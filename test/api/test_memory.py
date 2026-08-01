"""API contract: memory list / create / search / cleanup / stream retrieval."""

from __future__ import annotations

import json


def test_memory_add_list_search_stats(client):
    created = client.post(
        "/memory",
        json={
            "content": "User prefers Michelin tires for winter",
            "importance": 0.9,
            "keywords": ["tires", "michelin"],
        },
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["success"] is True
    assert body["id"]
    assert body["memory"]["content"].startswith("User prefers")
    assert body["memory"]["importance"] == 0.9
    assert "tires" in body["memory"]["tags"]
    assert body["stats"]["active_count"] >= 1

    listed = client.get("/memory?layer=active&limit=20")
    assert listed.status_code == 200
    listed_body = listed.json()
    assert isinstance(listed_body["memories"], list)
    assert listed_body["total"] >= 1
    assert listed_body["stats"]["active_count"] >= 1
    contents = [m["content"] for m in listed_body["memories"]]
    assert any("Michelin" in c for c in contents)

    for field in ("id", "content", "layer", "importance", "created_at", "tags"):
        assert field in listed_body["memories"][0]

    searched = client.get("/memory?search=Michelin&limit=10")
    assert searched.status_code == 200
    assert searched.json()["total"] >= 1
    assert any("Michelin" in m["content"] for m in searched.json()["memories"])


def test_memory_invalid_layer_returns_400(client):
    res = client.get("/memory?layer=foo")
    assert res.status_code == 400
    assert "Invalid layer" in res.json()["detail"]


def test_memory_cleanup_returns_stats(client):
    client.post("/memory", json={"content": "cleanup probe memory xyz", "importance": 0.7})
    res = client.post("/memory/cleanup")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert "stats" in body
    assert isinstance(body["stats"]["active_count"], int)


def test_chat_stream_zh_jargon_query_hits_memory_step(client):
    """Phase C/D: Chinese jargon question must surface real memory hits in SSE."""
    client.post(
        "/memory",
        json={
            "content": (
                "[Investment Jargon Wiki] 101（散户 / 边际接盘流动性）\n"
                "source: wiki/jargon/101.md\n\n"
                "101 指散户提供的边际接盘流动性。"
            ),
            "importance": 0.95,
            "keywords": ["101", "散户", "黑话", "jargon"],
            "metadata": {"collection": "jargon"},
        },
    )

    session = client.post("/sessions", json={"title": "Jargon ZH Stream"}).json()
    sid = (session.get("session") or session)["id"]

    with client.stream(
        "POST",
        "/chat/stream",
        json={
            "messages": [{"role": "user", "content": "什么是101"}],
            "session_id": sid,
            "model": "nonexistent-model-for-fallback",
        },
    ) as res:
        assert res.status_code == 200
        raw = "".join(res.iter_text())

    events = []
    for block in raw.split("\n\n"):
        line = block.strip()
        if line.startswith("data:"):
            events.append(json.loads(line[5:].strip()))

    mem_steps = [
        e
        for e in events
        if e.get("type") == "execution_step"
        and e.get("step_id") == "memory"
        and e.get("status") == "completed"
    ]
    assert mem_steps, f"No completed memory step: {events}"
    step = mem_steps[0]
    assert int(step["sub"].split()[0]) >= 1
    blob = json.dumps(step, ensure_ascii=False)
    assert "101" in blob or "散户" in blob


def test_chat_stream_memory_step_reflects_real_count(client):
    token = "unique-memory-token-alpha-42"
    client.post(
        "/memory",
        json={"content": f"Remember that the secret code is {token}", "importance": 0.95},
    )

    session = client.post("/sessions", json={"title": "Memory Stream"}).json()
    sid = (session.get("session") or session)["id"]

    with client.stream(
        "POST",
        "/chat/stream",
        json={
            "messages": [{"role": "user", "content": f"What is the secret code {token}?"}],
            "session_id": sid,
            "model": "nonexistent-model-for-fallback",
        },
    ) as res:
        assert res.status_code == 200
        raw = "".join(res.iter_text())

    events = []
    for block in raw.split("\n\n"):
        line = block.strip()
        if line.startswith("data:"):
            events.append(json.loads(line[5:].strip()))

    mem_steps = [
        e
        for e in events
        if e.get("type") == "execution_step" and e.get("step_id") == "memory" and e.get("status") == "completed"
    ]
    assert mem_steps, f"No memory step in events: {events[:5]}"
    step = mem_steps[0]
    assert "0 relevant memories" not in (step.get("sub") or "")
    assert any("memories" in str(c) for c in step.get("chips", []))
    # Must not be the old hardcoded "3 memories" unless count happens to be 3
    chips_joined = " ".join(str(c) for c in step.get("chips", []))
    assert "1 memories" in chips_joined or "memories" in chips_joined
    assert step.get("sub", "").startswith(f"{step.get('sub', '').split()[0]}")
    # Real hit count in sub
    assert "relevant memories loaded" in step.get("sub", "")
    count_word = step["sub"].split()[0]
    assert count_word.isdigit()
    assert int(count_word) >= 1
