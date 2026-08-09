"""Unit tests: real MemoryManager wiring for memory search/write tools."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from safe_claw.core.memory.manager import MemoryManager
from safe_claw.core.tools.manager import ToolManager
from safe_claw.models.config import MemoryConfig


def _tool_manager(memory_manager=None) -> ToolManager:
    return ToolManager(
        skill_scanner=MagicMock(),
        skill_discovery=MagicMock(),
        skill_executor=MagicMock(),
        memory_manager=memory_manager,
    )


def _by_name(tm: ToolManager, name: str):
    for t in tm.get_all_tools():
        if getattr(t, "name", None) == name:
            return t
    raise AssertionError(f"tool not found: {name}")


def test_memory_search_requires_manager():
    tm = _tool_manager(None)
    search = _by_name(tm, "safe_claw_memory_search")
    with pytest.raises(ValueError, match="requires MemoryManager"):
        search.invoke({"query": "101"})


def test_memory_search_hits_real_manager(temp_workspace):
    mm = MemoryManager(MemoryConfig(), temp_workspace)
    mm.add_memory(
        content="101: 散户 / 边际接盘流动性（投资黑话）",
        importance_score=0.9,
        keywords=["101", "黑话"],
        metadata={"collection": "jargon"},
    )
    tm = _tool_manager(mm)
    search = _by_name(tm, "safe_claw_memory_search")
    out = search.invoke({"query": "什么是101"})
    assert "No memories found" not in out
    assert "散户" in out or "101" in out
    assert "Memory search results for:" not in out  # old stub


def test_memory_write_and_search_roundtrip(temp_workspace):
    mm = MemoryManager(MemoryConfig(), temp_workspace)
    tm = _tool_manager(mm)
    write = _by_name(tm, "safe_claw_memory_write")
    search = _by_name(tm, "safe_claw_memory_search")

    wrote = write.invoke(
        {
            "content": "User prefers Maple font in Cursor",
            "importance": 0.8,
            "keywords": "font,cursor",
        }
    )
    assert "Remembered" in wrote
    assert mm.get_memory_stats()["total_count"] >= 1

    found = search.invoke({"query": "Maple font"})
    assert "Maple" in found


def test_memory_write_rejects_empty(temp_workspace):
    mm = MemoryManager(MemoryConfig(), temp_workspace)
    tm = _tool_manager(mm)
    write = _by_name(tm, "safe_claw_memory_write")
    with pytest.raises(ValueError, match="non-empty content"):
        write.invoke({"content": "   "})


def test_policy_strips_memory_write_when_auto_write_off(temp_workspace):
    mm = MemoryManager(MemoryConfig(), temp_workspace)
    tm = _tool_manager(mm)
    names = {
        getattr(t, "name", "")
        for t in tm.get_tools_for_policy(
            skill_execute="off",
            allow_create=False,
            allow_edit=False,
            memory_auto_write=False,
        )
    }
    assert "safe_claw_memory_search" in names
    assert "safe_claw_memory_write" not in names
    assert "safe_claw_file_write" not in names


def test_policy_keeps_memory_write_when_auto_write_on(temp_workspace):
    mm = MemoryManager(MemoryConfig(), temp_workspace)
    tm = _tool_manager(mm)
    names = {
        getattr(t, "name", "")
        for t in tm.get_tools_for_policy(
            skill_execute="full",
            allow_create=True,
            allow_edit=True,
            memory_auto_write=True,
        )
    }
    assert "safe_claw_memory_search" in names
    assert "safe_claw_memory_write" in names
