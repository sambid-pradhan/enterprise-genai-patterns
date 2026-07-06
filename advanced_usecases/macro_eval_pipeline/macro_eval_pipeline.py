import argparse
import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans


ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
DEFAULT_TRACE_PATH = DATA_DIR / "execution_traces.json"
DEFAULT_SUMMARY_PATH = DATA_DIR / "trace_summaries.json"
DEFAULT_EMBEDDING_PATH = DATA_DIR / "trace_embeddings.json"
DEFAULT_CLUSTER_PATH = DATA_DIR / "clusters.json"
DEFAULT_REPORT_PATH = DATA_DIR / "macro_eval_report.md"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_openrouter_client() -> OpenAI:
    load_dotenv(ROOT / ".env")
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is required. Add it to "
            "advanced_usecases/macro_eval_pipeline/.env or your shell environment."
        )
    return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)


def openrouter_chat(client: OpenAI, model: str, messages: list[dict[str, str]], temperature: float = 0.1) -> str:
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=messages,
        extra_body={"reasoning": {"enabled": True}},
    )
    return response.choices[0].message.content.strip()


def compact_trace(trace: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": trace["run_id"],
        "case_type": trace["case_type"],
        "customer_tier": trace["customer_tier"],
        "region": trace["region"],
        "user_message": trace["user_message"],
        "agent_steps": trace["agent_steps"],
        "tools_used": trace["tools_used"],
        "retry_count": trace["retry_count"],
        "human_review": trace["human_review"],
        "final_response": trace["final_response"],
        "outcome": trace["outcome"],
        "eval_result": trace["eval_result"],
        "latency_seconds": trace["latency_seconds"],
        "cost_usd": trace["cost_usd"],
    }


def summarize_trace(client: OpenAI, model: str, trace: dict[str, Any]) -> str:
    return openrouter_chat(
        client=client,
        model=model,
        temperature=0.1,
        messages=[
            {
                "role": "system",
                "content": (
                    "You summarize production AI agent execution traces for macro evaluation. "
                    "Write 3-5 concise sentences. Focus on user intent, tools used, important "
                    "decisions, errors, and final outcome. Do not mention hidden pattern labels."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(compact_trace(trace), indent=2),
            },
        ],
    )


def build_summaries(
    traces: list[dict[str, Any]],
    client: OpenAI,
    model: str,
    output_path: Path,
    force: bool,
    limit: int | None,
) -> list[dict[str, Any]]:
    if output_path.exists() and not force:
        summaries = load_json(output_path)
        if len(summaries) >= len(traces) or limit is not None:
            return summaries

    existing: dict[str, dict[str, Any]] = {}
    if output_path.exists() and not force:
        existing = {item["run_id"]: item for item in load_json(output_path)}

    selected = traces[:limit] if limit is not None else traces
    summaries: list[dict[str, Any]] = []
    for index, trace in enumerate(selected, start=1):
        if trace["run_id"] in existing:
            summaries.append(existing[trace["run_id"]])
            continue

        summary = summarize_trace(client, model, trace)
        item = {
            "run_id": trace["run_id"],
            "case_type": trace["case_type"],
            "eval_result": trace["eval_result"],
            "outcome": trace["outcome"],
            "tools_used": trace["tools_used"],
            "summary": summary,
        }
        summaries.append(item)
        print(f"Summarized {index}/{len(selected)}: {trace['run_id']}")

        if index % 10 == 0:
            write_json(output_path, summaries)

    write_json(output_path, summaries)
    return summaries


def build_embeddings(
    summaries: list[dict[str, Any]],
    model_name: str,
    output_path: Path,
    force: bool,
) -> list[dict[str, Any]]:
    if output_path.exists() and not force:
        embeddings = load_json(output_path)
        if len(embeddings) == len(summaries):
            return embeddings

    model = SentenceTransformer(model_name)
    texts = [item["summary"] for item in summaries]
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)

    records = []
    for item, vector in zip(summaries, vectors):
        records.append(
            {
                "run_id": item["run_id"],
                "summary": item["summary"],
                "embedding_model": model_name,
                "embedding": [round(float(value), 7) for value in vector],
            }
        )

    write_json(output_path, records)
    return records


