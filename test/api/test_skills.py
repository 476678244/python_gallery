"""API contract: skills tree + toggle."""

from __future__ import annotations


def test_get_skills_returns_tree_structure(client):
    res = client.get("/skills")
    assert res.status_code == 200
    body = res.json()
    assert "tree" in body
    assert isinstance(body["tree"], list)
    assert body.get("total", 0) >= 0

    folders = [n for n in body["tree"] if n.get("is_folder")]
    # Live env has 4 collections; empty mock still returns list
    ids = {f["id"] for f in folders}
    if folders:
        assert "private" in ids or any(i.startswith("linked/") for i in ids)
        for f in folders:
            assert "enabled" in f
            assert isinstance(f.get("children"), list)


def test_skills_folder_toggle_round_trip(client):
    res = client.get("/skills")
    assert res.status_code == 200
    tree = res.json().get("tree") or []
    folders = [n for n in tree if n.get("is_folder")]
    if not folders:
        return  # no skills loaded in this environment

    folder = folders[0]
    folder_id = folder["id"]

    off = client.post("/skills", json={"folder_id": folder_id, "enabled": False})
    assert off.status_code == 200
    assert off.json()["enabled"] is False

    after = client.get("/skills").json()
    node = next(n for n in after["tree"] if n["id"] == folder_id)
    assert node["enabled"] is False
    assert all(not c.get("enabled", True) for c in node.get("children") or [])

    on = client.post("/skills", json={"folder_id": folder_id, "enabled": True})
    assert on.status_code == 200
    restored = client.get("/skills").json()
    node2 = next(n for n in restored["tree"] if n["id"] == folder_id)
    assert node2["enabled"] is True


def test_build_skill_tree_private_and_linked_labels(client):
    body = client.get("/skills").json()
    names = {n["name"] for n in body.get("tree") or []}
    # When scanner is live these labels must appear
    if body.get("private", 0) > 0:
        assert "Private Skills" in names
    if body.get("linked", 0) > 0:
        assert any("Skills" in n for n in names if n != "Private Skills")
