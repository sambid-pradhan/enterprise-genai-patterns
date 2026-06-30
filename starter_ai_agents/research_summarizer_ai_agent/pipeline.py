from __future__ import annotations

from collections import Counter
from html import unescape
import re

from research_summarizer_ai_agent.fetcher import fetch_page_text
from research_summarizer_ai_agent.models import ReportSection, ResearchPlan, ResearchReport, SourceCandidate
from research_summarizer_ai_agent.planner import build_research_plan
from research_summarizer_ai_agent.search_agent import collect_candidate_sources, filter_primary_sources


_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]{3,}")


def _candidate_from_dict(candidate: dict) -> SourceCandidate:
    return SourceCandidate(
        title=str(candidate.get("title") or "Untitled source"),
        url=str(candidate.get("url") or ""),
        snippet=str(candidate.get("snippet") or ""),
        source_type=str(candidate.get("source_type") or "source"),
        is_primary=bool(candidate.get("is_primary")),
        score=float(candidate.get("score") or 0.0),
    )


def _first_sentences(text: str, limit: int = 2) -> str:
    cleaned = " ".join(text.split())
    if not cleaned:
        return ""
    segments = re.split(r"(?<=[.!?])\s+", cleaned)
    return " ".join(segments[:limit]).strip()


def _keywords(text: str) -> set[str]:
    return {match.group(0).lower() for match in _WORD_RE.finditer(text)}


def _summarize_agreement(sources: list[SourceCandidate], texts: dict[str, str]) -> str:
    if len(sources) < 2:
        return "Only one or zero primary sources were found, so agreement across sources cannot be assessed yet."

    keyword_sets = []
    for source in sources[:3]:
        source_text = texts.get(source.url) or source.snippet
        keyword_sets.append(_keywords(source_text))

    common = set.intersection(*keyword_sets) if keyword_sets else set()
    if common:
        top_terms = sorted(common)[:5]
        return f"Across the strongest primary sources, the overlapping themes are: {', '.join(top_terms)}."
    return "The strongest primary sources cover the same topic but emphasize different angles, so overlap is limited."


def _build_findings_body(plan: ResearchPlan, sources: list[SourceCandidate], texts: dict[str, str]) -> str:
    if not sources:
        return "No primary sources were found for these sub-questions."

    lines: list[str] = []
    for index, sub_question in enumerate(plan.sub_questions):
        source = sources[index % len(sources)]
        evidence = texts.get(source.url) or source.snippet or "No extract available."
        summary = _first_sentences(evidence, limit=2) or evidence[:240]
        lines.append(f"- {sub_question}\n  - {source.title}: {summary}")
    return "\n".join(lines)


def _build_gap_body(plan: ResearchPlan, sources: list[SourceCandidate]) -> str:
    if not sources:
        return "Primary-source coverage is thin. The next step is to search the topic with narrower keywords or add explicit source URLs."
    if len(sources) == 1:
        return "Only one primary source surfaced, so the topic needs a second source before the report can claim convergence."
    if len(plan.sub_questions) > len(sources):
        return "Some sub-questions are still mapped to the same source because the search did not return enough distinct primary sources."
    return "Primary-source coverage is decent, but any claims that depend on a single source should be treated carefully."


def run_research(topic: str) -> ResearchReport:
    plan = build_research_plan(topic)
    candidates = collect_candidate_sources(plan.search_queries)
    primary_sources = filter_primary_sources(candidates)
    chosen_sources = primary_sources[:3] if primary_sources else candidates[:3]
    report_sources = [_candidate_from_dict(candidate) for candidate in chosen_sources]

    texts: dict[str, str] = {}
    for source in report_sources:
        text = fetch_page_text(source.url)
        texts[source.url] = text or source.snippet

    findings_body = _build_findings_body(plan, report_sources, texts)
    agreement_body = _summarize_agreement(report_sources, texts)
    gaps_body = _build_gap_body(plan, report_sources)

    sections = [
        ReportSection(
            heading="Sub-questions and findings",
            body=findings_body,
            source_urls=[source.url for source in report_sources],
        ),
        ReportSection(
            heading="What the sources agree on",
            body=agreement_body,
            source_urls=[source.url for source in report_sources],
        ),
        ReportSection(
            heading="Where evidence is weak or missing",
            body=gaps_body,
            source_urls=[source.url for source in report_sources],
        ),
    ]

    if report_sources:
        executive_summary = f"Primary sources on {plan.topic} were found, and the report prioritizes the strongest evidence available."
    else:
        executive_summary = f"No primary sources were found for {plan.topic}, so the report flags the evidence as thin."

    return ResearchReport(
        title=f"Research digest: {plan.topic}",
        executive_summary=executive_summary,
        sections=sections,
        citations=report_sources,
    )

