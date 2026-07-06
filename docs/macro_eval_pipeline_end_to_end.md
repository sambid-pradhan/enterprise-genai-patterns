# Macro Evaluation Pipeline: End-to-End Build Notes

This document summarizes the end-to-end macro evaluation workflow built in this repository for synthetic customer-support agent execution traces.

The goal of the project is to demonstrate how a production team could move from raw agent traces to higher-level behavioral insights:

```text
Agent execution traces
  -> trace summaries
  -> embeddings
  -> semantic clusters
  -> cluster explanations
  -> engineering report
```

## Project Location

```text
advanced_usecases/macro_eval_pipeline/
```

Key files:

```text
advanced_usecases/macro_eval_pipeline/
|-- generate_traces.py
|-- macro_eval_pipeline.py
|-- requirements.txt
|-- README.md
`-- data/
    |-- execution_traces.json
    |-- eda_report.md
    |-- eda_summary.json
    |-- trace_summaries_preview_5.json
    |-- pipeline_preview_15/
    `-- pipeline_full_500/
```

## Phase 1: Synthetic Trace Generation

We created a synthetic dataset of 500 execution traces for a customer-support AI assistant at an e-commerce company.

Dataset path:

```text
advanced_usecases/macro_eval_pipeline/data/execution_traces.json
```

Each trace follows this structure:

```json
{
  "run_id": "run_000001",
  "timestamp": "...",
  "customer_tier": "...",
  "region": "...",
  "case_type": "...",
  "user_message": "...",
  "agent_steps": [],
  "tools_used": [],
  "retry_count": 0,
  "human_review": false,
  "final_response": "...",
  "outcome": "...",
  "eval_result": "...",
  "latency_seconds": 0,
  "cost_usd": 0.0,
  "token_input": 0,
  "token_output": 0
}
```

The generated data contains recurring behavior patterns rather than pure randomness.

Major intended patterns:

| Pattern Type | Approx Count | Behavior |
| --- | ---: | --- |
| Unnecessary refund escalation | 120 | Refund is eligible, but the agent escalates anyway |
| Missing shipment tool call | 80 | Shipping status request without `shipment_tracking` |
| Password reset retry loop | 60 | Account login flow repeatedly calls `password_reset` |
| Wrong refund policy retrieval | 50 | Refund policy retrieved incorrectly |
| Correct resolutions | 150 | Agent uses correct tools and resolves the request |
| Edge cases | 40 | Timeout, hallucination, low confidence, human review, incorrect refund decisions |

## Phase 2: Data Quality and EDA

We ran an exploratory data analysis pass to understand the 500 traces before building the pipeline.

EDA outputs:

```text
advanced_usecases/macro_eval_pipeline/data/eda_report.md
advanced_usecases/macro_eval_pipeline/data/eda_summary.json
```

High-level EDA results:

| Metric | Value |
| --- | ---: |
| Total traces | 500 |
| Unique run IDs | 500 |
| Resolved outcomes | 157 |
| Failed outcomes | 215 |
| Escalated outcomes | 120 |
| Awaiting customer outcomes | 8 |

Evaluation label distribution:

| Eval Result | Count |
| --- | ---: |
| `correct_resolution` | 150 |
| `unnecessary_escalation` | 120 |
| `missing_tool_call` | 80 |
| `retry_loop` | 60 |
| `wrong_policy_retrieval` | 50 |
| `hallucinated_response` | 10 |
| `timeout` | 8 |
| `low_confidence` | 8 |
| `successful_with_human_review` | 7 |
| `incorrect_refund_decision` | 7 |

Quality checks passed:

| Check | Result |
| --- | --- |
| Duplicate run IDs | 0 |
| Missing required fields | 0 |
| Invalid tools | 0 |
| Eval/outcome consistency issues | 0 |
| Eval/case type semantic issues | 0 |
| Resolved traces incorrectly saying a human must complete the next step | 0 |

## Phase 3: Trace Summarization

Instead of embedding the full JSON traces directly, each execution trace is summarized first.

The summary prompt focuses on:

- User intent
- Tools used
- Important decisions
- Errors
- Final outcome

OpenRouter client implementation:

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

