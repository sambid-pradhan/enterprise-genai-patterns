from __future__ import annotations

import html
import re
from collections import OrderedDict
from typing import Callable
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import requests


Candidate = dict[str, object]


_PRIMARY_HOST_HINTS = (
    "arxiv.org",
    "doi.org",
    "acm.org",
    "ieee.org",
    "nature.com",
    "science.org",
    "nist.gov",
    "github.com",
    ".edu",
)


def _classify_source(url: str, title: str = "") -> tuple[str, bool]:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    title_lower = title.lower()

    if "arxiv.org" in host:
        return "paper", True
    if "doi.org" in host:
        return "paper", True
    if any(hint in host for hint in _PRIMARY_HOST_HINTS):
        if "blog" in title_lower or "news" in title_lower:
            return "article", True
        return "official", True
    return "article", False


def _score_candidate(candidate: Candidate, index: int) -> float:
    score = float(candidate.get("score", 0.0) or 0.0)
    if candidate.get("is_primary"):
        score += 0.3
    score += max(0.0, 0.1 - index * 0.01)
    return score


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


def _parse_duckduckgo_html(html_text: str, max_results: int) -> list[Candidate]:
    results: list[Candidate] = []
    pattern = re.compile(
        r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="(?P<url>[^"]+)"[^>]*>(?P<title>.*?)</a>',
        re.IGNORECASE | re.DOTALL,
    )
    for index, match in enumerate(pattern.finditer(html_text)):
        if len(results) >= max_results:
            break
        url = html.unescape(_resolve_duckduckgo_url(match.group("url")))
        title = _strip_tags(html.unescape(match.group("title")))
        source_type, is_primary = _classify_source(url, title)
        results.append(
            {
                "title": title or url,
                "url": url,
                "snippet": "",
                "source_type": source_type,
                "is_primary": is_primary,
                "score": _score_candidate({"is_primary": is_primary, "score": 0.6}, index),
            }
        )
    return results


def search_web(query: str, max_results: int = 5, timeout: int = 15) -> list[Candidate]:
    try:
        from duckduckgo_search import DDGS
    except Exception:
        DDGS = None

    if DDGS is not None:
        try:
            with DDGS() as ddgs:
                raw_results = list(ddgs.text(query, max_results=max_results, safesearch="moderate"))
        except Exception:
            raw_results = []
        else:
            results: list[Candidate] = []
            for index, item in enumerate(raw_results):
                if len(results) >= max_results:
                    break
                url = str(item.get("href") or item.get("url") or "")
                title = str(item.get("title") or url)
                snippet = str(item.get("body") or item.get("snippet") or "")
                source_type, is_primary = _classify_source(url, title)
                results.append(
                    {
                        "title": title,
                        "url": url,
                        "snippet": snippet,
                        "source_type": source_type,
                        "is_primary": is_primary,
                        "score": _score_candidate({"is_primary": is_primary, "score": 0.7}, index),
                    }
                )
            return results

    response = requests.get(
        "https://html.duckduckgo.com/html/",
        params={"q": query},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=timeout,
    )
    response.raise_for_status()
    return _parse_duckduckgo_html(response.text, max_results)


def collect_candidate_sources(
    search_queries: list[str],
    search_fn: Callable[[str], list[Candidate]] | None = None,
) -> list[Candidate]:
    search_fn = search_fn or search_web
    by_url: "OrderedDict[str, Candidate]" = OrderedDict()

    for query in search_queries:
        for candidate in search_fn(query):
            url = str(candidate.get("url") or "").strip()
            if not url:
                continue
            candidate = dict(candidate)
            candidate["score"] = _score_candidate(candidate, len(by_url))
            previous = by_url.get(url)
            if previous is None or float(candidate["score"]) > float(previous["score"]):
                by_url[url] = candidate

    ranked = sorted(by_url.values(), key=lambda item: float(item.get("score", 0.0)), reverse=True)
    return ranked


def filter_primary_sources(candidates: list[Candidate]) -> list[Candidate]:
    return [candidate for candidate in candidates if bool(candidate.get("is_primary"))]

