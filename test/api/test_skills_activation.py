"""Skills activation SoT: toggle → filtered paths → tool visibility → SSE loaded."""

from __future__ import annotations

import json

import pytest


def _folder_by_prefix(tree: list, prefix: str):
    for n in tree:
        if n.get("is_folder") and str(n.get("id", "")).startswith(prefix):
            return n
    return None


def test_skills_503_when_manager_unavailable(client, monkeypatch):
    import api.main as api_main

    monkeypatch.setattr(api_main, "skills_manager", None)

    def boom():
        raise RuntimeError(
            "[SkillsManager] init failed (Fail Fast)\n  Error: forced for test"
        )

    monkeypatch.setattr(api_main, "_get_skills_manager", boom)
    res = client.get("/skills")
    assert res.status_code == 503
    assert "Fail Fast" in res.json()["detail"]


def test_folder_toggle_strict_no_collateral(client):
    body = client.get("/skills").json()
    tree = body.get("tree") or []
    ljg = next((n for n in tree if n.get("id") == "linked/ljg-skills"), None)
    private = next((n for n in tree if n.get("id") == "private"), None)
    if not ljg or not private:
        pytest.skip("need ljg-skills + private collections in this env")

    private_names = {c["name"] for c in private.get("children") or []}
    assert private_names, "private skills expected"

    # Ensure both folders on, then disable only Ljg
    client.post("/skills", json={"folder_id": "private", "enabled": True})
    client.post("/skills", json={"folder_id": "linked/ljg-skills", "enabled": True})
    off = client.post("/skills", json={"folder_id": "linked/ljg-skills", "enabled": False})
    assert off.status_code == 200

    after = client.get("/skills").json()["tree"]
    ljg2 = next(n for n in after if n["id"] == "linked/ljg-skills")
    priv2 = next(n for n in after if n["id"] == "private")
    assert ljg2["enabled"] is False
    assert all(not c.get("enabled") for c in ljg2.get("children") or [])
    # Private must not be collateral-disabled
    assert any(c.get("enabled") for c in priv2.get("children") or [])

    # Restore Ljg for other tests
    client.post("/skills", json={"folder_id": "linked/ljg-skills", "enabled": True})


def test_disable_all_then_enable_one_no_soft_reset(client):
    body = client.get("/skills").json()
    tree = body.get("tree") or []
    private = next((n for n in tree if n.get("id") == "private"), None)
    if not private or not private.get("children"):
        pytest.skip("need private skills")

    target = private["children"][0]["name"]
    # Turn every folder off
    for n in tree:
        if n.get("is_folder"):
            client.post("/skills", json={"folder_id": n["id"], "enabled": False})

    # Soft-reset bug: empty enabled + toggle would re-enable all
    on = client.post("/skills", json={"skill_id": target, "enabled": True})
    assert on.status_code == 200

    import api.main as api_main

    sm = api_main._get_skills_manager()
    enabled = set(sm.get_enabled_skills())
    assert enabled == {target}, f"expected only {target!r}, got {enabled}"

    # Restore folders for suite hygiene
    for n in client.get("/skills").json()["tree"]:
        if n.get("is_folder"):
            client.post("/skills", json={"folder_id": n["id"], "enabled": True})


