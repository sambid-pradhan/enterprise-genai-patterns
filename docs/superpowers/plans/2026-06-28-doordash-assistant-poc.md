# DoorDash-Style Assistant PoC Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete local DoorDash-style assistant MVP for grocery and recipe assistance with chat, grounded retrieval, durable memory, structured UI cards, streaming responses, and evaluation logging.

**Architecture:** Use a two-app monorepo with a Next.js frontend and a FastAPI backend. The backend owns orchestration, Postgres persistence, memory extraction, retrieval, and evaluation; the frontend owns chat UX and structured component rendering from model-emitted UI JSON. Keep the MVP as one vertical slice so every layer ships together and the assistant feels complete rather than partial.

**Tech Stack:** Next.js, React, TypeScript, Tailwind CSS, FastAPI, Python, Pydantic, LangGraph, PostgreSQL, pgvector, OpenRouter-compatible LLM calls, Docker Compose, Playwright, pytest.

---

### Task 1: Scaffold the workspace and developer loop

**Files:**
- Create: `package.json`
- Create: `pnpm-workspace.yaml`
- Create: `apps/web/package.json`
- Create: `apps/web/next.config.ts`
- Create: `apps/web/tsconfig.json`
- Create: `apps/web/tailwind.config.ts`
- Create: `apps/web/postcss.config.js`
- Create: `apps/web/app/layout.tsx`
- Create: `apps/web/app/page.tsx`
- Create: `apps/api/pyproject.toml`
- Create: `apps/api/uv.lock` or `apps/api/requirements.txt`
- Create: `apps/api/app/__init__.py`
- Create: `apps/api/app/main.py`
- Create: `apps/api/tests/test_health.py`
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `README.md`

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint_returns_ok():
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest apps/api/tests/test_health.py -v`

Expected: failure because the backend app and health route do not exist yet.

- [ ] **Step 3: Add the minimal scaffold**

```python
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest apps/api/tests/test_health.py -v`

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add package.json pnpm-workspace.yaml apps/web apps/api docker-compose.yml .env.example README.md
git commit -m "chore: scaffold assistant workspace"
```

### Task 2: Define the shared chat and UI contracts

**Files:**
- Create: `apps/api/app/schemas/chat.py`
- Create: `apps/api/app/schemas/ui.py`
- Create: `apps/api/tests/test_ui_schema.py`
- Create: `apps/web/src/lib/ui-schema.ts`
- Create: `apps/web/src/components/generative/render-ui.tsx`
- Create: `apps/web/src/components/generative/types.ts`
- Create: `apps/web/src/components/generative/__tests__/render-ui.test.tsx`

- [ ] **Step 1: Write the failing test**

```python
from app.schemas.ui import AssistantResponse


def test_assistant_response_requires_summary_and_ui_components():
    payload = {
        "summary": "Here are three quick dinner ideas.",
        "grounding": [{"source": "catalog_items", "id": "recipe_1"}],
        "memory_used": ["prefers spicy food"],
        "retrieved_items": [{"id": "recipe_1", "title": "Spicy chicken bowl"}],
        "clarifying_question": None,
        "next_actions": ["open recipe 1"],
        "confidence": 0.84,
        "ui_components": [{"type": "recipe_card", "props": {"title": "Spicy chicken bowl"}}],
    }

    response = AssistantResponse.model_validate(payload)
    assert response.summary == "Here are three quick dinner ideas."
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest apps/api/tests/test_ui_schema.py -v`

Expected: failure because the response schema is not implemented yet.

- [ ] **Step 3: Add the minimal schema**

```python
from typing import Any, Literal

from pydantic import BaseModel, Field


class GroundingItem(BaseModel):
    source: str
    id: str


class RetrievedItem(BaseModel):
    id: str
    title: str


class UIComponent(BaseModel):
    type: Literal[
        "recipe_card",
        "recipe_list",
        "ingredient_chip",
        "comparison_table",
        "clarifying_question",
        "cart_summary",
    ]
    props: dict[str, Any] = Field(default_factory=dict)


class AssistantResponse(BaseModel):
    summary: str
    grounding: list[GroundingItem] = Field(default_factory=list)
    memory_used: list[str] = Field(default_factory=list)
    retrieved_items: list[RetrievedItem] = Field(default_factory=list)
    clarifying_question: str | None = None
    next_actions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    ui_components: list[UIComponent] = Field(default_factory=list)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest apps/api/tests/test_ui_schema.py -v`

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/schemas apps/api/tests apps/web/src/lib apps/web/src/components/generative
git commit -m "feat: add shared assistant response contract"
```

### Task 3: Build the Postgres schema, repositories, and seeded demo data

**Files:**
- Create: `apps/api/app/db.py`
- Create: `apps/api/app/models.py`
- Create: `apps/api/app/repos/sessions.py`
- Create: `apps/api/app/repos/messages.py`
- Create: `apps/api/app/repos/memory.py`
- Create: `apps/api/app/repos/catalog.py`
- Create: `apps/api/migrations/versions/0001_init.py`
- Create: `apps/api/scripts/seed_demo_data.py`
- Create: `apps/api/tests/test_repos.py`
- Create: `apps/api/tests/test_seed_data.py`

- [ ] **Step 1: Write the failing test**

```python
from app.repos.catalog import CatalogRepository


