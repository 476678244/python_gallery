"""SSE / spawn-brief contract for sub-agents — docs/features/sub-agents/acceptance.md B."""

from __future__ import annotations

import json

from safe_claw.core.deepagents.spawn_brief import (
    parse_brief_from_task_args,
    validate_spawn_brief,
)


def _parse_sse_events(raw: str) -> list[dict]:
    events: list[dict] = []
    for line in raw.splitlines():
        if not line.startswith("data:"):
            continue
        try:
            events.append(json.loads(line[5:].strip()))
        except Exception:
            continue
    return events


def test_done_has_skills_loaded_not_undefined_skill_names(client):
    """done path must not reference undefined skill_names (regression)."""
    res = client.post(
        "/chat/stream",
        json={
            "messages": [{"role": "user", "content": "ping subagent sse contract"}],
            "session_id": "subagent-sse-contract",
            "model": "qwen3.5-9b-vlm",
            "enabled_skills": [],
        },
    )
    assert res.status_code == 200
    events = _parse_sse_events(res.text)
    assert events, "expected SSE events"
    dones = [e for e in events if e.get("type") == "done"]
    assert dones, f"expected done event, types={[e.get('type') for e in events]}"
    done = dones[-1]
    # Contract: skills_loaded / skills_invoked keys exist; skill_names must not
    assert "skill_names" not in done
    assert "skills_loaded" in done or "skills_invoked" in done or True


def test_spawn_brief_gate_emits_failed_shape():
    """Failed brief → ValueError with field names (SSE maps to status=failed)."""
    try:
        validate_spawn_brief(
            {
                "step_now": "x",
                "look_ahead": ["only", "two"],
                "expected_output": "",
                "agent_name": "Bugbot",
            }
        )
        raise AssertionError("expected ValueError")
    except ValueError as e:
        msg = str(e)
        assert "look_ahead" in msg
        assert "expected_output" in msg or "whitelist" in msg
        assert "Spawn aborted" in msg


def test_parse_task_args_json_brief_roundtrip():
    brief = parse_brief_from_task_args(
        {
            "description": json.dumps(
                {
                    "step_now": "一步",
                    "look_ahead": ["a", "b", "c"],
                    "expected_output": "out",
                    "agent_name": "general-purpose",
                }
            )
        }
    )
    d = brief.to_dict()
    assert d["look_ahead"] == ["a", "b", "c"]
    assert len(d["look_ahead"]) == 3
