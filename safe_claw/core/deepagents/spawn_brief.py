"""Spawn brief hard gate — 走一步看三步 (Fail Fast).

SoT: docs/features/sub-agents/methodology.md
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

ALLOWED_AGENTS = frozenset({"general-purpose", "explore"})

_BANNED_PHRASES = (
    "你看着办",
    "随便",
    "看着办",
    "whatever",
    "you decide",
)


@dataclass(frozen=True)
class SpawnBrief:
    step_now: str
    look_ahead: tuple[str, str, str]
    expected_output: str
    agent_name: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_now": self.step_now,
            "look_ahead": list(self.look_ahead),
            "expected_output": self.expected_output,
            "agent_name": self.agent_name,
        }


def validate_spawn_brief(payload: Mapping[str, Any] | None) -> SpawnBrief:
    """Validate spawn brief. Missing/invalid fields → ValueError (Fail Fast)."""
    if not payload or not isinstance(payload, Mapping):
        raise ValueError(
            "[spawn_brief] Rejected (Fail Fast)\n"
            "  Missing: entire brief payload\n"
            "  Expected keys: step_now, look_ahead[3], expected_output, agent_name"
        )

    missing: list[str] = []
    step_now = _as_nonempty_str(payload.get("step_now"), "step_now", missing)
    expected_output = _as_nonempty_str(
        payload.get("expected_output"), "expected_output", missing
    )
    agent_name = _as_nonempty_str(payload.get("agent_name"), "agent_name", missing)
    look_ahead = _as_look_ahead(payload.get("look_ahead"), missing)

    if agent_name and agent_name not in ALLOWED_AGENTS:
        missing.append(
            f"agent_name not in whitelist {sorted(ALLOWED_AGENTS)} (got {agent_name!r})"
        )

    for label, text in (
        ("step_now", step_now),
        ("expected_output", expected_output),
        *((f"look_ahead[{i}]", look_ahead[i] if look_ahead else None) for i in range(3)),
    ):
        if text and _is_banned(text):
            missing.append(f"{label} contains banned empty-talk phrase")

    if missing:
        raise ValueError(
            "[spawn_brief] Rejected (Fail Fast)\n"
            + "\n".join(f"  Missing/invalid: {m}" for m in missing)
            + "\n  Spawn aborted — subagent not started"
        )

    assert step_now and expected_output and agent_name and look_ahead
    return SpawnBrief(
        step_now=step_now,
        look_ahead=look_ahead,
        expected_output=expected_output,
        agent_name=agent_name,
    )


def parse_brief_from_task_args(tool_args: Mapping[str, Any] | None) -> SpawnBrief:
    """Extract brief from DeepAgents task tool args (JSON description or nested brief)."""
    if not tool_args:
        raise ValueError(
            "[spawn_brief] Rejected (Fail Fast)\n"
            "  Missing: task tool arguments\n"
            "  Spawn aborted — subagent not started"
        )

    if isinstance(tool_args.get("brief"), Mapping):
        brief_map = dict(tool_args["brief"])
        if "agent_name" not in brief_map and tool_args.get("subagent_type"):
            brief_map["agent_name"] = tool_args["subagent_type"]
        return validate_spawn_brief(brief_map)

    # Flat fields on the tool call
    flat = {
        "step_now": tool_args.get("step_now"),
        "look_ahead": tool_args.get("look_ahead"),
        "expected_output": tool_args.get("expected_output"),
        "agent_name": tool_args.get("agent_name")
        or tool_args.get("subagent_type")
        or "general-purpose",
    }
    if flat["step_now"] and flat["look_ahead"] and flat["expected_output"]:
        return validate_spawn_brief(flat)

    # Description may be a JSON object string
    desc = tool_args.get("description") or tool_args.get("prompt") or tool_args.get("task")
    if isinstance(desc, str) and desc.strip().startswith("{"):
        import json

        try:
            data = json.loads(desc)
        except json.JSONDecodeError as e:
            raise ValueError(
                "[spawn_brief] Rejected (Fail Fast)\n"
                f"  Invalid: description is not valid JSON brief ({e})\n"
                "  Spawn aborted — subagent not started"
            ) from e
        if isinstance(data, Mapping):
            if "agent_name" not in data and tool_args.get("subagent_type"):
                data = {**data, "agent_name": tool_args["subagent_type"]}
            return validate_spawn_brief(data)

    raise ValueError(
        "[spawn_brief] Rejected (Fail Fast)\n"
        "  Missing: structured brief (step_now, look_ahead[3], expected_output, agent_name)\n"
        "  Hint: pass brief{} or JSON description with those keys\n"
        "  Spawn aborted — subagent not started"
    )


def _as_nonempty_str(value: Any, field: str, missing: list[str]) -> str | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        missing.append(field)
        return None
    if not isinstance(value, str):
        missing.append(f"{field} must be str")
        return None
    return value.strip()


def _as_look_ahead(
    value: Any, missing: list[str]
) -> tuple[str, str, str] | None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        missing.append("look_ahead must be a list of exactly 3 non-empty strings")
        return None
    items = list(value)
    if len(items) != 3:
        missing.append(
            f"look_ahead must have exactly 3 non-empty items (got {len(items)})"
        )
        return None
    out: list[str] = []
    for i, item in enumerate(items):
        if not isinstance(item, str) or not item.strip():
            missing.append(f"look_ahead[{i}] empty")
            return None
        out.append(item.strip())
    return out[0], out[1], out[2]


def _is_banned(text: str) -> bool:
    lower = text.lower()
    return any(p.lower() in lower for p in _BANNED_PHRASES)