def test_catalog_lookup_returns_seeded_recipe(db_session):
    repo = CatalogRepository(db_session)
    item = repo.get_by_slug("spicy-chicken-bowl")
    assert item is not None
    assert item.title == "Spicy chicken bowl"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest apps/api/tests/test_repos.py -v`

Expected: failure because the database layer and repositories are not implemented yet.

- [ ] **Step 3: Add the minimal schema and repository layer**

```python
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class CatalogItem(Base):
    __tablename__ = "catalog_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    prep_minutes: Mapped[int] = mapped_column(Integer)
    spice_level: Mapped[str] = mapped_column(String(32))
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest apps/api/tests/test_repos.py -v`

Expected: pass after migrations and seed data are wired up.

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/db.py apps/api/app/models.py apps/api/app/repos apps/api/migrations apps/api/scripts apps/api/tests
git commit -m "feat: add persistence and demo catalog data"
```

### Task 4: Implement retrieval, memory extraction, and ranking rules

**Files:**
- Create: `apps/api/app/services/retrieval.py`
- Create: `apps/api/app/services/memory.py`
- Create: `apps/api/app/services/ranking.py`
- Create: `apps/api/tests/test_retrieval.py`
- Create: `apps/api/tests/test_memory.py`
- Create: `apps/api/tests/test_ranking.py`

- [ ] **Step 1: Write the failing test**

```python
from app.services.memory import extract_durable_facts


def test_extract_durable_facts_keeps_food_preferences():
    result = extract_durable_facts("I prefer oat milk and spicy food, but only for dinner.")
    assert "prefers oat milk" in result
    assert "prefers spicy food" in result
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest apps/api/tests/test_memory.py -v`

Expected: failure because the memory extractor is not implemented yet.

- [ ] **Step 3: Add the minimal implementation**

```python
def extract_durable_facts(text: str) -> list[str]:
    facts: list[str] = []
    lowered = text.lower()
    if "oat milk" in lowered:
        facts.append("prefers oat milk")
    if "spicy" in lowered:
        facts.append("prefers spicy food")
    return facts
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest apps/api/tests/test_memory.py -v`

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/services apps/api/tests
git commit -m "feat: add memory extraction and retrieval helpers"
```

### Task 5: Implement the LangGraph orchestration and chat endpoint

**Files:**
- Create: `apps/api/app/graph.py`
- Create: `apps/api/app/services/router.py`
- Create: `apps/api/app/services/answer.py`
- Create: `apps/api/app/routes/chat.py`
- Modify: `apps/api/app/main.py`
- Create: `apps/api/tests/test_chat_route.py`
- Create: `apps/api/tests/test_graph.py`

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient

from app.main import create_app


def test_chat_route_returns_structured_response():
    client = TestClient(create_app())
    response = client.post("/chat", json={"session_id": "s1", "message": "what can I make with chicken and rice?"})
    assert response.status_code == 200
    payload = response.json()
    assert "summary" in payload
    assert "ui_components" in payload
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest apps/api/tests/test_chat_route.py -v`

Expected: failure because the route and orchestration are not wired yet.

- [ ] **Step 3: Add the minimal orchestration and endpoint**

```python
from fastapi import APIRouter

from app.schemas.ui import AssistantResponse

router = APIRouter()


@router.post("/chat", response_model=AssistantResponse)
def chat(payload: dict) -> AssistantResponse:
    return AssistantResponse(
        summary="Try a spicy chicken rice bowl.",
        grounding=[{"source": "catalog_items", "id": "recipe_1"}],
        memory_used=[],
        retrieved_items=[{"id": "recipe_1", "title": "Spicy chicken bowl"}],
        clarifying_question=None,
        next_actions=["open recipe_1"],
        confidence=0.76,
        ui_components=[{"type": "recipe_card", "props": {"title": "Spicy chicken bowl"}}],
    )
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest apps/api/tests/test_chat_route.py -v`

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/graph.py apps/api/app/services apps/api/app/routes apps/api/app/main.py apps/api/tests
git commit -m "feat: add chat orchestration and response endpoint"
```

### Task 6: Build the Next.js chat interface and structured UI renderer

**Files:**
- Create: `apps/web/app/layout.tsx`
- Create: `apps/web/app/page.tsx`
- Create: `apps/web/src/components/chat/chat-shell.tsx`
- Create: `apps/web/src/components/chat/message-list.tsx`
- Create: `apps/web/src/components/chat/message-input.tsx`
- Create: `apps/web/src/components/generative/recipe-card.tsx`
- Create: `apps/web/src/components/generative/recipe-list.tsx`
- Create: `apps/web/src/components/generative/clarifying-question.tsx`
- Create: `apps/web/src/components/generative/render-ui.tsx`
- Create: `apps/web/app/api/chat/route.ts`
- Create: `apps/web/src/components/chat/__tests__/message-list.test.tsx`
- Create: `apps/web/e2e/chat.spec.ts`

- [ ] **Step 1: Write the failing test**

```tsx
import { render, screen } from "@testing-library/react";

