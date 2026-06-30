from __future__ import annotations

from html.parser import HTMLParser

import requests


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs):  # type: ignore[override]
        if tag in {"p", "br", "div", "li", "section", "article", "h1", "h2", "h3", "h4"}:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self._parts.append(text)

    def get_text(self) -> str:
        return "\n".join(part for part in self._parts if part.strip())


def _fallback_extract(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    lines = [line.strip() for line in parser.get_text().splitlines() if line.strip()]
    return "\n".join(lines)


def extract_main_text(html: str) -> str:
    try:
        import trafilatura
    except Exception:
        trafilatura = None

    if trafilatura is not None:
        extracted = trafilatura.extract(html, include_comments=False, include_tables=False)
        if extracted:
            return extracted.strip()

    return _fallback_extract(html)


def fetch_page_text(url: str, timeout: int = 20) -> str:
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
        response.raise_for_status()
    except Exception:
        return ""
    return extract_main_text(response.text)

