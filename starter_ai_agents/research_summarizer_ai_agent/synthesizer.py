from __future__ import annotations

from research_summarizer_ai_agent.citations import format_citation
from research_summarizer_ai_agent.models import ResearchPlan, ResearchReport


def build_report_markdown(plan: ResearchPlan, report: ResearchReport) -> str:
    sub_questions = "\n".join(f"- {question}" for question in plan.sub_questions)
    sections = "\n\n".join(f"## {section.heading}\n\n{section.body}" for section in report.sections)
    citations = "\n".join(
        format_citation(
            {
                "title": candidate.title,
                "url": candidate.url,
                "source_type": candidate.source_type,
                "is_primary": candidate.is_primary,
            }
        )
        for candidate in report.citations
    )

    return f"""# {report.title}

## Executive summary

{report.executive_summary}

## Sub-questions

{sub_questions}

{sections}

## Where evidence is weak or missing

The report only uses primary sources. If coverage is thin, the digest should call that out explicitly instead of filling gaps with weaker material.

## Citations

{citations}
"""

