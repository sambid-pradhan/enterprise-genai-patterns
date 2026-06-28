from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1)


class GroundingItem(BaseModel):
    source: str
    id: str


class RetrievedItem(BaseModel):
    id: str
    title: str
    details: dict[str, Any] = Field(default_factory=dict)


class AssistantResponse(BaseModel):
    summary: str
    grounding: list[GroundingItem] = Field(default_factory=list)
    memory_used: list[str] = Field(default_factory=list)
    retrieved_items: list[RetrievedItem] = Field(default_factory=list)
    clarifying_question: str | None = None
    next_actions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    ui_components: list[dict[str, Any]] = Field(default_factory=list)

