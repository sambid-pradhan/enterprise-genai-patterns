from __future__ import annotations

import html
import os
import re
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import requests

try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv() -> bool:
        return False

try:
    import trafilatura
except Exception:
    trafilatura = None

try:
    from langchain.agents import create_agent
    from langchain.tools import tool
    from langchain_openai import ChatOpenAI
    from langchain_openrouter import ChatOpenRouter
except Exception:
    create_agent = None
    tool = None
    ChatOpenAI = None
    ChatOpenRouter = None

from pydantic import BaseModel, Field


load_dotenv()


class AgentResult(BaseModel):
    user_input: str
    response_text: str
    sources: list[str] = Field(default_factory=list)
    runtime_mode: str = "fallback"
    used_fallback: bool = False
    error_message: str = ""


def get_runtime_mode() -> str:
    if os.getenv("OPENROUTER_API_KEY", "").strip():
        return "openrouter"
    if os.getenv("OPENAI_API_KEY", "").strip():
        return "openai"
    return "fallback"


def get_openrouter_model_name() -> str:
    return os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash").strip() or "deepseek/deepseek-v4-flash"


def _build_chat_model() -> Any:
    runtime_mode = get_runtime_mode()
    if runtime_mode == "openrouter" and ChatOpenRouter is not None:
        return ChatOpenRouter(
            model=get_openrouter_model_name(),
            api_key=os.getenv("OPENROUTER_API_KEY", "").strip(),
            base_url="https://openrouter.ai/api/v1",
            temperature=0,
            app_url=os.getenv("OPENROUTER_HTTP_REFERER", "").strip() or None,
            app_title=os.getenv("OPENROUTER_APP_TITLE", "Research Summarizer AI Agent").strip() or "Research Summarizer AI Agent",
        )
    if runtime_mode == "openai" and ChatOpenAI is not None:
        return ChatOpenAI(model="gpt-4o-mini", temperature=0)
    return None


def _resolve_duckduckgo_url(raw_url: str) -> str:
    if raw_url.startswith("//"):
        return f"https:{raw_url}"
    parsed = urlparse(raw_url)
    if parsed.netloc.endswith("duckduckgo.com") and parsed.path.startswith("/l/"):
        uddg = parse_qs(parsed.query).get("uddg", [raw_url])[0]
        return unquote(uddg)
    return raw_url


def _strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value).strip()


def search_web(query: str, max_results: int = 5, timeout: int = 15) -> str:
    response = requests.get(
        "https://html.duckduckgo.com/html/",
        params={"q": query},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=timeout,
    )
    response.raise_for_status()

    pattern = re.compile(
        r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="(?P<url>[^"]+)"[^>]*>(?P<title>.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    lines: list[str] = []
    for index, match in enumerate(pattern.finditer(response.text)):
        if index >= max_results:
            break
        url = html.unescape(_resolve_duckduckgo_url(match.group("url")))
        title = _strip_tags(html.unescape(match.group("title")))
        lines.append(f"- {title}: {url}")

    return "\n".join(lines) if lines else "No search results found."


def fetch_page_text(url: str, timeout: int = 20) -> str:
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException:
        return ""

    if trafilatura is not None:
        extracted = trafilatura.extract(response.text, url=url)
        if extracted:
            return " ".join(extracted.split())[:1200]

    return " ".join(_strip_tags(response.text).split())[:1200]


def _extract_sources(text: str) -> list[str]:
    seen: list[str] = []
    for line in text.splitlines():
        if ": http" not in line:
            continue
        _title, _separator, url = line.partition(": ")
        url = url.strip()
        if url and url not in seen:
            seen.append(url)
    return seen


def _build_agent() -> Any:
    chat_model = _build_chat_model()
    if chat_model is None or create_agent is None or tool is None:
        return None

    @tool
    def search_web_tool(query: str) -> str:
        """Search the web for the user's topic and return result titles with URLs."""
        return search_web(query)

    @tool
    def fetch_page_text_tool(url: str) -> str:
        """Fetch a web page and return the readable main text."""
        return fetch_page_text(url)

    return create_agent(
        model=chat_model,
        tools=[search_web_tool, fetch_page_text_tool],
        system_prompt=(
            "You are a simple research assistant. "
            "Given a user topic, use search_web_tool to find relevant sources, "
            "use fetch_page_text_tool to read promising pages, and write a concise report. "
            "Always include a Sources section with plain URLs you actually used."
        ),
    )


def _extract_response_text(result: Any) -> str:
    if isinstance(result, dict):
        messages = result.get("messages")
        if isinstance(messages, list):
            for message in reversed(messages):
                content = message.get("content") if isinstance(message, dict) else getattr(message, "content", None)
                if isinstance(content, str) and content.strip():
                    return content
                if isinstance(content, list):
                    parts: list[str] = []
                    for item in content:
                        if isinstance(item, dict):
                            text = item.get("text")
                            if text:
                                parts.append(str(text))
                    if parts:
                        return "\n".join(parts)
        structured = result.get("structured_response")
        if structured:
            return str(structured)
    return str(result)


def run_simple_agent(user_input: str) -> AgentResult:
    clean_input = user_input.strip()
    agent = _build_agent()
    runtime_mode = get_runtime_mode()

    if agent is None:
        return AgentResult(
            user_input=clean_input,
            response_text="No compatible LangChain chat model is configured, so the app returned a fallback response.",
            sources=[],
            runtime_mode=runtime_mode,
            used_fallback=True,
            error_message="Missing model or LangChain agent dependencies.",
        )

    try:
        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": clean_input,
                    }
                ]
            }
        )
        response_text = _extract_response_text(result).strip()
        sources = _extract_sources(response_text)
        return AgentResult(
            user_input=clean_input,
            response_text=response_text or "The agent did not return any text.",
            sources=sources,
            runtime_mode=runtime_mode,
            used_fallback=False,
            error_message="",
        )
    except Exception as exc:
        return AgentResult(
            user_input=clean_input,
            response_text="The LangChain agent failed, so the app returned a fallback response.",
            sources=[],
            runtime_mode=runtime_mode,
            used_fallback=True,
            error_message=str(exc),
        )


def build_view_model(result: AgentResult) -> dict[str, object]:
    return {
        "input": result.user_input,
        "response": result.response_text,
        "sources": result.sources,
        "runtime_mode": result.runtime_mode,
        "used_fallback": result.used_fallback,
        "error_message": result.error_message,
    }
