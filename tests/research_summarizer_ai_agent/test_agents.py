from research_summarizer_ai_agent.agents import AgentResult
from research_summarizer_ai_agent.agents import build_view_model
from research_summarizer_ai_agent.agents import get_runtime_mode
from research_summarizer_ai_agent.agents import run_simple_agent


def test_get_runtime_mode_uses_openrouter_when_key_present(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")

    assert get_runtime_mode() == "openrouter"


def test_run_simple_agent_returns_fallback_when_model_unavailable(monkeypatch):
    monkeypatch.setattr("research_summarizer_ai_agent.agents._build_chat_model", lambda: None)

    result = run_simple_agent("What are AI agents?")

    assert result.used_fallback is True
    assert "No compatible LangChain chat model" in result.response_text


def test_build_view_model_exposes_response_and_sources():
    result = AgentResult(
        user_input="What are AI agents?",
        response_text="AI agents are systems that use tools to complete tasks.",
        sources=["https://example.com"],
        runtime_mode="openrouter",
        used_fallback=False,
        error_message="",
    )

    view_model = build_view_model(result)

    assert view_model["response"] == result.response_text
    assert view_model["sources"] == ["https://example.com"]