def explain_cluster(client: OpenAI, model: str, cluster: dict[str, Any]) -> dict[str, str]:
    sample_text = "\n\n".join(
        f"Run {item['run_id']}:\n{item['summary']}" for item in cluster["representative_runs"]
    )
    text = openrouter_chat(
        client=client,
        model=model,
        temperature=0.1,
        messages=[
            {
                "role": "system",
                "content": (
                    "You explain clusters of AI agent execution summaries for engineering teams. "
                    "Return only valid JSON with keys cluster_name, root_cause, business_impact, "
                    "suggested_fix."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Here are representative execution summaries from one cluster.\n\n"
                    f"{sample_text}\n\n"
                    "Explain the shared behavior."
                ),
            },
        ],
    )
    return parse_cluster_explanation(text)


def parse_cluster_explanation(text: str) -> dict[str, str]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        parsed = json.loads(match.group(0)) if match else {}

    return {
        "cluster_name": str(parsed.get("cluster_name", "Unlabeled Cluster")),
        "root_cause": str(parsed.get("root_cause", "The shared behavior needs review.")),
        "business_impact": str(parsed.get("business_impact", "The cluster may affect support quality.")),
        "suggested_fix": str(parsed.get("suggested_fix", "Review representative runs and update agent policy.")),
    }


def build_clusters(
    summaries: list[dict[str, Any]],
    embeddings: list[dict[str, Any]],
    client: OpenAI,
    model: str,
    output_path: Path,
    force: bool,
    cluster_count: int,
) -> list[dict[str, Any]]:
    if output_path.exists() and not force:
        return load_json(output_path)

    vectors = np.array([item["embedding"] for item in embeddings], dtype=np.float32)
    kmeans = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
    labels = kmeans.fit_predict(vectors)

    by_run_id = {item["run_id"]: item for item in summaries}
    clusters: list[dict[str, Any]] = []

    for cluster_id in range(cluster_count):
        member_indexes = np.where(labels == cluster_id)[0]
        centroid = kmeans.cluster_centers_[cluster_id]
        distances = np.linalg.norm(vectors[member_indexes] - centroid, axis=1)
        representative_indexes = member_indexes[np.argsort(distances)[:20]]
        members = [by_run_id[embeddings[i]["run_id"]] for i in member_indexes]
        representative_runs = [by_run_id[embeddings[i]["run_id"]] for i in representative_indexes]
        eval_counts = Counter(item["eval_result"] for item in members)
        case_type_counts = Counter(item["case_type"] for item in members)

        cluster = {
            "cluster_id": cluster_id,
            "size": len(members),
            "eval_result_counts": dict(eval_counts),
            "case_type_counts": dict(case_type_counts),
            "representative_runs": representative_runs,
        }
        cluster["explanation"] = explain_cluster(client, model, cluster)
        clusters.append(cluster)
        print(f"Explained cluster {cluster_id + 1}/{cluster_count}")

    clusters.sort(key=lambda item: item["size"], reverse=True)
    write_json(output_path, clusters)
    return clusters


def estimate_cluster_cost(cluster: dict[str, Any]) -> float:
    monthly_multiplier = 30
    manual_review_cost = 2.0
    dominant_eval = max(cluster["eval_result_counts"], key=cluster["eval_result_counts"].get)
    if dominant_eval == "unnecessary_escalation":
        return round(cluster["size"] * manual_review_cost * monthly_multiplier / 30, 2)
    if dominant_eval in {"retry_loop", "timeout"}:
        return round(cluster["size"] * 0.75 * monthly_multiplier / 30, 2)
    if dominant_eval in {"missing_tool_call", "wrong_policy_retrieval", "hallucinated_response"}:
        return round(cluster["size"] * 1.25 * monthly_multiplier / 30, 2)
    return round(cluster["size"] * 0.25 * monthly_multiplier / 30, 2)


