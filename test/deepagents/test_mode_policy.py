"""Unit tests for ModePolicy (agent-modes)."""

from types import SimpleNamespace

import pytest
from langchain_core.messages import ToolMessage

from safe_claw.core.agent_modes import (
    ModePolicyError,
    SpawnGateMiddleware,
    resolve_mode_policy,
    spawn_runtime_enabled,
    validate_chat_mode,
)


def test_default_none_is_agent():
    p = resolve_mode_policy(None)
    assert p.mode == "agent"
    assert p.allow_create and p.allow_edit
    assert p.skill_execute == "full"


def test_ask_readonly():
    p = resolve_mode_policy("ask")
    assert not p.allow_create and not p.allow_edit and not p.allow_delete
    assert p.skill_execute == "off"
    assert not p.memory_auto_write


def test_safe_create_only():
    p = resolve_mode_policy("safe")
    assert p.allow_create and not p.allow_edit and not p.allow_delete
    assert p.allow_write is True
    assert p.skill_execute == "restrained"


def test_debug_full_obs():
    p = resolve_mode_policy("debug")
    assert p.observability == "full"
    assert p.allow_edit


def test_subagent_pack():
    p = resolve_mode_policy("subagent")
    assert p.observability == "subagent"
    assert p.spawn == "required"


def test_loop_rejected():
    with pytest.raises(ModePolicyError, match="loop"):
        validate_chat_mode("loop")


def test_invalid_mode():
    with pytest.raises(ModePolicyError, match="Invalid"):
        validate_chat_mode("yolo")


@pytest.mark.parametrize(
    "mode,enabled",
    [
        ("ask", False),
        ("plan", False),  # explore_only not wired
        ("safe", False),
        ("ppt", False),
        ("agent", True),
        ("debug", True),
        ("subagent", True),
    ],
)
def test_spawn_runtime_enabled_matrix(mode, enabled):
    assert spawn_runtime_enabled(resolve_mode_policy(mode)) is enabled


def test_spawn_gate_blocks_task_in_ask():
    mw = SpawnGateMiddleware(resolve_mode_policy("ask"))
    called = {"n": 0}

    def handler(_req):
        called["n"] += 1
        return ToolMessage(content="ran", tool_call_id="t1")

    req = SimpleNamespace(tool_call={"name": "task", "id": "t1", "args": {}})
    out = mw.wrap_tool_call(req, handler)
    assert called["n"] == 0
    assert isinstance(out, ToolMessage)
    assert out.status == "error"
    assert "spawn/task blocked" in out.content


def test_spawn_gate_allows_task_in_agent():
    mw = SpawnGateMiddleware(resolve_mode_policy("agent"))
    called = {"n": 0}

    def handler(_req):
        called["n"] += 1
        return ToolMessage(content="ran", tool_call_id="t1")

    req = SimpleNamespace(tool_call={"name": "task", "id": "t1", "args": {}})
    out = mw.wrap_tool_call(req, handler)
    assert called["n"] == 1
    assert out.content == "ran"


def test_spawn_gate_passes_other_tools_in_ask():
    mw = SpawnGateMiddleware(resolve_mode_policy("ask"))
    called = {"n": 0}

    def handler(_req):
        called["n"] += 1
        return ToolMessage(content="ok", tool_call_id="r1")

    req = SimpleNamespace(tool_call={"name": "read_file", "id": "r1", "args": {}})
    out = mw.wrap_tool_call(req, handler)
    assert called["n"] == 1
    assert out.content == "ok"
