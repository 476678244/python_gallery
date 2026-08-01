"""Fixtures for SafeClaw FastAPI contract tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Explicit mock LLM only for unit/API tests — never silent product fallback.
os.environ.setdefault("SAFECLAW_ALLOW_MOCK_LLM", "1")

# Ensure repo root is importable
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture()
def tmp_data_dirs(tmp_path, monkeypatch):
    """Isolate WORKSPACE_DIR / DATA_DIR away from ~/Downloads."""
    workspace = tmp_path / "workspace"
    data = tmp_path / "Data"
    workspace.mkdir()
    data.mkdir()

    import api.main as api_main

    monkeypatch.setattr(api_main, "WORKSPACE_DIR", workspace)
    monkeypatch.setattr(api_main, "DATA_DIR", data)
    monkeypatch.setattr(api_main, "SESSIONS_FILE", data / "sessions.json")
    monkeypatch.setattr(api_main, "MESSAGES_DIR", data / "messages")
    monkeypatch.setattr(api_main, "LLM_CONFIG_FILE", data / "llm_config.json")
    monkeypatch.setattr(api_main, "AGENT_CONFIG_FILE", data / "agent_config.json")
    # Isolate legacy migrate path so host skill_tree_state.json cannot leak into tests.
    monkeypatch.setattr(api_main, "_LEGACY_SKILL_TREE_STATE_FILE", data / "skill_tree_state.json")
    monkeypatch.setattr(api_main, "_DATA_DIR", data)
    monkeypatch.setattr(api_main, "_folder_enabled", {})
    # Reset global model to product default (DeepSeek); do not inherit host agent_config.
    monkeypatch.setattr(api_main, "_selected_model", api_main.DEFAULT_MODEL)
    # Force SkillsManager re-init against isolated AGENT_CONFIG_FILE (not host SoT).
    monkeypatch.setattr(api_main, "skills_manager", None)
    # Clear in-memory session list without replacing the binding used by endpoints
    api_main.SESSIONS.clear()

    (data / "messages").mkdir(exist_ok=True)
    return {"workspace": workspace, "data": data}


@pytest.fixture()
def client(tmp_data_dirs, monkeypatch):
    """TestClient bound to isolated data dirs + fresh MemoryManager."""
    import api.main as api_main
    from api.main import app
    from safe_claw.core.memory.manager import MemoryManager
    from safe_claw.models.config import MemoryConfig

    api_main.memory_manager = MemoryManager(
        config=MemoryConfig(),
        workspace_path=str(tmp_data_dirs["workspace"]),
    )
    api_main.safe_claw_loaded = True

    with TestClient(app) as c:
        yield c
