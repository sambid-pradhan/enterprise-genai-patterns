from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ResearchPlan:
    topic: str
    sub_questions: list[str]
    search_queries: list[str]


@dataclass(slots=True)
class SourceCandidate:
    title: str
    url: str
    snippet: str
    source_type: str
    is_primary: bool
    score: float


@dataclass(slots=True)
class ReportSection:
    heading: str
    body: str
    source_urls: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ResearchReport:
    title: str
    executive_summary: str
    sections: list[ReportSection]
    citations: list[SourceCandidate]

