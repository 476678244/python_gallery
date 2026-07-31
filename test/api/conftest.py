"""Fixtures for SafeClaw FastAPI contract tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

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
    monkeypatch.setattr(api_main, "_DATA_DIR", data)
    monkeypatch.setattr(api_main, "_folder_enabled", {})
    # Clear in-memory session list without replacing the binding used by endpoints
    api_main.SESSIONS.clear()

    (data / "messages").mkdir(exist_ok=True)
    return {"workspace": workspace, "data": data}


@pytest.fixture()
def client(tmp_data_dirs):
    """TestClient bound to isolated data dirs."""
    from api.main import app

    with TestClient(app) as c:
        yield c
