"""API contract: sessions + messages CRUD."""

from __future__ import annotations


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
