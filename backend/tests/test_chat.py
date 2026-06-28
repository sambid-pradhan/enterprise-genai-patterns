from __future__ import annotations

import sqlite3


def test_chat_route_returns_structured_response_and_persists_messages(client, db_path):
    response = client.post(
        "/chat",
        json={
            "session_id": "session-1",
            "message": "What can I make with chicken, rice, and spinach?",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) >= {
        "summary",
        "grounding",
        "memory_used",
        "retrieved_items",
        "clarifying_question",
        "next_actions",
        "confidence",
        "ui_components",
    }
    assert payload["summary"]
    assert payload["retrieved_items"]
    assert payload["ui_components"]

    connection = sqlite3.connect(db_path)
    try:
        messages = connection.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id",
            ("session-1",),
        ).fetchall()
    finally:
        connection.close()

    assert [row[0] for row in messages] == ["user", "assistant"]
    assert messages[0][1] == "What can I make with chicken, rice, and spinach?"

