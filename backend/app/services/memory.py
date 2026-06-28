from __future__ import annotations

import re


_PREFERENCE_PATTERNS = (
    (re.compile(r"\bprefer(?:s|) (?P<value>[^.?!,]+)", re.IGNORECASE), "prefers {value}"),
    (re.compile(r"\bremember that i like (?P<value>[^.?!,]+)", re.IGNORECASE), "likes {value}"),
    (re.compile(r"\bremember that i prefer (?P<value>[^.?!,]+)", re.IGNORECASE), "prefers {value}"),
)


def extract_memory_facts(message: str) -> list[str]:
    lowered = message.strip()
    facts: list[str] = []

    for pattern, template in _PREFERENCE_PATTERNS:
        match = pattern.search(lowered)
        if not match:
            continue
        value = match.group("value").strip().rstrip(".")
        if value:
            facts.append(template.format(value=value))

    if not facts and "remember" in lowered.lower():
        cleaned = lowered.lower().replace("remember that ", "").strip()
        if cleaned:
            facts.append(f"memory note: {cleaned}")

    return facts

