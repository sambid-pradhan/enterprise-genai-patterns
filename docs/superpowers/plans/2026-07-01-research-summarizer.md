# Research Summarizer Starter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a new `starter_ai_agents/research_summarizer_ai_agent` Streamlit app that takes a topic, runs multiple primary-source web research passes, optionally fetches the best source pages, and renders a sectioned digest with citations.

**Architecture:** Keep the app split into small, testable modules: a planner that turns one topic into sub-questions, a search agent that gathers and filters primary sources, a fetcher that extracts readable page text from the best sources, and a synthesizer that turns evidence into a report. The Streamlit UI should stay thin and only orchestrate these pieces. This keeps the starter easy to run while still showing the full agent loop.

**Tech Stack:** Python 3.12, Streamlit, `python-dotenv`, `pydantic`, `duckduckgo_search`, `requests`, `trafilatura`, and the existing OpenRouter/LangChain pattern from the current starter.

---

## File Structure

Create a new starter project folder:

- `starter_ai_agents/research_summarizer_ai_agent/__init__.py`
- `starter_ai_agents/research_summarizer_ai_agent/app.py`
- `starter_ai_agents/research_summarizer_ai_agent/models.py`
- `starter_ai_agents/research_summarizer_ai_agent/planner.py`
- `starter_ai_agents/research_summarizer_ai_agent/search_agent.py`
- `starter_ai_agents/research_summarizer_ai_agent/fetcher.py`
- `starter_ai_agents/research_summarizer_ai_agent/citations.py`
- `starter_ai_agents/research_summarizer_ai_agent/synthesizer.py`
- `starter_ai_agents/research_summarizer_ai_agent/pipeline.py`
- `starter_ai_agents/research_summarizer_ai_agent/requirements.txt`
- `starter_ai_agents/research_summarizer_ai_agent/.env.example`
- `tests/research_summarizer_ai_agent/test_models.py`
- `tests/research_summarizer_ai_agent/test_planner.py`
- `tests/research_summarizer_ai_agent/test_search_agent.py`
- `tests/research_summarizer_ai_agent/test_fetcher.py`
- `tests/research_summarizer_ai_agent/test_synthesizer.py`
- `tests/research_summarizer_ai_agent/test_pipeline.py`

Use the existing `starter_ai_agents/web_scraping_ai_agent` project as a layout and dependency reference, but do not reuse its scraping-specific naming.

## Task 1: Scaffold the package and shared models

**Files:**
- Create: `starter_ai_agents/research_summarizer_ai_agent/__init__.py`
- Create: `starter_ai_agents/research_summarizer_ai_agent/models.py`
- Create: `starter_ai_agents/research_summarizer_ai_agent/requirements.txt`
- Create: `starter_ai_agents/research_summarizer_ai_agent/.env.example`
- Create: `tests/research_summarizer_ai_agent/test_models.py`

- [ ] **Step 1: Write the failing test**

```python
from research_summarizer_ai_agent.models import ResearchPlan, SourceCandidate, ResearchReport


def test_research_models_round_trip():
    plan = ResearchPlan(
        topic="LLM evaluation",
        sub_questions=["What changed?", "What is the evidence?"],
        search_queries=["LLM evaluation primary sources", "LLM eval benchmark paper"],
    )

    candidate = SourceCandidate(
        title="Example Paper",
        url="https://example.com/paper",
        snippet="Example snippet",
        source_type="paper",
        is_primary=True,
        score=0.9,
    )

    report = ResearchReport(
        title="LLM evaluation digest",
        executive_summary="Short answer.",
        sections=[],
        citations=[candidate],
    )

    assert plan.topic == "LLM evaluation"
    assert report.citations[0].is_primary is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/research_summarizer_ai_agent/test_models.py -v`

Expected: fail with `ModuleNotFoundError` or missing symbol errors until the package exists.

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass, field


@dataclass
class ResearchPlan:
    topic: str
    sub_questions: list[str]
    search_queries: list[str]


@dataclass
class SourceCandidate:
    title: str
    url: str
    snippet: str
    source_type: str
    is_primary: bool
    score: float


@dataclass
class ReportSection:
    heading: str
    body: str
    source_urls: list[str] = field(default_factory=list)


@dataclass
class ResearchReport:
    title: str
    executive_summary: str
    sections: list[ReportSection]
    citations: list[SourceCandidate]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/research_summarizer_ai_agent/test_models.py -v`

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add starter_ai_agents/research_summarizer_ai_agent/__init__.py starter_ai_agents/research_summarizer_ai_agent/models.py starter_ai_agents/research_summarizer_ai_agent/requirements.txt starter_ai_agents/research_summarizer_ai_agent/.env.example tests/research_summarizer_ai_agent/test_models.py
git commit -m "feat: scaffold research summarizer models"
```

## Task 2: Build the research planner and source filtering

**Files:**
- Create: `starter_ai_agents/research_summarizer_ai_agent/planner.py`
- Create: `starter_ai_agents/research_summarizer_ai_agent/search_agent.py`
- Create: `tests/research_summarizer_ai_agent/test_planner.py`
- Create: `tests/research_summarizer_ai_agent/test_search_agent.py`

