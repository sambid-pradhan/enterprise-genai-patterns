from __future__ import annotations


def format_citation(source: dict) -> str:
    title = str(source.get("title") or "Untitled source")
    url = str(source.get("url") or "")
    source_type = str(source.get("source_type") or "source")
    marker = "primary" if source.get("is_primary") else "secondary"
    return f"- [{title}]({url}) ({source_type}, {marker})"

