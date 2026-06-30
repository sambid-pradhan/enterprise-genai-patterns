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
            ReportSection(
                heading="Sub-questions and findings",
                body="Findings here.",
                source_urls=["https://example.com/paper"],
            )
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