- [ ] **Step 1: Write the failing test**

```python
from research_summarizer_ai_agent.planner import build_research_plan
from research_summarizer_ai_agent.search_agent import collect_candidate_sources, filter_primary_sources


def test_build_research_plan_creates_multiple_subquestions():
    plan = build_research_plan("How do research summarizers work?")
    assert 2 <= len(plan.sub_questions) <= 4
    assert len(plan.search_queries) == len(plan.sub_questions)


def test_filter_primary_sources_keeps_only_primary_sources():
    candidates = [
        {"title": "Paper", "url": "https://example.com/paper", "snippet": "x", "source_type": "paper", "is_primary": True, "score": 0.9},
        {"title": "Blog", "url": "https://example.com/blog", "snippet": "y", "source_type": "blog", "is_primary": False, "score": 0.8},
    ]

    filtered = filter_primary_sources(candidates)
    assert len(filtered) == 1
    assert filtered[0]["title"] == "Paper"


def test_collect_candidate_sources_uses_each_query():
    seen_queries = []

    def fake_search(query):
        seen_queries.append(query)
        return []

    plan = build_research_plan("How do research summarizers work?")
    collect_candidate_sources(plan.search_queries, search_fn=fake_search)
    assert seen_queries == plan.search_queries
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/research_summarizer_ai_agent/test_planner.py tests/research_summarizer_ai_agent/test_search_agent.py -v`

Expected: fail because the planner and source filter do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
from research_summarizer_ai_agent.models import ResearchPlan


def build_research_plan(topic: str) -> ResearchPlan:
    sub_questions = [
        f"What is the current state of {topic}?",
        f"What primary sources define {topic}?",
        f"What evidence or benchmarks exist for {topic}?",
    ]
    search_queries = [f'{question} primary source' for question in sub_questions]
    return ResearchPlan(topic=topic, sub_questions=sub_questions, search_queries=search_queries)


def filter_primary_sources(candidates: list[dict]) -> list[dict]:
    return [candidate for candidate in candidates if candidate.get("is_primary")]


def collect_candidate_sources(search_queries: list[str], search_fn) -> list[dict]:
    results: list[dict] = []
    for query in search_queries:
        results.extend(search_fn(query))
    return results
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/research_summarizer_ai_agent/test_planner.py tests/research_summarizer_ai_agent/test_search_agent.py -v`

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add starter_ai_agents/research_summarizer_ai_agent/planner.py starter_ai_agents/research_summarizer_ai_agent/search_agent.py tests/research_summarizer_ai_agent/test_planner.py tests/research_summarizer_ai_agent/test_search_agent.py
git commit -m "feat: add research planning and source filtering"
```

## Task 3: Add page fetching and citation formatting

**Files:**
- Create: `starter_ai_agents/research_summarizer_ai_agent/fetcher.py`
- Create: `starter_ai_agents/research_summarizer_ai_agent/citations.py`
- Create: `tests/research_summarizer_ai_agent/test_fetcher.py`

- [ ] **Step 1: Write the failing test**

```python
from research_summarizer_ai_agent.fetcher import extract_main_text
from research_summarizer_ai_agent.citations import format_citation


def test_extract_main_text_returns_readable_article_text():
    html = """
    <html>
      <body>
        <article>
          <h1>Title</h1>
          <p>First paragraph.</p>
          <p>Second paragraph.</p>
        </article>
      </body>
    </html>
    """
    text = extract_main_text(html)
    assert "First paragraph" in text
    assert "Second paragraph" in text


def test_format_citation_creates_markdown_link():
    citation = format_citation(
        {"title": "Example Paper", "url": "https://example.com/paper", "source_type": "paper"}
    )
    assert "[Example Paper](https://example.com/paper)" in citation
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/research_summarizer_ai_agent/test_fetcher.py -v`

Expected: fail because the extractor and formatter do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
import trafilatura


def extract_main_text(html: str) -> str:
    return trafilatura.extract(html, include_comments=False, include_tables=False) or ""


def format_citation(source: dict) -> str:
    title = source["title"]
    url = source["url"]
    source_type = source.get("source_type", "source")
    return f"- [{title}]({url}) ({source_type})"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/research_summarizer_ai_agent/test_fetcher.py -v`

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add starter_ai_agents/research_summarizer_ai_agent/fetcher.py starter_ai_agents/research_summarizer_ai_agent/citations.py tests/research_summarizer_ai_agent/test_fetcher.py
git commit -m "feat: add page extraction and citations"
```

## Task 4: Synthesize the report and wire the Streamlit app

**Files:**
- Create: `starter_ai_agents/research_summarizer_ai_agent/synthesizer.py`
- Create: `starter_ai_agents/research_summarizer_ai_agent/pipeline.py`
- Create: `starter_ai_agents/research_summarizer_ai_agent/app.py`
- Create: `tests/research_summarizer_ai_agent/test_synthesizer.py`
- Create: `tests/research_summarizer_ai_agent/test_pipeline.py`

- [ ] **Step 1: Write the failing test**

