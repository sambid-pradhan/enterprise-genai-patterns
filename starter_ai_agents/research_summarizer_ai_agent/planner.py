from __future__ import annotations

from research_summarizer_ai_agent.models import ResearchPlan


_QUESTION_TEMPLATES = (
    "What do the primary sources say about {topic}?",
    "Which primary sources define or explain {topic}?",
    "What evidence, benchmarks, or examples support {topic}?",
    "What limitations, disagreements, or open questions appear in primary sources about {topic}?",
)


def build_research_plan(topic: str) -> ResearchPlan:
    clean_topic = topic.strip()
    if not clean_topic:
        raise ValueError("topic must not be empty")

    word_count = len(clean_topic.split())
    question_count = 2 if word_count <= 3 else 3 if word_count <= 8 else 4
    sub_questions = [template.format(topic=clean_topic) for template in _QUESTION_TEMPLATES[:question_count]]
    search_queries = [f"{question} primary source" for question in sub_questions]
    return ResearchPlan(topic=clean_topic, sub_questions=sub_questions, search_queries=search_queries)

