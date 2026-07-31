"""API contract: /api/upload confined to WORKSPACE_DIR."""

from __future__ import annotations

from io import BytesIO


def test_upload_relative_path_lands_in_workspace(client, tmp_data_dirs):
    files = {"file": ("hello.txt", BytesIO(b"hello safeclaw"), "text/plain")}
    data = {"path": "uploaded/hello.txt"}
    res = client.post("/api/upload", files=files, data=data)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    saved = tmp_data_dirs["workspace"] / "uploaded" / "hello.txt"
    assert saved.exists()
    assert saved.read_bytes() == b"hello safeclaw"


def test_upload_rejects_path_traversal(client, tmp_data_dirs):
    files = {"file": ("evil.txt", BytesIO(b"nope"), "text/plain")}
    data = {"path": "../evil.txt"}
    res = client.post("/api/upload", files=files, data=data)
    assert res.status_code == 400
    assert "escapes WORKSPACE_DIR" in res.json()["detail"]


def test_upload_rejects_absolute_outside_workspace(client):
    files = {"file": ("evil.txt", BytesIO(b"nope"), "text/plain")}
    data = {"path": "/tmp/uploaded/evil.txt"}
    res = client.post("/api/upload", files=files, data=data)
    assert res.status_code == 400