```python
from research_summarizer_ai_agent.models import ResearchPlan, ResearchReport, ReportSection, SourceCandidate
from research_summarizer_ai_agent.synthesizer import build_report_markdown


def test_build_report_markdown_includes_required_sections():
    plan = ResearchPlan(
        topic="Research summarizers",
        sub_questions=["What are they?", "How do they search?"],
        search_queries=["research summarizer primary source", "web research agent paper"],
    )
    report = ResearchReport(
        title="Research summarizers",
        executive_summary="Short answer.",
        sections=[
            ReportSection(heading="Sub-questions and findings", body="Findings here.", source_urls=["https://example.com/paper"])
        ],
        citations=[
            SourceCandidate(
                title="Example Paper",
                url="https://example.com/paper",
                snippet="Snippet",
                source_type="paper",
                is_primary=True,
                score=0.95,
            )
        ],
    )

    markdown = build_report_markdown(plan, report)
    assert "Executive summary" in markdown
    assert "Sub-questions and findings" in markdown
    assert "Where evidence is weak or missing" in markdown
    assert "[Example Paper](https://example.com/paper)" in markdown
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/research_summarizer_ai_agent/test_synthesizer.py -v`

Expected: fail because report rendering does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
from research_summarizer_ai_agent.citations import format_citation


def build_report_markdown(plan, report) -> str:
    citation_lines = "\n".join(format_citation({"title": c.title, "url": c.url, "source_type": c.source_type}) for c in report.citations)
    sections = "\n\n".join(f"## {section.heading}\n\n{section.body}" for section in report.sections)
    return f"""# {report.title}

## Executive summary

{report.executive_summary}

{sections}

## Where evidence is weak or missing

Primary-source coverage is thin or mixed for at least one sub-question.

## Citations

{citation_lines}
"""
```

- [ ] **Step 4: Write the pipeline and wire the Streamlit app**

```python
from research_summarizer_ai_agent.models import ResearchReport, ReportSection
from research_summarizer_ai_agent.planner import build_research_plan
from research_summarizer_ai_agent.search_agent import collect_candidate_sources, filter_primary_sources


def run_research(topic: str) -> ResearchReport:
    plan = build_research_plan(topic)
    candidates = collect_candidate_sources(plan.search_queries)
    primary_sources = filter_primary_sources(candidates)
    sections = [
        ReportSection(
            heading="Sub-questions and findings",
            body="Findings are assembled here from the best primary sources.",
            source_urls=[source["url"] for source in primary_sources[:3]],
        )
    ]
    return ResearchReport(
        title=f"Research digest: {topic}",
        executive_summary="Short summary goes here.",
        sections=sections,
        citations=[],
    )
```

```python
from research_summarizer_ai_agent.pipeline import run_research


def test_run_research_returns_a_report(monkeypatch):
    monkeypatch.setattr(
        "research_summarizer_ai_agent.pipeline.collect_candidate_sources",
        lambda queries: [
            {"title": "Example Paper", "url": "https://example.com/paper", "snippet": "Snippet", "source_type": "paper", "is_primary": True, "score": 0.95}
        ],
    )
    report = run_research("Research summarizers")
    assert report.title == "Research digest: Research summarizers"
    assert report.sections[0].heading == "Sub-questions and findings"
```

```python
import streamlit as st

from research_summarizer_ai_agent.pipeline import run_research
from research_summarizer_ai_agent.planner import build_research_plan
from research_summarizer_ai_agent.synthesizer import build_report_markdown


st.title("Research Summarizer")
topic = st.text_input("Topic or question")

if st.button("Research") and topic.strip():
    plan = build_research_plan(topic)
    report = run_research(topic)
    st.subheader("Planned sub-questions")
    for question in plan.sub_questions:
        st.write(f"- {question}")
    st.subheader("Report")
    st.markdown(build_report_markdown(plan, report))
```

- [ ] **Step 5: Run the test and a manual app smoke check**

Run:

```bash
pytest tests/research_summarizer_ai_agent/test_synthesizer.py -v
pytest tests/research_summarizer_ai_agent/test_pipeline.py -v
streamlit run starter_ai_agents/research_summarizer_ai_agent/app.py
```

Expected:
- the synth test passes
- the pipeline test passes
- the app opens, accepts a topic, and shows a sectioned digest scaffold without crashing

- [ ] **Step 6: Commit**

```bash
git add starter_ai_agents/research_summarizer_ai_agent/synthesizer.py starter_ai_agents/research_summarizer_ai_agent/app.py tests/research_summarizer_ai_agent/test_synthesizer.py
git commit -m "feat: wire research summarizer report flow"
```

## Spec Coverage Check

This plan covers the approved design:

- Streamlit UI -> Task 4
- single-topic input -> Task 4
- automatic topic decomposition -> Task 2
- multiple web search passes -> Task 2
- optional full-page fetch for top primary sources -> Task 3
- sectioned report with citations -> Task 4
- primary-sources-only evidence policy -> Task 2

Out of scope by design:

- saved research history
- PDF export
- background jobs
- multi-turn chat
- non-web data sources
