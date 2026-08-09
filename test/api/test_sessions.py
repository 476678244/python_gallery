"""API contract: sessions + messages CRUD."""

from __future__ import annotations


def test_new_session_uses_global_selected_model(client):
    """New Chat without model must inherit /settings/model (not hardcoded Qwen)."""
    selected = client.put("/settings/model", json={"model": "deepseek-v4-flash"})
    assert selected.status_code == 200
    assert selected.json()["model"] == "deepseek-v4-flash"

    created = client.post("/sessions", json={"title": "New Chat"})
    assert created.status_code == 200
    session = created.json().get("session") or created.json()
    assert session["settings"]["model"] == "deepseek-v4-flash"

    client.delete(f"/sessions/{session['id']}")


def test_default_model_and_models_list_include_deepseek(client):
    """DeepSeek is the product global default and always listed in /settings/models."""
    models = client.get("/settings/models")
    assert models.status_code == 200
    body = models.json()
    assert body.get("default") == "deepseek-v4-flash"
    ids = {m["id"] for m in body.get("models", [])}
    assert "deepseek-v4-flash" in ids
    assert "deepseek-v4-pro" in ids

    selected = client.get("/settings/model")
    assert selected.status_code == 200
    # Fresh test client may not load agent_config; DEFAULT_MODEL must be DeepSeek.
    assert selected.json()["model"] == "deepseek-v4-flash"


def test_session_crud_round_trip(client):
    created = client.post("/sessions", json={"title": "API Contract Chat"})
    assert created.status_code == 200
    body = created.json()
    session = body.get("session") or body
    sid = session["id"]
    assert session["title"] == "API Contract Chat"

    listed = client.get("/sessions")
    assert listed.status_code == 200
    ids = {s["id"] for s in listed.json()["sessions"]}
    assert sid in ids

    got = client.get(f"/sessions/{sid}")
    assert got.status_code == 200
    got_body = got.json()
    assert (got_body.get("session") or got_body)["id"] == sid

    deleted = client.delete(f"/sessions/{sid}")
    assert deleted.status_code == 200

    listed2 = client.get("/sessions").json()["sessions"]
    assert sid not in {s["id"] for s in listed2}


def test_session_messages_replace_and_load(client):
    created = client.post("/sessions", json={"title": "Msg Test"})
    body = created.json()
    sid = (body.get("session") or body)["id"]

    messages = [
        {"id": "m1", "role": "user", "content": "hello"},
        {"id": "m2", "role": "assistant", "content": "hi there"},
    ]
    put = client.post(f"/sessions/{sid}/messages", json={"messages": messages})
    assert put.status_code == 200

    loaded = client.get(f"/sessions/{sid}/messages")
    assert loaded.status_code == 200
    body = loaded.json()
    msgs = body.get("messages") or body
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["content"] == "hi there"

    client.delete(f"/sessions/{sid}")


def test_clear_all_sessions(client, tmp_data_dirs):
    """DELETE /sessions/all wipes sessions.json and message files."""
    a = client.post("/sessions", json={"title": "Clear A"}).json()
    b = client.post("/sessions", json={"title": "Clear B"}).json()
    sid_a = (a.get("session") or a)["id"]
    sid_b = (b.get("session") or b)["id"]

    client.post(
        f"/sessions/{sid_a}/messages",
        json={"messages": [{"id": "m1", "role": "user", "content": "bye"}]},
    )
    client.post(
        f"/sessions/{sid_b}/messages",
        json={"messages": [{"id": "m2", "role": "user", "content": "bye2"}]},
    )

    cleared = client.delete("/sessions/all")
    assert cleared.status_code == 200
    body = cleared.json()
    assert body["success"] is True
    assert body["deleted_count"] == 2
    assert set(body["deleted_ids"]) == {sid_a, sid_b}
    assert body["message_files_removed"] >= 2

    listed = client.get("/sessions").json()["sessions"]
    assert listed == []

    messages_dir = tmp_data_dirs["data"] / "messages"
    assert list(messages_dir.glob("*.json")) == []

    # Idempotent
    again = client.delete("/sessions/all")
    assert again.status_code == 200
    assert again.json()["deleted_count"] == 0
