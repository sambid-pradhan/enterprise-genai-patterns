from research_summarizer_ai_agent.pipeline import run_research


def test_run_research_returns_a_report(monkeypatch):
    monkeypatch.setattr(
        "research_summarizer_ai_agent.pipeline.collect_candidate_sources",
        lambda queries: [
            {
                "title": "Example Paper",
                "url": "https://example.com/paper",
                "snippet": "Snippet one. Snippet two.",
                "source_type": "paper",
                "is_primary": True,
                "score": 0.95,
            }
        ],
    )
    monkeypatch.setattr(
        "research_summarizer_ai_agent.pipeline.fetch_page_text",
        lambda url: "First paragraph. Second paragraph.",
    )

    report = run_research("Research summarizers")
    assert report.title == "Research digest: Research summarizers"
    assert report.sections[0].heading == "Sub-questions and findings"
    assert report.citations[0].title == "Example Paper"

