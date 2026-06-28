from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.schemas.chat import AssistantResponse, GroundingItem, RetrievedItem
from app.services.memory import extract_memory_facts


@dataclass(frozen=True)
class CatalogEntry:
    id: str
    title: str
    details: dict[str, Any]


_CATALOG = (
    CatalogEntry(
        id="recipe_spicy_chicken_rice_bowl",
        title="Spicy chicken rice bowl",
        details={"prep_minutes": 25, "ingredients": ["chicken", "rice", "spinach"]},
    ),
    CatalogEntry(
        id="recipe_veggie_stir_fry",
        title="Veggie stir fry",
        details={"prep_minutes": 20, "ingredients": ["spinach", "rice", "garlic"]},
    ),
    CatalogEntry(
        id="recipe_golden_pasta",
        title="Golden pasta",
        details={"prep_minutes": 18, "ingredients": ["pasta", "olive oil", "garlic"]},
    ),
)


def _score_entry(message: str, entry: CatalogEntry) -> int:
    haystack = f"{message} {entry.title} {' '.join(entry.details.get('ingredients', []))}".lower()
    keywords = ("chicken", "rice", "spinach", "pasta", "quick", "dinner", "recipe")
    return sum(1 for keyword in keywords if keyword in haystack and keyword in entry.title.lower() or keyword in haystack)


def _retrieve_items(message: str) -> list[CatalogEntry]:
    scored = sorted(
        ((entry, _score_entry(message, entry)) for entry in _CATALOG),
        key=lambda item: (-item[1], item[0].title),
    )
    selected = [entry for entry, score in scored if score > 0]
    return selected[:2] or [scored[0][0]]


def build_assistant_response(message: str) -> AssistantResponse:
    memory_facts = extract_memory_facts(message)
    retrieved = _retrieve_items(message)
    lowered = message.lower()
    is_memory_turn = "remember" in lowered or any(fact.startswith("memory note:") for fact in memory_facts)
    has_ingredients = any(word in lowered for word in ("chicken", "rice", "spinach", "pasta"))

    if is_memory_turn and memory_facts:
        summary = "Got it. I'll remember that preference."
        clarifying_question = None
        next_actions = ["Ask for a recipe or grocery idea whenever you're ready."]
        confidence = 0.94
        ui_components: list[dict[str, Any]] = [
            {
                "type": "memory_confirmation",
                "props": {"facts": memory_facts},
            }
        ]
    elif has_ingredients:
        summary = "Here are a couple of grounded meal ideas based on your ingredients."
        clarifying_question = None
        next_actions = ["Open the top recipe", "Ask for a substitution"]
        confidence = 0.88
        ui_components = [
            {
                "type": "recipe_card",
                "props": {
                    "title": entry.title,
                    "prep_minutes": entry.details.get("prep_minutes"),
                    "ingredients": entry.details.get("ingredients", []),
                },
            }
            for entry in retrieved
        ]
    else:
        summary = "I can help with recipes, grocery ideas, or preference memory."
        clarifying_question = "What are you trying to make or remember?"
        next_actions = ["Share ingredients", "Ask me to remember a preference"]
        confidence = 0.72
        ui_components = [
            {
                "type": "clarifying_question",
                "props": {"question": clarifying_question},
            }
        ]

    return AssistantResponse(
        summary=summary,
        grounding=[GroundingItem(source="seed_catalog", id=entry.id) for entry in retrieved],
        memory_used=memory_facts,
        retrieved_items=[
            RetrievedItem(id=entry.id, title=entry.title, details=entry.details)
            for entry in retrieved
        ],
        clarifying_question=clarifying_question,
        next_actions=next_actions,
        confidence=confidence,
        ui_components=ui_components,
    )
