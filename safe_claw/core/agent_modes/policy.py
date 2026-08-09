"""ModePolicy — hard gates for agent session modes (Fail Fast).

SoT: docs/features/agent-modes/methodology.md + docs/features/ppt-mode/methodology.md
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Literal, Optional

AgentMode = Literal["ask", "agent", "plan", "safe", "debug", "subagent", "ppt"]

EXECUTION_MODES: FrozenSet[str] = frozenset(
    {"ask", "agent", "plan", "safe", "debug", "subagent", "ppt"}
)

SkillExecute = Literal["off", "restrained", "full"]
SpawnPolicy = Literal["off", "explore_only", "on", "required"]
ObservabilityPack = Literal["default", "full", "subagent", "ppt"]


class ModePolicyError(ValueError):
    """Invalid mode for /chat/stream (Fail Fast)."""


@dataclass(frozen=True)
class ModePolicy:
    mode: AgentMode
    allow_read: bool
    allow_create: bool
    allow_edit: bool
    allow_delete: bool
    skill_execute: SkillExecute
    memory_auto_write: bool
    spawn: SpawnPolicy
    observability: ObservabilityPack
    system_prompt_addendum: str
    ppt_tools: bool = False

    @property
    def allow_write(self) -> bool:
        """FS backend allow_write: True if create and/or edit permitted."""
        return self.allow_create or self.allow_edit


_ADDENDA = {
    "ask": (
        "\n\n## AGENT MODE: ask\n"
        "You are in read-only Ask mode. Answer and explain only. "
        "Do not write, edit, delete files, execute skills that mutate the workspace, "
        "or spawn subagents / call the task tool. Tools for mutation are not available.\n"
    ),
    "plan": (
        "\n\n## AGENT MODE: plan\n"
        "You are in Plan mode (read-only). Produce a structured plan only — do not modify files.\n"
        "Do not spawn subagents or call the task tool unless the product explicitly enables "
        "explore-only spawn; prefer planning without delegation.\n"
        "Format your reply with:\n"
        "### Plan\n"
        "1. ...\n"
        "2. ...\n"
        "### Risks\n"
        "- ...\n"
        "### Pending confirmation\n"
        "- ...\n"
        "Do not switch to agent or write files unless the user explicitly changes mode.\n"
    ),
    "safe": (
        "\n\n## AGENT MODE: safe\n"
        "Restrained write mode: you may CREATE new files only. "
        "Updating/editing existing files, overwrite, delete, and remove are FORBIDDEN "
        "and will fail at the tool/FS gate. Prefer new paths under the workspace. "
        "Do not spawn subagents or call the task tool in safe mode.\n"
    ),
    "agent": (
        "\n\n## AGENT MODE: agent\n"
        "Full agent capabilities (current default behavior).\n"
    ),
    "debug": (
        "\n\n## AGENT MODE: debug\n"
        "Full agent tools. Observability Full pack is forced in the UI "
        "(Exec, Prompt Inspect, Skills, nested steps). Be explicit about tools and failures.\n"
    ),
    "subagent": (
        "\n\n## AGENT MODE: subagent\n"
        "Full agent tools with subagent spawn enabled. "
        "Prefer legitimate task/spawn with look-ahead brief when isolation helps. "
        "Subagent Observability pack is forced in the UI. "
        "Spawn brief hard-gates still apply — do not skip required fields.\n"
    ),
    "ppt": (
        "\n\n## AGENT MODE: ppt\n"
        "PPT authoring mode. Prefer safe_claw_ppt_* tools for structure, save, and preview.\n"
        "Do NOT hand-craft pptx via raw file_write. Do not spawn / call the task tool.\n"
        "Unless the user says 直接出稿 / generate now, first reply with exact H3 titles "
        "(suffix after the title is OK, e.g. ### Deck Outline（共4页）):\n"
        "### Deck Outline\n...\n"
        "### Slide Storyboard\n"
        "(prefer numbered list per slide: title + bullets + visual; tables OK)\n"
        "### Pending confirmation\n...\n"
        "Do NOT claim DingTalk/钉钉 upload — only local workspace pptx path.\n"
        "For ~2-minute kid talks prefer ≤5 slides.\n"
        "After confirm: deck_init → slide_upsert* → save_version → preview.\n"
        "On [PPT_STEER]: apply precise slide/theme changes, save a NEW version, preview again.\n"
        "Filesystem is create-only; versions are _vN.pptx (never overwrite).\n"
    ),
}


def spawn_runtime_enabled(policy: ModePolicy) -> bool:
    """Whether DeepAgents `task` may run under this policy.

    Contract: only ``on`` / ``required`` execute. ``explore_only`` is reserved
    (plan) and treated as off until explore-only spawn is wired.
    """
    return policy.spawn in ("on", "required")


def validate_chat_mode(mode: Optional[str]) -> AgentMode:
    """Validate mode for POST /chat/stream.

    None/empty → agent. \"loop\" and unknown → ModePolicyError (HTTP 400).
    """
    if mode is None or (isinstance(mode, str) and not mode.strip()):
        return "agent"
    key = mode.strip().lower()
    if key == "loop":
        raise ModePolicyError(
            "[ModePolicy] mode=loop is not valid on /chat/stream\n"
            "  Loop is a scheduler; ticks must send the session execution mode "
            "(ask|agent|plan|safe|debug|subagent|ppt).\n"
            f"  Actual: {mode!r}"
        )
    if key not in EXECUTION_MODES:
        raise ModePolicyError(
            "[ModePolicy] Invalid agent mode\n"
            f"  Expected: one of {sorted(EXECUTION_MODES)}\n"
            f"  Actual: {mode!r}"
        )
    return key  # type: ignore[return-value]


def resolve_mode_policy(mode: Optional[str]) -> ModePolicy:
    """Resolve ModePolicy from optional mode string (defaults to agent)."""
    m = validate_chat_mode(mode)

    if m in ("ask", "plan"):
        return ModePolicy(
            mode=m,
            allow_read=True,
            allow_create=False,
            allow_edit=False,
            allow_delete=False,
            skill_execute="off",
            memory_auto_write=False,
            spawn="explore_only" if m == "plan" else "off",
            observability="default",
            system_prompt_addendum=_ADDENDA[m],
            ppt_tools=False,
        )
    if m == "safe":
        return ModePolicy(
            mode="safe",
            allow_read=True,
            allow_create=True,
            allow_edit=False,
            allow_delete=False,
            skill_execute="restrained",
            memory_auto_write=False,
            spawn="off",
            observability="default",
            system_prompt_addendum=_ADDENDA["safe"],
            ppt_tools=False,
        )
    if m == "ppt":
        return ModePolicy(
            mode="ppt",
            allow_read=True,
            allow_create=True,
            allow_edit=False,
            allow_delete=False,
            skill_execute="restrained",
            memory_auto_write=False,
            spawn="off",
            observability="ppt",
            system_prompt_addendum=_ADDENDA["ppt"],
            ppt_tools=True,
        )
    if m == "debug":
        return ModePolicy(
            mode="debug",
            allow_read=True,
            allow_create=True,
            allow_edit=True,
            allow_delete=True,
            skill_execute="full",
            memory_auto_write=True,
            spawn="on",
            observability="full",
            system_prompt_addendum=_ADDENDA["debug"],
            ppt_tools=False,
        )
    if m == "subagent":
        return ModePolicy(
            mode="subagent",
            allow_read=True,
            allow_create=True,
            allow_edit=True,
            allow_delete=True,
            skill_execute="full",
            memory_auto_write=True,
            spawn="required",
            observability="subagent",
            system_prompt_addendum=_ADDENDA["subagent"],
            ppt_tools=False,
        )
    # agent
    return ModePolicy(
        mode="agent",
        allow_read=True,
        allow_create=True,
        allow_edit=True,
        allow_delete=True,
        skill_execute="full",
        memory_auto_write=True,
        spawn="on",
        observability="default",
        system_prompt_addendum=_ADDENDA["agent"],
        ppt_tools=False,
    )
