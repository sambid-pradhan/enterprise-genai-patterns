from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request

from app.db.sqlite import initialize_database, insert_message, upsert_session
from app.schemas.chat import AssistantResponse, ChatRequest
from app.services.chat_service import build_assistant_response


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "assistant.sqlite3"


def create_app(db_path: str | Path | None = None) -> FastAPI:
    resolved_db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    initialize_database(resolved_db_path)

    app = FastAPI(title="GenAI at Scale Backend", version="0.1.0")
    app.state.db_path = resolved_db_path

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/chat", response_model=AssistantResponse)
    def chat(payload: ChatRequest, request: Request) -> AssistantResponse:
        db_file = request.app.state.db_path
        upsert_session(db_file, payload.session_id)
        insert_message(
            db_file,
            session_id=payload.session_id,
            role="user",
            content=payload.message,
        )
        response = build_assistant_response(payload.message)
        insert_message(
            db_file,
            session_id=payload.session_id,
            role="assistant",
            content=response.summary,
            payload=response.model_dump(),
        )
        return response

    return app


app = create_app()