import { MessageList } from "../message-list";


test("renders assistant summary and recipe card title", () => {
  render(
    <MessageList
      messages={[
        {
          role: "assistant",
          summary: "Try this recipe",
          ui_components: [{ type: "recipe_card", props: { title: "Spicy chicken bowl" } }],
        },
      ]}
    />
  );

  expect(screen.getByText("Try this recipe")).toBeInTheDocument();
  expect(screen.getByText("Spicy chicken bowl")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pnpm --filter web test`

Expected: failure because the chat components and renderer do not exist yet.

- [ ] **Step 3: Add the minimal UI and renderer**

```tsx
type Message = {
  role: "user" | "assistant";
  summary?: string;
  ui_components?: Array<{ type: string; props: Record<string, unknown> }>;
};

export function MessageList({ messages }: { messages: Message[] }) {
  return (
    <div>
      {messages.map((message, index) => (
        <article key={index}>
          {message.summary ? <p>{message.summary}</p> : null}
          {message.ui_components?.map((component, componentIndex) => {
            if (component.type === "recipe_card") {
              return <div key={componentIndex}>{String(component.props.title)}</div>;
            }
            return null;
          })}
        </article>
      ))}
    </div>
  );
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pnpm --filter web test`

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add apps/web/app apps/web/src apps/web/e2e
git commit -m "feat: add chat UI and structured component rendering"
```

### Task 7: Add evaluation logging, scenario replay, and debug views

**Files:**
- Create: `apps/api/app/services/eval.py`
- Create: `apps/api/app/routes/debug.py`
- Create: `apps/api/scripts/run_scenarios.py`
- Create: `apps/api/tests/test_eval.py`
- Create: `apps/api/tests/test_scenarios.py`
- Create: `docs/scenarios/grocery-recipe-scenarios.md`

- [ ] **Step 1: Write the failing test**

```python
from app.services.eval import score_turn


def test_score_turn_rewards_grounded_response():
    score = score_turn(
        grounding=[{"source": "catalog_items", "id": "recipe_1"}],
        memory_used=["prefers spicy food"],
        clarifying_question=None,
        ui_components=[{"type": "recipe_card", "props": {"title": "Spicy chicken bowl"}}],
    )
    assert score >= 0.8
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest apps/api/tests/test_eval.py -v`

Expected: failure because the evaluator does not exist yet.

- [ ] **Step 3: Add the minimal evaluator**

```python
def score_turn(
    grounding: list[dict],
    memory_used: list[str],
    clarifying_question: str | None,
    ui_components: list[dict],
) -> float:
    score = 0.0
    if grounding:
        score += 0.4
    if memory_used:
        score += 0.2
    if ui_components:
        score += 0.2
    if clarifying_question is None:
        score += 0.2
    return score
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest apps/api/tests/test_eval.py -v`

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/services/eval.py apps/api/app/routes/debug.py apps/api/scripts/run_scenarios.py apps/api/tests docs/scenarios
git commit -m "feat: add eval scoring and replay scenarios"
```

### Task 8: Run full end-to-end verification and tighten the MVP

**Files:**
- Modify: `README.md`
- Modify: `docs/scenarios/grocery-recipe-scenarios.md`
- Modify: `apps/api/app/main.py`
- Modify: `apps/web/app/page.tsx`
- Create: `apps/web/e2e/full-flow.spec.ts`

- [ ] **Step 1: Write the failing test**

```ts
import { test, expect } from "@playwright/test";

test("user can ask for a recipe and see a grounded card", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Message").fill("What can I make with chicken, rice, and spinach?");
  await page.getByRole("button", { name: "Send" }).click();
  await expect(page.getByText("recipe")).toBeVisible();
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pnpm --filter web test:e2e`

Expected: failure until the frontend, backend, and seed data are fully wired together.

- [ ] **Step 3: Tighten the integration points**

```text
Wire the frontend to the backend chat route.
Confirm the backend returns grounded responses from the seeded catalog.
Confirm memory writes survive a restart.
Confirm the debug surface shows grounding, memory usage, and eval score.
```

- [ ] **Step 4: Run the test to verify it passes**

Run:
`pytest apps/api/tests -v`
`pnpm --filter web test`
`pnpm --filter web test:e2e`

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/scenarios apps/api apps/web
git commit -m "feat: finish end-to-end assistant MVP"
```

## Self-Review Checklist

- Every vision item maps to at least one task.
- Grocery/recipe is the only MVP domain, which keeps the plan cohesive.
- The plan includes chat, memory, retrieval, orchestration, structured UI, evaluation, and end-to-end verification.
- Each task has explicit files, a failing test, a minimal implementation, a rerun command, and a commit.
- No task depends on a function or type that is never defined earlier in the plan.
