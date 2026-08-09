"""Hard-gate DeepAgents `task` tool when ModePolicy.spawn disallows it.

DeepAgents always registers SubAgentMiddleware/`task`. Prompt alone is not enough
(Fail Fast). This middleware returns a ToolMessage error instead of running spawn.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from langchain_core.messages import ToolMessage

from safe_claw.core.agent_modes.policy import ModePolicy, spawn_runtime_enabled

logger = logging.getLogger(__name__)

try:
    from deepagents.graph import AgentMiddleware
except ImportError:  # pragma: no cover
    from langchain.agents.middleware.types import AgentMiddleware  # type: ignore


class SpawnGateMiddleware(AgentMiddleware):
    """Block `task` tool calls when mode spawn is off / explore_only (unwired)."""

    def __init__(self, mode_policy: ModePolicy):
        self.mode_policy = mode_policy

    def wrap_tool_call(self, request, handler: Callable[..., Any]):
        if spawn_runtime_enabled(self.mode_policy):
            return handler(request)
        tool_call = getattr(request, "tool_call", None) or {}
        name = (
            tool_call.get("name")
            if isinstance(tool_call, dict)
            else getattr(tool_call, "name", None)
        )
        if name != "task":
            return handler(request)

        tc_id = (
            tool_call.get("id")
            if isinstance(tool_call, dict)
            else getattr(tool_call, "id", None)
        ) or "spawn-blocked"
        err = (
            f"[ModePolicy] spawn/task blocked (Fail Fast)\n"
            f"  mode: {self.mode_policy.mode}\n"
            f"  spawn: {self.mode_policy.spawn}\n"
            f"  Expected: spawn in (on|required) for task tool\n"
            f"  explore_only is not wired — treated as off"
        )
        logger.error(err)
        return ToolMessage(content=err, tool_call_id=tc_id, status="error")

    async def awrap_tool_call(self, request, handler: Callable[..., Any]):
        if spawn_runtime_enabled(self.mode_policy):
            return await handler(request)
        tool_call = getattr(request, "tool_call", None) or {}
        name = (
            tool_call.get("name")
            if isinstance(tool_call, dict)
            else getattr(tool_call, "name", None)
        )
        if name != "task":
            return await handler(request)

        tc_id = (
            tool_call.get("id")
            if isinstance(tool_call, dict)
            else getattr(tool_call, "id", None)
        ) or "spawn-blocked"
        err = (
            f"[ModePolicy] spawn/task blocked (Fail Fast)\n"
            f"  mode: {self.mode_policy.mode}\n"
            f"  spawn: {self.mode_policy.spawn}\n"
            f"  Expected: spawn in (on|required) for task tool\n"
            f"  explore_only is not wired — treated as off"
        )
        logger.error(err)
        return ToolMessage(content=err, tool_call_id=tc_id, status="error")
