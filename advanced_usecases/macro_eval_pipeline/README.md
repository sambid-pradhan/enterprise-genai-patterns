# Synthetic Agent Execution Traces

This example generates a synthetic dataset of 500 customer-support AI agent execution traces for an e-commerce company, then runs a macro-evaluation pipeline over those traces.

The pipeline uses OpenRouter for trace summarization and cluster explanation, Hugging Face `sentence-transformers` for embeddings, and local KMeans clustering for pattern discovery.

## Files

```text
macro_eval_pipeline/
|-- generate_traces.py
|-- macro_eval_pipeline.py
|-- README.md
|-- requirements.txt
`-- data/
    |-- execution_traces.json
    |-- trace_summaries.json
    |-- trace_embeddings.json
    |-- clusters.json
    `-- macro_eval_report.md
```

## Setup

```powershell
pip install -r advanced_usecases/macro_eval_pipeline/requirements.txt
```

Create a local `.env` file:

```text
OPENROUTER_API_KEY=your_key_here
```

## Phase 1: Generate Traces

```powershell
python advanced_usecases/macro_eval_pipeline/generate_traces.py
```

## Phases 2-6: Run Macro Eval Pipeline

```powershell
python advanced_usecases/macro_eval_pipeline/macro_eval_pipeline.py
```

For a quick smoke test, process fewer traces:

```powershell
python advanced_usecases/macro_eval_pipeline/macro_eval_pipeline.py --limit 10 --clusters 3 --force
```

## Outputs

The generated trace dataset contains:

- 500 execution traces
- realistic tool use and agent steps
- recurring hidden behavioral patterns
- varied customer messages, latency, cost, token usage, regions, tiers, and outcomes

The macro-eval pipeline adds:

- `data/trace_summaries.json`
- `data/trace_embeddings.json`
- `data/clusters.json`
- `data/macro_eval_report.md`
