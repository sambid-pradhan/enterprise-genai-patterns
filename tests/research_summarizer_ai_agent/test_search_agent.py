from research_summarizer_ai_agent.search_agent import collect_candidate_sources, filter_primary_sources


def test_collect_candidate_sources_uses_search_results():
    def fake_search(query):
        return [
            {
                "title": f"Paper for {query}",
                "url": f"https://example.com/{query.replace(' ', '-')}",
                "snippet": "Snippet",
                "source_type": "paper",
                "is_primary": True,
                "score": 0.8,
            }
        ]

    results = collect_candidate_sources(["topic one", "topic two"], search_fn=fake_search)
    assert len(results) == 2
    assert all(result["is_primary"] for result in results)


def test_filter_primary_sources_keeps_only_primary_sources():
    candidates = [
        {"title": "Primary", "url": "https://example.com/p1", "snippet": "x", "source_type": "paper", "is_primary": True, "score": 0.9},
        {"title": "Secondary", "url": "https://example.com/s1", "snippet": "y", "source_type": "blog", "is_primary": False, "score": 0.5},
    ]

    filtered = filter_primary_sources(candidates)
    assert [candidate["title"] for candidate in filtered] == ["Primary"]