def build_report(
    traces: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    output_path: Path,
) -> str:
    eval_counts = Counter(trace["eval_result"] for trace in traces)
    outcome_counts = Counter(trace["outcome"] for trace in traces)
    resolved = outcome_counts.get("resolved", 0)
    success_rate = round((resolved / len(traces)) * 100, 1)
    highest_impact = max(clusters, key=lambda cluster: estimate_cluster_cost(cluster))

    lines = [
        "# Macro Evaluation Report",
        "",
        "## Overview",
        "",
        f"- Runs analyzed: {len(traces)}",
        f"- Summaries generated: {len(summaries)}",
        f"- Clusters found: {len(clusters)}",
        f"- Resolved outcome rate: {success_rate}%",
        "",
        "## Evaluation Result Distribution",
        "",
    ]

    for label, count in eval_counts.most_common():
        lines.append(f"- {label}: {count}")

    lines.extend(
        [
            "",
            "## Highest Impact Cluster",
            "",
            f"- Cluster: {highest_impact['explanation']['cluster_name']}",
            f"- Occurrences: {highest_impact['size']}",
            f"- Estimated cost signal: ${estimate_cluster_cost(highest_impact):.2f}",
            f"- Recommendation: {highest_impact['explanation']['suggested_fix']}",
            "",
            "## Clusters",
            "",
        ]
    )

    for cluster in clusters:
        explanation = cluster["explanation"]
        lines.extend(
            [
                f"### Cluster {cluster['cluster_id']}: {explanation['cluster_name']}",
                "",
                f"- Occurrences: {cluster['size']}",
                f"- Dominant eval labels: {format_counts(cluster['eval_result_counts'])}",
                f"- Dominant case types: {format_counts(cluster['case_type_counts'])}",
                f"- Estimated cost signal: ${estimate_cluster_cost(cluster):.2f}",
                "",
                f"Root cause: {explanation['root_cause']}",
                "",
                f"Business impact: {explanation['business_impact']}",
                "",
                f"Suggested fix: {explanation['suggested_fix']}",
                "",
                "Representative runs:",
            ]
        )
        for item in cluster["representative_runs"][:5]:
            lines.append(f"- {item['run_id']}: {item['summary']}")
        lines.append("")

    report = "\n".join(lines).strip() + "\n"
    output_path.write_text(report, encoding="utf-8")
    return report


def format_counts(counts: dict[str, int]) -> str:
    return ", ".join(f"{label} ({count})" for label, count in Counter(counts).most_common(3))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the macro evaluation pipeline.")
    parser.add_argument("--traces", type=Path, default=DEFAULT_TRACE_PATH)
    parser.add_argument("--output-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--openrouter-model", default="google/gemini-3.1-flash-lite")
    parser.add_argument("--embedding-model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--clusters", type=int, default=5)
    parser.add_argument("--limit", type=int, default=None, help="Process only the first N traces for smoke tests.")
    parser.add_argument("--force", action="store_true", help="Regenerate all derived artifacts.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    traces = load_json(args.traces)
    if args.limit is not None:
        traces = traces[: args.limit]

    client = load_openrouter_client()
    summaries = build_summaries(
        traces=traces,
        client=client,
        model=args.openrouter_model,
        output_path=output_dir / DEFAULT_SUMMARY_PATH.name,
        force=args.force,
        limit=None,
    )
    embeddings = build_embeddings(
        summaries=summaries,
        model_name=args.embedding_model,
        output_path=output_dir / DEFAULT_EMBEDDING_PATH.name,
        force=args.force,
    )
    clusters = build_clusters(
        summaries=summaries,
        embeddings=embeddings,
        client=client,
        model=args.openrouter_model,
        output_path=output_dir / DEFAULT_CLUSTER_PATH.name,
        force=args.force,
        cluster_count=min(args.clusters, len(summaries)),
    )
    build_report(
        traces=traces,
        summaries=summaries,
        clusters=clusters,
        output_path=output_dir / DEFAULT_REPORT_PATH.name,
    )

    print(f"Wrote {output_dir / DEFAULT_SUMMARY_PATH.name}")
    print(f"Wrote {output_dir / DEFAULT_EMBEDDING_PATH.name}")
    print(f"Wrote {output_dir / DEFAULT_CLUSTER_PATH.name}")
    print(f"Wrote {output_dir / DEFAULT_REPORT_PATH.name}")


if __name__ == "__main__":
    main()
