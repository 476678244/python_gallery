"""Hard gate tests for spawn brief — docs/features/sub-agents/acceptance.md A."""

import pytest

from safe_claw.core.deepagents.spawn_brief import (
    ALLOWED_AGENTS,
    parse_brief_from_task_args,
    validate_spawn_brief,
)


def _valid(**overrides):
    base = {
        "step_now": "调研主题 A",
        "look_ahead": ["收集来源", "压缩要点", "交回主线程"],
        "expected_output": "JSON facts",
        "agent_name": "general-purpose",
    }
    base.update(overrides)
    return base


def test_valid_brief_ok():
    b = validate_spawn_brief(_valid())
    assert b.agent_name == "general-purpose"
    assert len(b.look_ahead) == 3


def test_missing_look_ahead_fails():
    with pytest.raises(ValueError, match="look_ahead"):
        validate_spawn_brief(_valid(look_ahead=["only", "two"]))


def test_empty_expected_fails():
    with pytest.raises(ValueError, match="expected_output"):
        validate_spawn_brief(_valid(expected_output="  "))


def test_unknown_agent_fails():
    with pytest.raises(ValueError, match="whitelist"):
        validate_spawn_brief(_valid(agent_name="Bugbot"))


def test_banned_phrase_fails():
    with pytest.raises(ValueError, match="banned"):
        validate_spawn_brief(_valid(step_now="你看着办吧"))


def test_parse_from_nested_brief():
    b = parse_brief_from_task_args(
        {
            "subagent_type": "explore",
            "brief": {
                "step_now": "搜关键词",
                "look_ahead": ["a", "b", "c"],
                "expected_output": "paths[]",
            },
        }
    )
    assert b.agent_name == "explore"
    assert "explore" in ALLOWED_AGENTS


def test_parse_from_json_description():
    import json

    desc = json.dumps(
        {
            "step_now": "一步",
            "look_ahead": ["1", "2", "3"],
            "expected_output": "out",
            "agent_name": "general-purpose",
        },
        ensure_ascii=False,
    )
    b = parse_brief_from_task_args({"description": desc})
    assert b.step_now == "一步"


def test_parse_missing_structured_fails():
    with pytest.raises(ValueError, match="structured brief"):
        parse_brief_from_task_args({"description": "just go do stuff"})
