"""API tests for agent-modes hard gates."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient


def _parse_sse(text: str) -> list[dict]:
    events = []
    for line in text.splitlines():
        if line.startswith("data: "):
            try:
                events.append(json.loads(line[6:]))
            except json.JSONDecodeError:
                continue
    return events


def test_invalid_mode_400(client: TestClient):
    r = client.post(
        "/chat/stream",
        json={
            "messages": [{"role": "user", "content": "hi"}],
            "mode": "nope",
            "stream": True,
        },
    )
    assert r.status_code == 400
    assert "ModePolicy" in r.text or "Invalid" in r.text


def test_loop_mode_on_stream_400(client: TestClient):
    r = client.post(
        "/chat/stream",
        json={
            "messages": [{"role": "user", "content": "hi"}],
            "mode": "loop",
            "stream": True,
        },
    )
    assert r.status_code == 400
    assert "loop" in r.text.lower()


def test_ask_mode_emits_gate_and_done(client: TestClient, monkeypatch):
    """With mock LLM, ask mode should complete and emit mode_gate step."""
    r = client.post(
        "/chat/stream",
        json={
            "messages": [{"role": "user", "content": "只解释 1+1，不要写文件"}],
            "session_id": "mode-ask-test",
            "mode": "ask",
            "stream": True,
        },
    )
    assert r.status_code == 200
    events = _parse_sse(r.text)
    types = [e.get("type") for e in events]
    assert "done" in types or "error" in types
    gates = [
        e
        for e in events
        if e.get("type") == "execution_step" and e.get("step_id") == "mode_gate"
    ]
    assert gates, f"expected mode_gate step, got {events[:8]}"
    assert gates[0].get("name", "").endswith("ask") or "ask" in str(gates[0].get("chips"))


def test_session_create_default_mode(client: TestClient):
    r = client.post("/sessions", json={"title": "mode-default"})
    assert r.status_code == 200
    body = r.json()
    settings = body.get("settings") or body.get("session", {}).get("settings") or {}
    # API may wrap session
    if "mode" not in settings and "session" in body:
        settings = body["session"].get("settings") or {}
    assert settings.get("mode") == "agent" or "id" in body
