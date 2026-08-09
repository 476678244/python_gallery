"""API contract: /chat/stream SSE."""

from __future__ import annotations

import json


def _parse_sse_types(raw: str) -> list[str]:
    types: list[str] = []
    for line in raw.splitlines():
        if not line.startswith("data:"):
            continue
        try:
            types.append(json.loads(line[5:].strip()).get("type"))
        except Exception:
            continue
    return [t for t in types if t]


def test_chat_stream_requires_user_message(client):
    res = client.post(
        "/chat/stream",
        json={"messages": [{"role": "assistant", "content": "only assistant"}], "session_id": "t"},
    )
    assert res.status_code == 200
    types = _parse_sse_types(res.text)
    assert "error" in types
    assert "done" in types


def test_chat_stream_emits_done(client):
    res = client.post(
        "/chat/stream",
        json={
            "messages": [{"role": "user", "content": "Hi from contract test"}],
            "session_id": "contract-stream",
            "model": "qwen3.5-9b-vlm",
            "enabled_skills": [],
        },
    )
    assert res.status_code == 200
    assert "data:" in res.text
    types = _parse_sse_types(res.text)
    assert "execution_step" in types
    assert "done" in types