response = client.chat.completions.create(
    model="google/gemini-3.1-flash-lite",
    messages=messages,
    extra_body={"reasoning": {"enabled": True}},
)
```

Current OpenRouter model:

```text
google/gemini-3.1-flash-lite
```

We first tested summarization on 5 traces.

Output:

```text
advanced_usecases/macro_eval_pipeline/data/trace_summaries_preview_5.json
```

Then we ran a 15-trace preview end to end.

Output:

```text
advanced_usecases/macro_eval_pipeline/data/pipeline_preview_15/trace_summaries.json
```

Finally, we summarized all 500 traces.

Output:

```text
advanced_usecases/macro_eval_pipeline/data/pipeline_full_500/trace_summaries.json
```

Example summary:

```text
The user requested a delivery date for order ORD-900001, prompting the agent to retrieve order status and general shipping policy information. Although the agent successfully identified the order and referenced the knowledge base, it failed to query the specific tracking API to provide an accurate delivery date. Consequently, the agent provided a generic estimate rather than the actual status, resulting in a failed outcome due to a missing tool call.
```

## Phase 4: Embedding Generation

After summarization, we embedded each summary locally using Hugging Face Sentence Transformers.

Embedding model:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Embedding results:

| Run | Records | Dimensions |
| --- | ---: | ---: |
| 15-trace preview | 15 | 384 |
| Full run | 500 | 384 |

Full embedding output:

```text
advanced_usecases/macro_eval_pipeline/data/pipeline_full_500/trace_embeddings.json
```

## Phase 5: Clustering

We clustered the embedded summaries with local KMeans.

For the full 500-trace run, we used 8 clusters.

Full cluster output:

```text
advanced_usecases/macro_eval_pipeline/data/pipeline_full_500/clusters.json
```

Cluster results:

| Cluster ID | Size | Cluster Name |
| ---: | ---: | --- |
| 3 | 111 | Incorrect Policy Retrieval for Damaged Items |
| 1 | 110 | Unnecessary Escalation of Eligible Automated Refunds |
| 4 | 94 | Failure to Invoke Tracking Tool |
| 2 | 77 | Infinite Retry Loop on Account Lock Resolution |
| 0 | 31 | Shipping Address Verification Failures |
| 5 | 28 | Warranty and Service Policy Hallucinations |
| 6 | 25 | Successful Automated Exchange Processing |
| 7 | 24 | Automated Resolution of Payment Authorization Inquiries |

The clusters successfully recovered the major hidden patterns from the synthetic dataset.

## Phase 6: Cluster Explanation

Each cluster was explained by the OpenRouter model using representative summaries from that cluster.

For every cluster, the model generated:

- Cluster name
- Root cause
- Business impact
- Suggested fix

Example cluster:

```text
Cluster: Unnecessary Escalation of Eligible Automated Refunds
Occurrences: 110
Root cause: The agent verifies refund eligibility but does not trigger the automated refund execution path.
Business impact: More manual support tickets and delayed customer resolution.
Suggested fix: Add a guardrail requiring automated refund completion when eligibility checks pass.
```

## Phase 7: Final Engineering Report

The final report was generated as markdown.

Output:

```text
advanced_usecases/macro_eval_pipeline/data/pipeline_full_500/macro_eval_report.md
```

Report overview:

| Metric | Value |
| --- | ---: |
| Runs analyzed | 500 |
| Summaries generated | 500 |
| Clusters found | 8 |
| Resolved outcome rate | 31.4% |

Highest impact cluster:

```text
Unnecessary Escalation of Eligible Automated Refunds
```

Impact:

```text
Occurrences: 110
Estimated cost signal: $220.00
```

Recommendation:

```text
Update the agent's system prompt or decision-tree logic to explicitly mandate use of the refund execution tool when policy verification returns a positive result. Implement a guardrail to prevent escalation if all automated criteria are met.
```

## How To Rerun

Install dependencies:

```powershell
.\.venv\Scripts\pip3.12.exe install -r advanced_usecases/macro_eval_pipeline/requirements.txt
```

Generate traces:

```powershell
.\.venv\Scripts\python.exe advanced_usecases/macro_eval_pipeline/generate_traces.py
```

Run a small smoke test:

```powershell
.\.venv\Scripts\python.exe advanced_usecases/macro_eval_pipeline/macro_eval_pipeline.py --limit 15 --clusters 4 --force
```

Run the full pipeline:

```powershell
.\.venv\Scripts\python.exe advanced_usecases/macro_eval_pipeline/macro_eval_pipeline.py --clusters 8
```

Environment variable required:

```text
OPENROUTER_API_KEY=...
```

## Current Implementation Notes

- Summarization uses OpenRouter through the OpenAI Python SDK.
- The current OpenRouter model is `google/gemini-3.1-flash-lite`.
- Reasoning is enabled with `extra_body={"reasoning": {"enabled": True}}`.
- Embeddings are generated locally with `sentence-transformers/all-MiniLM-L6-v2`.
- Clustering uses local KMeans from scikit-learn.
- The full 500-trace run is stored separately under `pipeline_full_500` so preview artifacts and final artifacts are easy to compare.

## Next Possible Steps

1. Add a Streamlit dashboard for cluster exploration.
2. Add weekly comparison logic to detect new or growing clusters.
3. Add prompt/version metadata to every run.
4. Add regression checks to confirm whether a fix reduces cluster size.
5. Add a production architecture section explaining where traces come from and how scheduled macro-evals should run.
