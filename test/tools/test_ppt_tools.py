"""Unit tests for PPT tools + ModePolicy ppt (docs/features/ppt-mode)."""

from pathlib import Path

import pytest

from safe_claw.core.agent_modes import resolve_mode_policy, spawn_runtime_enabled
from safe_claw.core.tools.ppt import (
    PPT_TOOL_NAMES,
    PptToolError,
    build_ppt_tools,
    clear_ppt_store,
    probe_preview_engine,
)


@pytest.fixture(autouse=True)
def _clear_store():
    clear_ppt_store()
    yield
    clear_ppt_store()


def _invoke(tool, **kwargs):
    return tool.invoke(kwargs)


def test_ppt_mode_policy():
    p = resolve_mode_policy("ppt")
    assert p.mode == "ppt"
    assert p.allow_create and not p.allow_edit and not p.allow_delete
    assert p.ppt_tools is True
    assert p.observability == "ppt"
    assert p.spawn == "off"
    assert not spawn_runtime_enabled(p)
    assert "Deck Outline" in p.system_prompt_addendum


def test_tools_happy_path_save_preview(tmp_path: Path):
    tools = {t.name: t for t in build_ppt_tools(tmp_path, session_id="s1")}
    assert set(tools) == PPT_TOOL_NAMES

    _invoke(
        tools["safe_claw_ppt_deck_init"],
        deck_id="demo",
        title="Demo Deck",
        theme_id="default",
    )
    _invoke(
        tools["safe_claw_ppt_slide_upsert"],
        deck_id="demo",
        slide_index=1,
        title="Page One",
        bullets="a\nb",
    )
    _invoke(
        tools["safe_claw_ppt_slide_upsert"],
        deck_id="demo",
        slide_index=2,
        title="Page Two",
        bullets="c",
    )
    saved = _invoke(tools["safe_claw_ppt_save_version"], deck_id="demo")
    assert '"version": 1' in saved or '"version":1' in saved.replace(" ", "")
    pptx = tmp_path / "ppt" / "demo_v1.pptx"
    assert pptx.is_file()

    # second save must create v2, never overwrite
    _invoke(
        tools["safe_claw_ppt_slide_upsert"],
        deck_id="demo",
        slide_index=1,
        title="Page One Revised",
        bullets="a",
    )
    saved2 = _invoke(tools["safe_claw_ppt_save_version"], deck_id="demo")
    assert "v2" in saved2 or '"version": 2' in saved2 or '"version":2' in saved2.replace(
        " ", ""
    )
    assert pptx.is_file()
    assert (tmp_path / "ppt" / "demo_v2.pptx").is_file()

    try:
        probe_preview_engine()
    except PptToolError:
        pytest.skip("No preview engine installed")

    previewed = _invoke(tools["safe_claw_ppt_preview"], deck_id="demo", version=2)
    assert "ppt_preview" in previewed
    assert "preview_urls" in previewed
    pngs = list((tmp_path / "ppt" / "previews" / "demo_v2").glob("slide_*.png"))
    assert len(pngs) >= 1


def test_preview_requires_save(tmp_path: Path):
    tools = {t.name: t for t in build_ppt_tools(tmp_path, session_id="s2")}
    _invoke(tools["safe_claw_ppt_deck_init"], deck_id="x", title="X")
    _invoke(
        tools["safe_claw_ppt_slide_upsert"],
        deck_id="x",
        slide_index=1,
        title="Only",
        bullets="1",
    )
    with pytest.raises(Exception, match="unsaved|save_version"):
        _invoke(tools["safe_claw_ppt_preview"], deck_id="x")


def test_cannot_remove_last_slide(tmp_path: Path):
    tools = {t.name: t for t in build_ppt_tools(tmp_path, session_id="s3")}
    _invoke(tools["safe_claw_ppt_deck_init"], deck_id="solo", title="Solo")
    _invoke(
        tools["safe_claw_ppt_slide_upsert"],
        deck_id="solo",
        slide_index=1,
        title="Only",
        bullets="1",
    )
    with pytest.raises(Exception, match="last slide"):
        _invoke(tools["safe_claw_ppt_slide_remove"], deck_id="solo", slide_index=1)


def test_path_escape_image(tmp_path: Path):
    tools = {t.name: t for t in build_ppt_tools(tmp_path, session_id="s4")}
    _invoke(tools["safe_claw_ppt_deck_init"], deck_id="img", title="Img")
    _invoke(
        tools["safe_claw_ppt_slide_upsert"],
        deck_id="img",
        slide_index=1,
        title="T",
        bullets="1",
    )
    with pytest.raises(Exception, match="escapes|not found|Image"):
        _invoke(
            tools["safe_claw_ppt_image_place"],
            deck_id="img",
            slide_index=1,
            workspace_rel_path="../outside.png",
        )


def test_toolmanager_ppt_only_when_flag(tmp_path: Path, monkeypatch):
    from safe_claw.core.skills import SkillDiscovery, SkillExecutor, SkillScanner
    from safe_claw.core.tools.manager import ToolManager

    scanner = SkillScanner()
    discovery = SkillDiscovery(scanner)
    executor = SkillExecutor(discovery)
    tm = ToolManager(scanner, discovery, executor)

    no_ppt = tm.get_tools_for_policy(
        skill_execute="full",
        allow_create=True,
        allow_edit=True,
        memory_auto_write=True,
        ppt_tools=False,
    )
    names = {getattr(t, "name", "") for t in no_ppt}
    assert not (names & PPT_TOOL_NAMES)

    with_ppt = tm.get_tools_for_policy(
        skill_execute="restrained",
        allow_create=True,
        allow_edit=False,
        memory_auto_write=False,
        ppt_tools=True,
        workspace_dir=tmp_path,
        session_id="tm",
    )
    names2 = {getattr(t, "name", "") for t in with_ppt}
    assert PPT_TOOL_NAMES <= names2
