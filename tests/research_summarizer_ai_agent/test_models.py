from research_summarizer_ai_agent.models import ResearchPlan, ResearchReport, ReportSection, SourceCandidate


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
        sections=[ReportSection(heading="Intro", body="Body")],
        citations=[candidate],
    )

    assert plan.topic == "LLM evaluation"
    assert report.citations[0].is_primary is True