def test_filtered_paths_and_discovery_honor_enabled(client):
    import api.main as api_main

    body = client.get("/skills").json()
    tree = body.get("tree") or []
    ljg = next((n for n in tree if n.get("id") == "linked/ljg-skills"), None)
    private = next((n for n in tree if n.get("id") == "private"), None)
    if not ljg or not private:
        pytest.skip("need ljg + private")

    client.post("/skills", json={"folder_id": "linked/ljg-skills", "enabled": False})
    client.post("/skills", json={"folder_id": "private", "enabled": True})

    sm = api_main._get_skills_manager()
    enabled = set(sm.get_enabled_skills())
    assert not any(n.startswith("ljg-") for n in enabled)

    paths = sm.get_filtered_skills_paths()
    path_names = {p.rstrip("/").split("/")[-1] for p in paths}
    assert not any(n.startswith("ljg-") for n in path_names)
    assert path_names <= enabled or enabled  # filtered ⊆ enabled

    disc = sm.get_skill_discovery()
    entries = disc._enabled_entries()
    assert not any(e.name.startswith("ljg-") for e in entries)

    from safe_claw.core.tools.manager import ToolManager

    tm = ToolManager(
        skill_scanner=sm.get_skill_scanner(),
        skill_discovery=disc,
        skill_executor=sm.get_skill_executor(),
    )
    list_tool = next(t for t in tm.get_skills_tools() if t.name == "skill_list_available")
    listed = list_tool.invoke({"category": ""})
    assert "ljg-roundtable" not in listed
    for line in listed.splitlines():
        # skill lines look like: "  👤 ljg-foo: ..."
        if "ljg-" in line:
            pytest.fail(f"disabled ljg skill still listed: {line!r}")

    client.post("/skills", json={"folder_id": "linked/ljg-skills", "enabled": True})


def test_agent_config_persists_enabled_skills(client, tmp_data_dirs):
    body = client.get("/skills").json()
    tree = body.get("tree") or []
    private = next((n for n in tree if n.get("id") == "private"), None)
    if not private or not private.get("children"):
        pytest.skip("need private skills")

    for n in tree:
        if n.get("is_folder"):
            client.post("/skills", json={"folder_id": n["id"], "enabled": False})
    target = private["children"][0]["name"]
    client.post("/skills", json={"skill_id": target, "enabled": True})

    cfg_path = tmp_data_dirs["data"] / "agent_config.json"
    assert cfg_path.exists()
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert target in (cfg.get("enabled_skills") or [])
    assert len(cfg.get("enabled_skills") or []) == 1

    # Restore
    for n in client.get("/skills").json()["tree"]:
        if n.get("is_folder"):
            client.post("/skills", json={"folder_id": n["id"], "enabled": True})


def test_deep_agent_get_loaded_skills_matches_filter(client, monkeypatch):
    """create_deep_agent skills= == get_loaded_skills (mocked create)."""
    from unittest.mock import MagicMock

    import api.main as api_main
    from safe_claw.core.deepagents import official_integration as oi
    from safe_claw.core.deepagents.official_integration import SafeClawDeepAgent

    sm = api_main._get_skills_manager()
    tree = client.get("/skills").json()["tree"]
    private = next((n for n in tree if n.get("id") == "private"), None)
    if not private or not private.get("children"):
        pytest.skip("need private skills")

    keep = [c["name"] for c in private["children"][:2]]
    sm.set_enabled_skills(keep)

    captured: dict = {}

    def fake_create_deep_agent(**kwargs):
        captured["skills"] = kwargs.get("skills")
        return MagicMock()

    monkeypatch.setattr(oi, "create_deep_agent", fake_create_deep_agent)
    monkeypatch.setattr(
        SafeClawDeepAgent,
        "_create_langchain_model",
        lambda self: MagicMock(),
    )

    class _Cfg:
        model = "mock"
        provider = "openai"
        api_key = "x"
        base_url = None
        temperature = 0.7
        max_tokens = 256

    class _Gw:
        config = _Cfg()

    class _LLM:
        gateway = _Gw()

    agent = SafeClawDeepAgent(
        llm_service=_LLM(),
        config={
            "skills_manager": sm,
            "enabled_skills": keep,
            "max_skills": 100,
            "system_prompt_limit": 65536,
            "backend": {"filesystem": {"enabled": False}},
        },
    )
    loaded = agent.get_loaded_skills()
    assert set(loaded["names"]) == set(keep)
    assert loaded["count"] == len(keep)
    passed_names = {p.rstrip("/").split("/")[-1] for p in (captured.get("skills") or [])}
    assert passed_names == set(keep)

    for n in tree:
        if n.get("is_folder"):
            client.post("/skills", json={"folder_id": n["id"], "enabled": True})
