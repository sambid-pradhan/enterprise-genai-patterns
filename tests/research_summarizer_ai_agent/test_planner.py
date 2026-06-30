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

