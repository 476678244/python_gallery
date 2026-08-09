"""
SafeClaw FastAPI Backend
Bridges Next.js UI with SafeClaw Python Core
"""

import asyncio
import json
import logging
import sys
import os
import re
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Dict, Any, Optional, Union
from datetime import datetime
from pathlib import Path

# --- Realtime log capture -------------------------------------------------
# Tee stdout/stderr into logs/server.log so ALL backend output (prints,
# uvicorn default/error logs, app logs) is tailable in realtime, regardless
# of how the server is launched (PyCharm, `python start_api.py`, scripts...).
class _Tee:
    def __init__(self, primary, *streams):
        # primary is the real stdout/stderr; attribute lookups delegate to it
        self._primary = primary
        self._streams = (primary, *streams)

    def write(self, data):
        for s in self._streams:
            try:
                s.write(data)
                s.flush()
            except Exception:
                pass
        return len(data)

    def flush(self):
        for s in self._streams:
            try:
                s.flush()
            except Exception:
                pass

    def isatty(self):
        try:
            return self._primary.isatty()
        except Exception:
            return False

    def fileno(self):
        return self._primary.fileno()

    def __getattr__(self, name):
        # Delegate everything else (encoding, writable, etc.) to the real stream
        return getattr(self._primary, name)


_LOG_DIR = Path(__file__).parent.parent / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_SERVER_LOG = open(_LOG_DIR / "server.log", "a", buffering=1, encoding="utf-8")
sys.stdout = _Tee(sys.__stdout__, _SERVER_LOG)
sys.stderr = _Tee(sys.__stderr__, _SERVER_LOG)

# Configure logging to output to stdout (now tee'd into server.log)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

import httpx

# LM Studio endpoint (override via env or runtime via /settings/llm).
# Local IP must bypass proxy -> trust_env=False on httpx clients.
LM_STUDIO_BASE_URL = os.environ.get("LM_STUDIO_BASE_URL", "http://192.168.1.100:1234/v1")


def _lm_studio_models_url() -> str:
    """Derive the /models URL from the current base URL."""
    return LM_STUDIO_BASE_URL.rstrip("/") + "/models"

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add safe_claw to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# SafeClaw imports (lazy loaded to avoid startup overhead)
safe_claw_loaded = False
chat_agent = None
llm_service = None
skills_manager = None
memory_manager = None


def load_safe_claw():
    """Lazy load SafeClaw components"""
    global safe_claw_loaded, chat_agent, llm_service, skills_manager, memory_manager

    if safe_claw_loaded:
        return

    # Ensure python_gallery root is on sys.path
    pkg_root = str(Path(__file__).parent.parent.parent)
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)

    try:
        from safe_claw.services.llm_gateway import LLMService
        from safe_claw.core.agents.chat_agent import ChatAgent
        from safe_claw.core.skills.manager import SkillsManager
        from safe_claw.core.memory.manager import MemoryManager
        from safe_claw.models.config import LLMConfig, MemoryConfig

        # Init LLM from real global selection — never mock-key (Fail Fast).
        if _selected_model.startswith("deepseek"):
            if not DEEPSEEK_API_KEY:
                raise ValueError(
                    "[load_safe_claw] DeepSeek selected but API key missing (Fail Fast)"
                )
            llm_config = LLMConfig(
                provider="deepseek",
                model=_selected_model,
                api_key=DEEPSEEK_API_KEY,
                base_url=None,
                temperature=0.7,
                max_tokens=2000,
            )
        else:
            llm_config = LLMConfig(
                provider="openai",
                model=_selected_model,
                api_key="lm-studio",
                base_url=LM_STUDIO_BASE_URL,
                temperature=0.7,
                max_tokens=2000,
            )
        llm_service = LLMService(config=llm_config)
        if not skills_manager:
            skills_manager = SkillsManager()
            if not skills_manager.skill_scanner.loaded:
                skills_manager.skill_scanner.scan_all_skills()
            _load_skill_tree_state(skills_manager)
        memory_manager = MemoryManager(
            config=MemoryConfig(),
            workspace_path=str(WORKSPACE_DIR),
        )
        chat_agent = ChatAgent(
            llm_service=llm_service,
            config={"personality": "helpful_assistant", "max_response_length": 4000},
        )

        safe_claw_loaded = True
        print("✅ SafeClaw loaded successfully")

    except Exception as e:
        safe_claw_loaded = False
        raise RuntimeError(f"[load_safe_claw] Failed (Fail Fast): {e}") from e


# Pydantic models
class ChatMessage(BaseModel):
    role: str
    # content is either plain text or a multimodal array of parts
    # (e.g. [{"type": "text", "text": ...}, {"type": "image_url", "image_url": {"url": ...}}])
    content: Union[str, List[Dict[str, Any]]]

    def text(self) -> str:
        """Extract the plain-text portion of the message content."""
        if isinstance(self.content, str):
            return self.content
        parts = []
        for part in self.content:
            if isinstance(part, dict) and part.get("type") == "text":
                parts.append(part.get("text", ""))
        return " ".join(parts)


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    session_id: Optional[str] = None
    enabled_skills: List[str] = Field(default_factory=list)
    # None → use globally selected model from agent_config.json
    model: Optional[str] = None
    temperature: float = 0.7
    stream: bool = True
    # Agent execution mode (ask|agent|plan|safe|debug|subagent|ppt). None → agent.
    # loop is invalid here (scheduler only) → 400.
    mode: Optional[str] = None


class SessionCreateRequest(BaseModel):
    title: Optional[str] = "New Chat"
    # None → use globally selected model; do NOT hardcode Qwen here or it
    # overrides agent_config.json (e.g. DeepSeek) on every New Chat.
    model: Optional[str] = None


class SessionUpdateRequest(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class SkillToggleRequest(BaseModel):
    skill_id: Optional[str] = None
    folder_id: Optional[str] = None
    enabled: bool = True


# ── Skills tree builder using safe_claw SkillsManager ────────────────────────

_DATA_DIR = Path.home() / "Downloads" / "safe_claw_worksapce" / "Data"
_DATA_DIR.mkdir(parents=True, exist_ok=True)
AGENT_CONFIG_FILE = _DATA_DIR / "agent_config.json"
_LEGACY_SKILL_TREE_STATE_FILE = _DATA_DIR / "skill_tree_state.json"

# Product / cold-start default: DeepSeek is the global default model selection.
DEFAULT_MODEL = "deepseek-v4-flash"
# Globally selected agent model, persisted in agent_config.json.
_selected_model: str = DEFAULT_MODEL

def _get_skills_manager() -> Any:
    """Get or lazily init the SkillsManager. Fail Fast — never return None."""
    global skills_manager
    if skills_manager:
        return skills_manager
    # Ensure python_gallery root is on sys.path (same as load_safe_claw)
    pkg_root = str(Path(__file__).parent.parent.parent)
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)
    try:
        from safe_claw.core.skills.manager import SkillsManager as SM
        skills_manager = SM()
        if not skills_manager.skill_scanner.loaded:
            skills_manager.skill_scanner.scan_all_skills()
        print(f"✅ SkillsManager loaded: {skills_manager.get_skill_count()} skills")
        _load_skill_tree_state(skills_manager)
    except Exception as e:
        skills_manager = None
        raise RuntimeError(
            f"[SkillsManager] init failed (Fail Fast)\n"
            f"  Error: {e}"
        ) from e
    return skills_manager


def _require_skills_manager() -> Any:
    """HTTP-facing SoT accessor — 503 when SkillsManager cannot load."""
    try:
        return _get_skills_manager()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


# In-memory folder toggle state (skills use SkillsManager.set_enabled_skills)
_folder_enabled: Dict[str, bool] = {}


def _skill_collection_id(skill_path: Path, project_root: Path) -> str:
    """Derive collection id exactly as build_skill_tree (strict, no substring)."""
    try:
        rel = skill_path.relative_to(project_root)
        parts = rel.parts
        if parts[0] == "linked_skills" and len(parts) >= 3:
            return f"linked/{parts[1]}"
        if "private_skills" in parts:
            return "private"
        if len(parts) >= 2:
            return parts[0]
        return "other"
    except ValueError:
        raw = str(skill_path)
        if "linked_skills" in raw:
            idx = raw.find("linked_skills")
            rest = raw[idx:].split("/")
            return f"linked/{rest[1]}" if len(rest) > 1 else "linked"
        if "private_skills" in raw:
            return "private"
        return "other"


def _enabled_skills_mutable(sm: Any) -> set:
    """Current enabled set for toggle mutations — never soft-reset empty → all."""
    state = sm.get_enabled_skills_state()
    if state is None:
        return set(sm.get_available_skills())
    return set(state)


def _save_agent_config(sm: Any) -> None:
    """Persist agent config (enabled skills, folder toggles, model) to disk. Fail Fast."""
    config = {
        "model": _selected_model,
        "enabled_skills": list(sm.get_enabled_skills_state() or []) if sm else [],
        "folder_enabled": _folder_enabled,
    }
    try:
        AGENT_CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")
    except Exception as e:
        raise RuntimeError(
            f"[agent_config] Failed to save\n"
            f"  Path: {AGENT_CONFIG_FILE}\n"
            f"  Error: {e}"
        ) from e


# Backwards-compatible alias
_save_skill_tree_state = _save_agent_config


def _load_agent_config(sm: Any) -> None:
    """Load persisted agent config from disk into SkillsManager and globals."""
    global _folder_enabled, _selected_model
    # Migrate legacy skill_tree_state.json -> agent_config.json on first load.
    config_file = AGENT_CONFIG_FILE
    if not config_file.exists():
        if _LEGACY_SKILL_TREE_STATE_FILE.exists():
            config_file = _LEGACY_SKILL_TREE_STATE_FILE
            print(f"ℹ️  Migrating legacy {config_file.name} -> {AGENT_CONFIG_FILE.name}")
        else:
            return
    try:
        config = json.loads(config_file.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(
            f"[agent_config] Corrupt or unreadable config (Fail Fast)\n"
            f"  Path: {config_file}\n"
            f"  Error: {e}"
        ) from e

    try:
        model = config.get("model")
        if not isinstance(model, str) or not model.strip():
            # Legacy skill_tree_state.json never stored model — migrate with DEFAULT_MODEL.
            if config_file is _LEGACY_SKILL_TREE_STATE_FILE:
                model = DEFAULT_MODEL
                print(
                    f"ℹ️  Legacy {config_file.name} has no model; "
                    f"migrating with DEFAULT_MODEL={model}"
                )
            else:
                raise ValueError(
                    f"[agent_config] Missing non-empty 'model' (Fail Fast)\n"
                    f"  Path: {config_file}\n"
                    f"  Actual: {config.get('model')!r}"
                )
        _selected_model = model.strip()
        print(f"✅ Restored selected model: {_selected_model}")
        enabled_skills = config.get("enabled_skills")
        if enabled_skills is not None and sm:
            sm.set_enabled_skills(enabled_skills)
            print(f"✅ Restored {len(enabled_skills)} enabled skills from {config_file.name}")
        folder_state = config.get("folder_enabled")
        if folder_state:
            _folder_enabled.update(folder_state)
            print(f"✅ Restored {len(folder_state)} folder toggle states")
        # Write migrated config to the new file once the SkillsManager is available
        # (avoid clobbering enabled_skills when sm is None at startup).
        if config_file is _LEGACY_SKILL_TREE_STATE_FILE and sm:
            _save_agent_config(sm)
    except Exception:
        raise


# Backwards-compatible alias
_load_skill_tree_state = _load_agent_config

# Load persisted model selection at startup (skills loaded later on SM init).
_load_agent_config(None)


def build_skill_tree() -> List[Dict[str, Any]]:
    """Build skill tree from SkillsManager.skill_scanner.index. Fail Fast if SM missing."""
    sm = _get_skills_manager()

    # Get enabled skill names from manager state
    enabled_skills = sm.get_enabled_skills()
    enabled_set = set(enabled_skills)

    # Group index entries by collection (derived from path)
    project_root = Path(__file__).parent.parent  # python_gallery
    collections: Dict[str, List[Dict]] = {}

    for entry in sm.skill_scanner.index.values():
        skill_path = Path(entry.path)
        collection_id = _skill_collection_id(skill_path, project_root)
        if collection_id == "private":
            collection_label = "Private Skills"
        elif collection_id.startswith("linked/"):
            label_src = collection_id.split("/", 1)[1]
            collection_label = label_src.replace("_", " ").replace("-", " ").title()
        else:
            collection_label = collection_id.replace("_", " ").title()

        skill_id = entry.name
        node = {
            "id": skill_id,
            "name": entry.name,
            "path": entry.path,
            "is_folder": False,
            "enabled": skill_id in enabled_set,
            "expanded": False,
            "children": [],
            "skill_entry": {
                "name": entry.name,
                "description": entry.description,
                "category": entry.category or "",
                "tags": entry.tags or [],
                "aliases": entry.aliases or [],
                "user_invocable": entry.user_invocable,
                "auto_trigger": entry.auto_trigger,
            },
        }
        if collection_id not in collections:
            collections[collection_id] = {"label": collection_label, "skills": []}
        collections[collection_id]["skills"].append(node)

    # Sort skills within each collection
    tree = []
    for cid, data in sorted(collections.items()):
        skills = sorted(data["skills"], key=lambda x: x["name"])
        tree.append({
            "id": cid,
            "name": data["label"],
            "path": cid,
            "is_folder": True,
            "enabled": _folder_enabled.get(cid, True),
            "expanded": cid == "private",
            "children": skills,
        })
    return tree

# ── File-backed session + message storage ────────────────────────────────────

WORKSPACE_DIR = Path.home() / "Downloads" / "safe_claw_worksapce" / "workspace"
DATA_DIR = Path.home() / "Downloads" / "safe_claw_worksapce" / "Data"
SESSIONS_FILE = DATA_DIR / "sessions.json"
MESSAGES_DIR = DATA_DIR / "messages"
LLM_CONFIG_FILE = DATA_DIR / "llm_config.json"
# Secrets file lives OUTSIDE the project tree so it is never committed.
SECRETS_FILE = Path.home() / ".safeclaw_secrets.json"
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
MESSAGES_DIR.mkdir(parents=True, exist_ok=True)


# DeepSeek API key (loaded from ~/.safeclaw_secrets.json, never committed)
DEEPSEEK_API_KEY: Optional[str] = os.environ.get("DEEPSEEK_API_KEY")


def _load_secrets() -> None:
    """Load API keys from the local secrets file (~/.safeclaw_secrets.json). Fail Fast on corrupt file."""
    global DEEPSEEK_API_KEY
    if not SECRETS_FILE.exists():
        return
    try:
        data = json.loads(SECRETS_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(
            f"[secrets] Corrupt secrets file (Fail Fast)\n"
            f"  Path: {SECRETS_FILE}\n"
            f"  Error: {e}"
        ) from e
    key = data.get("deepseek_api_key")
    if key:
        DEEPSEEK_API_KEY = key
        logger.info("Loaded DeepSeek API key from secrets file.")


def _save_secrets() -> None:
    """Persist API keys to the local secrets file (mode 600)."""
    data: Dict[str, Any] = {}
    if SECRETS_FILE.exists():
        try:
            data = json.loads(SECRETS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    if DEEPSEEK_API_KEY:
        data["deepseek_api_key"] = DEEPSEEK_API_KEY
    else:
        data.pop("deepseek_api_key", None)
    SECRETS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    SECRETS_FILE.chmod(0o600)


def _load_llm_config() -> None:
    """Load persisted LM Studio base URL, overriding the default if present."""
    global LM_STUDIO_BASE_URL
    if LLM_CONFIG_FILE.exists():
        try:
            data = json.loads(LLM_CONFIG_FILE.read_text(encoding="utf-8"))
            url = data.get("base_url")
            if url:
                LM_STUDIO_BASE_URL = url
                logger.info(f"Loaded LM Studio base URL from config: {url}")
        except Exception as e:
            logger.warning(f"Failed to load LLM config: {e}")


def _save_llm_config() -> None:
    LLM_CONFIG_FILE.write_text(
        json.dumps({"base_url": LM_STUDIO_BASE_URL}, indent=2), encoding="utf-8"
    )


_load_secrets()
_load_llm_config()


def _load_sessions() -> List[Dict[str, Any]]:
    if not SESSIONS_FILE.exists():
        return []
    try:
        data = json.loads(SESSIONS_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(
            f"[sessions] Corrupt sessions file (Fail Fast)\n"
            f"  Path: {SESSIONS_FILE}\n"
            f"  Error: {e}"
        ) from e
    if not isinstance(data, list):
        raise RuntimeError(
            f"[sessions] Expected JSON array (Fail Fast)\n"
            f"  Path: {SESSIONS_FILE}\n"
            f"  Actual type: {type(data).__name__}"
        )
    return data


def _save_sessions(sessions: List[Dict[str, Any]]) -> None:
    SESSIONS_FILE.write_text(json.dumps(sessions, indent=2, ensure_ascii=False), encoding="utf-8")


def _messages_file(session_id: str) -> Path:
    return MESSAGES_DIR / f"{session_id}.json"


def _load_messages(session_id: str) -> List[Dict[str, Any]]:
    f = _messages_file(session_id)
    if not f.exists():
        return []
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(
            f"[messages] Corrupt messages file (Fail Fast)\n"
            f"  Path: {f}\n"
            f"  Session: {session_id}\n"
            f"  Error: {e}"
        ) from e
    if not isinstance(data, list):
        raise RuntimeError(
            f"[messages] Expected JSON array (Fail Fast)\n"
            f"  Path: {f}\n"
            f"  Actual type: {type(data).__name__}"
        )
    return data


def _save_messages(session_id: str, messages: List[Dict[str, Any]]) -> None:
    _messages_file(session_id).write_text(
        json.dumps(messages, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _delete_session_messages(session_id: str) -> bool:
    """Remove persisted message file for a session. Returns True if a file was deleted."""
    f = _messages_file(session_id)
    if not f.exists():
        return False
    f.unlink()
    return True


SESSIONS: List[Dict[str, Any]] = _load_sessions()


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    print("🚀 Starting SafeClaw API...")
    load_safe_claw()
    yield
    print("🛑 Shutting down SafeClaw API...")


# Create FastAPI app
app = FastAPI(
    title="SafeClaw API",
    description="FastAPI backend for SafeClaw Agent Workspace",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "safe_claw_loaded": safe_claw_loaded,
        "version": "1.0.0"
    }


def _sse(data: dict) -> str:
    """Helper to format an SSE data line."""
    return f"data: {json.dumps(data)}\n\n"


# Chat streaming endpoint
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat responses from SafeClaw"""
    from safe_claw.core.agent_modes import ModePolicyError, resolve_mode_policy

    try:
        mode_policy = resolve_mode_policy(request.mode)
    except ModePolicyError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    async def event_generator() -> AsyncGenerator[str, None]:
        t0 = datetime.now().timestamp()
        msg_id = f"msg-{t0}"
        try:
            # Get last user message
            last_message = None
            for msg in reversed(request.messages):
                if msg.role == "user":
                    last_message = msg.text()
                    break
            
            if not last_message:
                yield _sse({"type": "error", "error": "No user message found"})
                yield _sse({"type": "done", "session_id": request.session_id, "message_id": msg_id})
                return

            yield _sse({
                "type": "execution_step",
                "step_id": "mode_gate",
                "name": f"Mode gate · {mode_policy.mode}",
                "step_type": "gate",
                "status": "completed",
                "sub": (
                    f"create={mode_policy.allow_create} edit={mode_policy.allow_edit} "
                    f"delete={mode_policy.allow_delete} skill={mode_policy.skill_execute} "
                    f"obs={mode_policy.observability}"
                ),
                "chips": [
                    f"✓ {mode_policy.mode}",
                    "create" if mode_policy.allow_create else "no-create",
                    "edit" if mode_policy.allow_edit else "no-edit",
                ],
            })
            
            # ── Step 1: Parse ─────────────────────────────────────
            t_parse_start = datetime.now().timestamp()
            yield _sse({"type": "execution_step", "step_id": "parse", "name": "Understanding request",
                        "step_type": "reasoning", "status": "running"})
            # Minimal latency – just identifying the intent
            await asyncio.sleep(0.05)
            yield _sse({"type": "execution_step", "step_id": "parse", "name": "Understanding request",
                        "step_type": "reasoning", "status": "completed",
                        "duration": round(datetime.now().timestamp() - t_parse_start, 3),
                        "sub": "Parsed intent & entities",
                        "chips": ["\u2713 done"]})

            # ── Step 2: Skill router (semantic matching; chips ≠ loaded) ─
            t_router_start = datetime.now().timestamp()
            try:
                sm = _get_skills_manager()
            except RuntimeError as e:
                yield _sse({"type": "error", "error": str(e)})
                yield _sse({"type": "done", "session_id": request.session_id, "message_id": msg_id})
                return

            # SoT = SkillsManager only. ChatRequest.enabled_skills is deprecated (ignored).
            active_skills = sm.get_enabled_skills()
            if request.enabled_skills:
                logger.info(
                    "[chat/stream] Ignoring deprecated request.enabled_skills "
                    "(SoT=%s, request=%s) — toggle via POST /skills",
                    len(active_skills),
                    len(request.enabled_skills),
                )

            yield _sse({"type": "execution_step", "step_id": "router", "name": "Skill router",
                        "step_type": "tool_call", "status": "running",
                        "active_skills": active_skills})

            # Semantic match: rank enabled skills by relevance (router hint only)
            router_skill_names: list[str] = []
            if active_skills and last_message:
                try:
                    from safe_claw.core.skills.matcher import get_semantic_matcher
                    matcher = get_semantic_matcher()
                    enabled_set = set(active_skills)
                    entries = [
                        entry for entry in sm.skill_scanner.index.values()
                        if entry.name in enabled_set
                    ]
                    if entries:
                        matches = matcher.simple_match_l1(last_message, entries, top_k=5)
                        router_skill_names = [m.skill.name for m in matches if m.score > 0]
                except Exception as e:
                    logger.warning(f"Skill router semantic match failed: {e}")

            router_dur = round(datetime.now().timestamp() - t_router_start, 3)
            yield _sse({"type": "execution_step", "step_id": "router", "name": "Skill router",
                        "step_type": "tool_call", "status": "completed",
                        "duration": router_dur,
                        "sub": f"Router match: {', '.join(router_skill_names[:3]) or '(none)'}",
                        "chips": ["\u2713 done"] + router_skill_names[:3] + [f"{router_dur}s"],
                        "skills_invoked": router_skill_names,
                        "note": "skills_invoked = BM25 router hints; see skills_loaded for agent load"})

            # ── Step 3: Memory retrieval ──────────────────────────
            from safe_claw.core.memory.manager import (
                format_memory_context,
                serialize_memory,
            )

            t_mem_start = datetime.now().timestamp()
            yield _sse({"type": "execution_step", "step_id": "memory", "name": "Memory retrieval",
                        "step_type": "context_retrieval", "status": "running"})

            # Ensure global MemoryManager (singleton) is available
            global memory_manager
            if memory_manager is None:
                load_safe_claw()
            if memory_manager is None:
                from safe_claw.core.memory.manager import MemoryManager
                from safe_claw.models.config import MemoryConfig

                memory_manager = MemoryManager(
                    config=MemoryConfig(),
                    workspace_path=str(WORKSPACE_DIR),
                )
            global_mm = memory_manager

            mem_hits = global_mm.search_memories(last_message, max_results=5)
            mem_context = format_memory_context(mem_hits, top_k=5)
            mem_count = len(mem_hits)
            mem_preview = []
            for hit in mem_hits[:3]:
                snippet = (hit.memory.content or "").replace("\n", " ").strip()
                mem_preview.append(snippet[:48] + ("…" if len(snippet) > 48 else ""))

            mem_dur = round(datetime.now().timestamp() - t_mem_start, 3)
            mem_sub = (
                f"{mem_count} relevant memories loaded"
                if mem_count
                else "0 relevant memories loaded"
            )
            mem_chips = ["\u2713 done", f"{mem_dur}s", f"{mem_count} memories"] + mem_preview
            yield _sse({"type": "execution_step", "step_id": "memory", "name": "Memory retrieval",
                        "step_type": "context_retrieval", "status": "completed",
                        "duration": mem_dur,
                        "sub": mem_sub,
                        "chips": mem_chips,
                        "memories": [serialize_memory(h.memory) for h in mem_hits]})

            # ── Step 4: LLM call using SafeClawGraphBuilder ───────────────
            model_id = request.model if request.model else _selected_model
            t_llm_start = datetime.now().timestamp()
            prompt_tokens = sum(len(m.text().split()) for m in request.messages)
            llm_service = None

            # Import SafeClawGraphBuilder and related modules
            from safe_claw.services.llm_gateway import LLMService, LLMConfig
            from safe_claw.core.graph.builder import SafeClawGraphBuilder
            from safe_claw.core.deepagents.official_integration import (
                _llm_call_logs_lock, _llm_call_logs
            )

            # Detect provider: DeepSeek models bypass LM Studio entirely
            _is_deepseek = model_id.startswith("deepseek")
            if _is_deepseek:
                if not DEEPSEEK_API_KEY:
                    yield _sse({"type": "error",
                                "error": "DeepSeek API key not configured. "
                                         "Set it via Settings → DeepSeek API Key."})
                    yield _sse({"type": "done", "session_id": request.session_id, "message_id": msg_id})
                    return
                llm_config = LLMConfig(
                    provider="deepseek",
                    model=model_id,
                    api_key=DEEPSEEK_API_KEY,
                    base_url=None,
                    temperature=request.temperature,
                    max_tokens=4096,
                )
                lm_ready = True
                lm_studio_ready = True
            else:
                # Create LLM config for LM Studio
                llm_config = LLMConfig(
                    provider="openai",
                    model=model_id,
                    api_key="lm-studio",
                    base_url=LM_STUDIO_BASE_URL,
                    temperature=request.temperature,
                    max_tokens=512,
                )

                # Pre-flight health check for LM Studio (avoid 503 errors)
                lm_ready = False
                lm_studio_ready = True  # Default to True, set to False on failure
                try:
                    async with httpx.AsyncClient(timeout=5.0, trust_env=False) as client:
                        resp = await client.get(_lm_studio_models_url())
                        if resp.status_code == 200:
                            models = resp.json().get("data", [])
                            lm_ready = any(m.get("id") == model_id for m in models)
                            if not lm_ready:
                                available = [m.get("id") for m in models]
                                raise ValueError(
                                    f"[chat/stream] Requested model not loaded in LM Studio\n"
                                    f"  Requested: {model_id}\n"
                                    f"  Available: {available}"
                                )
                        else:
                            raise ValueError(
                                f"[chat/stream] LM Studio /models HTTP {resp.status_code}\n"
                                f"  Base URL: {LM_STUDIO_BASE_URL}"
                            )
                except Exception as e:
                    logger.error("LM Studio health check failed (Fail Fast): %s", e)
                    yield _sse({"type": "error", "error": str(e)})
                    yield _sse({"type": "done", "session_id": request.session_id, "message_id": msg_id})
                    return

            if not lm_ready:
                err = (
                    f"[chat/stream] LLM not ready (Fail Fast)\n"
                    f"  model_id: {model_id}\n"
                    f"  provider: {'deepseek' if _is_deepseek else 'lm-studio'}"
                )
                logger.error(err)
                yield _sse({"type": "error", "error": err})
                yield _sse({"type": "done", "session_id": request.session_id, "message_id": msg_id})
                return

            llm_service = LLMService(config=llm_config)

            # Create SafeClawGraphBuilder with DeepAgent — reuse global SM + MemoryManager
            ppt_preview_events: List[Dict[str, Any]] = []

            def _on_ppt_preview(payload: Dict[str, Any]) -> None:
                ppt_preview_events.append(dict(payload))

            try:
                graph_builder = SafeClawGraphBuilder(
                    llm_service=llm_service,
                    memory_manager=global_mm,
                    config={
                        "skills_manager": sm,
                        "enabled_skills": active_skills,
                        "max_skills": 100,
                        "system_prompt_limit": 65536,
                        "print_prompts": True,
                        "mode_policy": mode_policy,
                        "workspace_path": str(WORKSPACE_DIR),
                        "session_id": request.session_id or "_default",
                        "on_ppt_preview": _on_ppt_preview,
                        "backend": {
                            "filesystem": {
                                "enabled": True,
                                "base_path": str(WORKSPACE_DIR.parent),
                                "encrypt_files": False,
                                "allow_write": mode_policy.allow_write,
                                "allow_edit": mode_policy.allow_edit,
                                "allow_delete": mode_policy.allow_delete,
                            }
                        }
                    }
                )
            except Exception as e:
                logger.error("DeepAgent/GraphBuilder init failed (Fail Fast): %s", e)
                yield _sse({"type": "error", "error": str(e)})
                yield _sse({"type": "done", "session_id": request.session_id, "message_id": msg_id})
                return

            deep_agent = graph_builder.deep_agent
            loaded = (
                deep_agent.get_loaded_skills()
                if hasattr(deep_agent, "get_loaded_skills")
                else {"names": [], "paths": [], "count": 0}
            )
            yield _sse({
                "type": "execution_step",
                "step_id": "skills_load",
                "name": "Skills loaded into agent",
                "step_type": "tool_call",
                "status": "completed",
                "sub": f"{loaded.get('count', 0)} skills passed to create_deep_agent",
                "chips": ["\u2713 loaded"] + list(loaded.get("names") or [])[:8],
                "skills_loaded": loaded.get("names") or [],
                "skills_loaded_paths": loaded.get("paths") or [],
            })

            yield _sse({"type": "execution_step", "step_id": "llm", "name": "LLM call",
                        "step_type": "model_call", "status": "running",
                        "sub": f"{model_id} \u00b7 stream \u00b7 512 max tokens",
                        "skills_loaded": loaded.get("names") or []})

            full_response = ""
            has_error = False
            stream_error: Optional[str] = None

            try:
                messages = [{"role": m.role, "content": m.content} for m in request.messages]
                if mem_context:
                    messages = [
                        {"role": "system", "content": mem_context},
                        *messages,
                    ]

                for chunk in deep_agent.stream(messages, message_id=msg_id, session_id=request.session_id or ""):
                    while ppt_preview_events:
                        ev = ppt_preview_events.pop(0)
                        yield _sse({"type": "ppt_preview", **ev})
                    if chunk.get("type") == "error":
                        stream_error = chunk.get("content") or "Unknown DeepAgent stream error"
                        has_error = True
                        logger.error("DeepAgent stream error chunk (Fail Fast): %s", stream_error)
                        break
                    elif chunk.get("type") == "execution_step":
                        # Subagent / nested tool observability (authoritative tree)
                        yield _sse(chunk)
                    elif chunk.get("type") == "ppt_preview":
                        yield _sse(chunk)
                    elif chunk.get("thinking"):
                        yield _sse({"type": "thinking", "content": chunk["thinking"]})
                    elif chunk.get("tool"):
                        yield _sse({"type": "tool", "tool": chunk["tool"], "content": chunk.get("content", "")})
                        # Fallback: parse ppt_preview JSON from tool result text
                        raw = chunk.get("content") or ""
                        if "ppt_preview" in raw and "preview_urls" in raw:
                            try:
                                import json as _json

                                data = _json.loads(raw)
                                if data.get("type") == "ppt_preview":
                                    yield _sse({"type": "ppt_preview", **data})
                            except Exception:
                                pass
                    elif chunk.get("content"):
                        full_response = chunk["content"]
                        yield _sse({"type": "content", "content": full_response})

                while ppt_preview_events:
                    ev = ppt_preview_events.pop(0)
                    yield _sse({"type": "ppt_preview", **ev})

            except Exception as e:
                has_error = True
                stream_error = str(e)
                logger.error("SafeClawGraphBuilder/DeepAgent error (Fail Fast): %s", e)

            if has_error:
                err = stream_error or "DeepAgent stream failed without detail"
                yield _sse({"type": "execution_step", "step_id": "llm", "name": "LLM call",
                            "step_type": "model_call", "status": "failed",
                            "sub": f"{model_id} · failed"})
                yield _sse({"type": "error", "error": err})
                yield _sse({"type": "done", "session_id": request.session_id, "message_id": msg_id})
                return

            if not full_response.strip():
                err = (
                    f"[chat/stream] Empty LLM response (Fail Fast)\n"
                    f"  model_id: {model_id}\n"
                    f"  message_id: {msg_id}"
                )
                yield _sse({"type": "error", "error": err})
                yield _sse({"type": "done", "session_id": request.session_id, "message_id": msg_id})
                return

            # Complete LLM step
            completion_tokens = len(full_response.split())
            llm_dur = round(datetime.now().timestamp() - t_llm_start, 3)

            yield _sse({"type": "execution_step", "step_id": "llm", "name": "LLM call",
                        "step_type": "model_call", "status": "completed",
                        "duration": llm_dur,
                        "sub": f"{model_id} \u00b7 stream \u00b7 512 max tokens",
                        "chips": ["\u2713 done", f"{llm_dur}s", f"{prompt_tokens} in", f"{completion_tokens} out"]})

            # Persist turn to memory when importance passes threshold (mode gate)
            if full_response and global_mm is not None and mode_policy.memory_auto_write:
                try:
                    stored_id = global_mm.maybe_store_conversation(
                        user_input=last_message,
                        response=full_response.strip(),
                        session_id=request.session_id,
                    )
                    if stored_id:
                        logger.info("[chat/stream] Stored conversation memory id=%s", stored_id)
                except Exception as mem_err:
                    logger.error("[chat/stream] Failed to store memory: %s", mem_err)
                    raise
            elif full_response and not mode_policy.memory_auto_write:
                logger.info(
                    "[chat/stream] Skip memory auto-write (mode=%s)", mode_policy.mode
                )

            # ── Done ──────────────────────────────────────────────
            total_dur = round(datetime.now().timestamp() - t0, 3)
            total_tokens = prompt_tokens + completion_tokens

            # Retrieve actual LLM call logs from SafeClawDeepAgent (populated by PromptLoggerMiddleware)
            with _llm_call_logs_lock:
                agent_logs = _llm_call_logs.get(msg_id, [])

            # Build LLM calls array - use actual logs from middleware if available, fallback to synthetic
            if agent_logs:
                llm_calls = []
                for i, call in enumerate(agent_logs):
                    llm_calls.append({
                        "call_id": call.get("call_id", f"call-{i+1}-{msg_id}"),
                        "call_number": call.get("call_number", i + 1),
                        "timestamp": call.get("timestamp", datetime.now().isoformat()),
                        "status": "completed",
                        "steps": [
                            {"id": "parse-1", "name": "Understanding request", "type": "reasoning", "status": "completed",
                             "duration": round(datetime.now().timestamp() - t_parse_start, 3)},
                            {"id": "router-1", "name": "Skill router", "type": "tool_call", "status": "completed",
                             "duration": router_dur},
                            {"id": "memory-1", "name": "Memory retrieval", "type": "context_retrieval", "status": "completed",
                             "duration": mem_dur},
                            {"id": f"llm-{i+1}", "name": f"LLM call #{i+1}", "type": "model_call", "status": "completed",
                             "duration": (call.get("duration_ms", 0) / 1000) if call.get("duration_ms") else llm_dur,
                             "chips": [f"{call.get('token_estimate', 0):.0f} in", f"{call.get('response_tokens', 0)} out"]},
                        ],
                        "active_skills": active_skills[:10] if active_skills else [],
                        "skills_invoked": router_skill_names,
                        "skills_loaded": loaded.get("names") or [],
                        "prompt_tokens": int(call.get("token_estimate", prompt_tokens)),
                        "completion_tokens": call.get("response_tokens", completion_tokens),
                        "duration_ms": call.get("duration_ms", round(llm_dur * 1000, 2)),
                        "response_preview": call.get("response", full_response)[:200] if (call.get("response") or full_response) else "",
                        # Include full prompt/response from middleware logs
                        "prompt": call.get("formatted_prompt", ""),
                        "response": call.get("response", ""),
                    })
            else:
                # Fallback: synthetic log entry (DeepAgent didn't populate logs)
                llm_calls = [{
                    "call_id": f"call-1-{msg_id}",
                    "call_number": 1,
                    "timestamp": datetime.now().isoformat(),
                    "status": "completed",
                    "steps": [
                        {"id": "parse-1", "name": "Understanding request", "type": "reasoning", "status": "completed",
                         "duration": round(datetime.now().timestamp() - t_parse_start, 3)},
                        {"id": "router-1", "name": "Skill router", "type": "tool_call", "status": "completed",
                         "duration": router_dur},
                        {"id": "memory-1", "name": "Memory retrieval", "type": "context_retrieval", "status": "completed",
                         "duration": mem_dur},
                        {"id": "llm-1", "name": "LLM call", "type": "model_call", "status": "completed",
                         "duration": llm_dur, "chips": [f"{prompt_tokens} in", f"{completion_tokens} out"]},
                    ],
                    "active_skills": active_skills[:10] if active_skills else [],
                    "skills_invoked": router_skill_names,
                    "skills_loaded": loaded.get("names") or [],
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "duration_ms": round(llm_dur * 1000, 2),
                    "response_preview": full_response[:200] if full_response else "",
                }]

            yield _sse({
                "type": "done",
                "session_id": request.session_id,
                "message_id": msg_id,
                "mode": mode_policy.mode,
                "observability": mode_policy.observability,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                },
                "timing": {
                    "start_time": t0,
                    "end_time": datetime.now().timestamp(),
                    "total_duration": total_dur,
                },
                "execution_path": [
                    {"name": "Understanding request", "duration": round(datetime.now().timestamp() - t_parse_start, 3)},
                    {"name": "Skill router",          "duration": router_dur},
                    {"name": "Memory retrieval",      "duration": mem_dur},
                    {"name": "LLM call",              "duration": llm_dur},
                ],
                "skills_used": [{"name": s, "duration": 0} for s in router_skill_names],
                "skills_loaded": loaded.get("names") or [],
                "llm_calls": llm_calls,
                "total_calls": len(llm_calls),
            })
                
        except Exception as e:
            logger.error("Chat stream error (Fail Fast, no mock): %s", e)
            yield _sse({"type": "error", "error": str(e)})
            yield _sse({"type": "done", "session_id": request.session_id, "message_id": msg_id})
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# Skills endpoints
@app.get("/skills")
async def get_skills(flat: bool = False):
    """Scan real skill directories and return tree. 503 if SkillsManager unavailable."""
    try:
        tree = build_skill_tree()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        print(f"Skills scan error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

    private_count = sum(
        len(n["children"]) for n in tree if n["id"] == "private"
    )
    linked_count = sum(
        len(n["children"]) for n in tree if n["id"].startswith("linked/")
    )
    total = sum(len(n["children"]) for n in tree)
    return {
        "tree": tree,
        "total": total,
        "categories": len(tree),
        "private": private_count,
        "linked": linked_count,
    }


@app.post("/skills")
async def toggle_skill(request: SkillToggleRequest):
    """Toggle skill or folder enabled state via SkillsManager (strict folder match)."""
    sm = _require_skills_manager()
    project_root = Path(__file__).parent.parent

    if request.folder_id:
        # Toggle entire folder: enable/disable all skills in that collection only
        _folder_enabled[request.folder_id] = request.enabled
        current = _enabled_skills_mutable(sm)
        changed = []
        for entry in sm.skill_scanner.index.values():
            cid = _skill_collection_id(Path(entry.path), project_root)
            if cid != request.folder_id:
                continue
            if request.enabled:
                current.add(entry.name)
            else:
                current.discard(entry.name)
            changed.append(entry.name)
        if not changed:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"[skills/toggle] Unknown folder_id (Fail Fast)\n"
                    f"  folder_id: {request.folder_id!r}\n"
                    f"  Hint: use ids from GET /skills tree (e.g. private, linked/...)."
                ),
            )
        sm.set_enabled_skills(list(current))
        print(
            f"🔧 Folder toggle '{request.folder_id}': {len(changed)} skills "
            f"{'enabled' if request.enabled else 'disabled'}, {len(current)} total active"
        )
    elif request.skill_id:
        current = _enabled_skills_mutable(sm)
        if request.enabled:
            current.add(request.skill_id)
        else:
            current.discard(request.skill_id)
        sm.set_enabled_skills(list(current))
    else:
        raise HTTPException(
            status_code=400,
            detail="[skills/toggle] Require skill_id or folder_id (Fail Fast)",
        )

    _save_skill_tree_state(sm)

    return {
        "success": True,
        "skill_id": request.skill_id,
        "folder_id": request.folder_id,
        "enabled": request.enabled,
        "enabled_count": len(sm.get_enabled_skills()),
    }


@app.post("/skills/toggle")
async def toggle_skill_alias(request: SkillToggleRequest):
    """Alias: POST /skills/toggle — same as POST /skills"""
    return await toggle_skill(request)


@app.post("/skills/{skill_id:path}/toggle")
async def toggle_skill_by_id(skill_id: str, request: SkillToggleRequest):
    """Toggle a specific skill by path param: POST /skills/{id}/toggle"""
    merged = SkillToggleRequest(
        skill_id=skill_id,
        folder_id=request.folder_id,
        enabled=request.enabled,
    )
    return await toggle_skill(merged)


# Session endpoints
@app.get("/sessions")
async def list_sessions(limit: int = 20, offset: int = 0):
    """List sessions"""
    try:
        sliced = SESSIONS[offset: offset + limit]
        return {
            "sessions": sliced,
            "total": len(SESSIONS),
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < len(SESSIONS),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions")
async def create_session(request: SessionCreateRequest):
    """Create new session"""
    try:
        session_id = f"sess-{datetime.now().timestamp()}"
        new_session = {
            "id": session_id,
            "title": request.title,
            "status": "active",
            "message_count": 0,
            "settings": {
                "model": request.model or _selected_model,
                "enabled_skills": [],
                "mode": "agent",
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "last_activity_at": datetime.now().isoformat()
        }
        SESSIONS.insert(0, new_session)
        _save_sessions(SESSIONS)
        return {"session": new_session, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get single session by ID"""
    session = next((s for s in SESSIONS if s["id"] == session_id), None)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session": session}


@app.patch("/sessions/{session_id}")
async def update_session(session_id: str, request: SessionUpdateRequest):
    """Update a session"""
    session = next((s for s in SESSIONS if s["id"] == session_id), None)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if request.title is not None:
        session["title"] = request.title
    if request.status is not None:
        session["status"] = request.status
    if request.settings is not None:
        session["settings"].update(request.settings)
    session["updated_at"] = datetime.now().isoformat()
    _save_sessions(SESSIONS)
    return {"session": session, "success": True}


@app.delete("/sessions")
async def delete_session(id: str):
    """Delete session by query param: DELETE /sessions?id=xxx"""
    try:
        global SESSIONS
        SESSIONS = [s for s in SESSIONS if s["id"] != id]
        _save_sessions(SESSIONS)
        _delete_session_messages(id)
        return {"success": True, "deleted_id": id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sessions/all")
async def delete_all_sessions():
    """One-click clear: delete every session + message files (Fail Fast, no soft archive)."""
    global SESSIONS
    ids = [s["id"] for s in SESSIONS]
    message_files_removed = 0
    if MESSAGES_DIR.exists():
        for f in MESSAGES_DIR.glob("*.json"):
            try:
                f.unlink()
                message_files_removed += 1
            except OSError as e:
                raise RuntimeError(
                    f"[sessions/all] Failed to delete message file (Fail Fast)\n"
                    f"  Path: {f}\n"
                    f"  Error: {e}"
                ) from e
    count = len(ids)
    SESSIONS = []
    _save_sessions(SESSIONS)
    logger.info(
        "[sessions/all] Cleared %s sessions, message_files_removed=%s",
        count,
        message_files_removed,
    )
    return {
        "success": True,
        "deleted_count": count,
        "deleted_ids": ids,
        "message_files_removed": message_files_removed,
    }


@app.delete("/sessions/{session_id}")
async def delete_session_by_path(session_id: str):
    """Delete session by path param: DELETE /sessions/{id}"""
    if session_id == "all":
        # Defensive: static route /sessions/all should win; never treat "all" as an id.
        return await delete_all_sessions()
    global SESSIONS
    SESSIONS = [s for s in SESSIONS if s["id"] != session_id]
    _save_sessions(SESSIONS)
    _delete_session_messages(session_id)
    return {"success": True, "deleted_id": session_id}


# Session messages endpoints
@app.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """Return persisted messages for a session"""
    session = next((s for s in SESSIONS if s["id"] == session_id), None)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = _load_messages(session_id)
    return {"messages": messages, "total": len(messages)}


class MessagePayload(BaseModel):
    messages: List[Dict[str, Any]]


@app.post("/sessions/{session_id}/messages")
async def save_session_messages(session_id: str, payload: MessagePayload):
    """Persist messages for a session (full replace)"""
    session = next((s for s in SESSIONS if s["id"] == session_id), None)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _save_messages(session_id, payload.messages)
    # Update message_count on session
    session["message_count"] = len(payload.messages)
    session["updated_at"] = datetime.now().isoformat()
    _save_sessions(SESSIONS)
    return {"success": True, "count": len(payload.messages)}


# Memory endpoints
class MemoryCreateRequest(BaseModel):
    content: str = Field(..., min_length=1)
    importance: float = Field(default=0.8, ge=0.0, le=1.0)
    keywords: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


@app.post("/memory/cleanup")
async def cleanup_memories_post():
    """Run memory cleanup"""
    if not safe_claw_loaded or memory_manager is None:
        load_safe_claw()
    if memory_manager is None:
        raise HTTPException(
            status_code=503,
            detail="[memory/cleanup] MemoryManager not available",
        )
    result = memory_manager.cleanup_old_memories()
    return {"success": True, "result": result, "stats": memory_manager.get_memory_stats()}


@app.post("/memory")
async def create_memory(body: MemoryCreateRequest):
    """Explicitly add a memory (e.g. /remember slash)."""
    if not safe_claw_loaded or memory_manager is None:
        load_safe_claw()
    if memory_manager is None:
        raise HTTPException(
            status_code=503,
            detail="[memory] MemoryManager not available",
        )
    from safe_claw.core.memory.manager import serialize_memory

    memory_id = memory_manager.add_memory(
        content=body.content,
        importance_score=body.importance,
        keywords=body.keywords,
        metadata={**(body.metadata or {}), "source": "api"},
    )
    memory = memory_manager.get_memory(memory_id)
    if memory is None:
        raise HTTPException(
            status_code=500,
            detail=f"[memory] Created memory missing after write\n  id: {memory_id}",
        )
    return {
        "success": True,
        "id": memory_id,
        "memory": serialize_memory(memory),
        "stats": memory_manager.get_memory_stats(),
    }


@app.get("/memory")
async def get_memories(layer: str = "active", limit: int = 20, search: Optional[str] = None):
    """Get memories from the memory manager"""
    from safe_claw.core.memory.manager import VALID_LAYERS, serialize_memory
    from safe_claw.models.memory import MemorySearchResult

    if not safe_claw_loaded or memory_manager is None:
        load_safe_claw()
    if memory_manager is None:
        raise HTTPException(
            status_code=503,
            detail="[memory] MemoryManager not available",
        )

    if search is None and layer not in VALID_LAYERS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"[memory] Invalid layer\n"
                f"  layer: {layer!r}\n"
                f"  Expected: {sorted(VALID_LAYERS)}"
            ),
        )

    stats = memory_manager.get_memory_stats()
    if search:
        results = memory_manager.search_memories(search, limit)
        memories = [
            serialize_memory(r.memory if isinstance(r, MemorySearchResult) else r)
            for r in results
        ]
    else:
        items = memory_manager.get_memories_by_layer(layer, limit)
        memories = [serialize_memory(m) for m in items]

    return {
        "memories": memories,
        "stats": stats,
        "total": len(memories),
    }


# System monitor endpoint
@app.get("/system")
async def get_system_info():
    """Get system resource information"""
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        return {
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count(),
                "per_cpu": psutil.cpu_percent(percpu=True, interval=0),
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "percent": memory.percent,
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": round(disk.used / disk.total * 100, 1),
            },
            "safe_claw_loaded": safe_claw_loaded,
        }
    except ImportError:
        return {
            "cpu": {"percent": 0, "count": 0, "per_cpu": []},
            "memory": {"total": 0, "available": 0, "used": 0, "percent": 0},
            "disk": {"total": 0, "used": 0, "free": 0, "percent": 0},
            "safe_claw_loaded": safe_claw_loaded,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Safety dashboard endpoint
@app.get("/safety")
async def get_safety_stats():
    """Get safety statistics"""
    try:
        if safe_claw_loaded:
            try:
                from safe_claw.core.safety.checker import SafetyChecker
                from safe_claw.core.safety.audit import AuditLogger
                checker = SafetyChecker()
                auditor = AuditLogger()
                stats = checker.get_safety_stats()
                audit_stats = auditor.get_statistics()
                return {"safety_stats": stats, "audit_stats": audit_stats}
            except Exception:
                pass
        return {
            "safety_stats": {
                "total_checks": 0,
                "blocked_requests": 0,
                "confirmation_required": 0,
                "block_rate": 0.0,
                "risk_distribution": {"low": 0, "medium": 0, "high": 0, "critical": 0},
            },
            "audit_stats": {"total_events": 0, "by_level": {}},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


FALLBACK_MODELS = [
    {"id": "deepseek-v4-flash",   "name": "DeepSeek V4 Flash", "provider": "deepseek"},
    {"id": "deepseek-v4-pro",     "name": "DeepSeek V4 Pro",   "provider": "deepseek"},
    {"id": "qwen3.5-9b-vlm",       "name": "Qwen3.5 9B",      "provider": "lm-studio"},
    {"id": "gemma-4-e4b",          "name": "Gemma 4 E4B",     "provider": "lm-studio"},
    {"id": "gemma-4-31b",          "name": "Gemma 4 31B",     "provider": "lm-studio"},
    {"id": "qwen3.6-27b",          "name": "Qwen3.6 27B",     "provider": "lm-studio"},
    {"id": "qwen/qwen3.5-35b-a3b", "name": "Qwen3.5 35B A3B", "provider": "lm-studio"},
]

_CLOUD_MODELS = [
    {"id": "deepseek-v4-flash", "name": "DeepSeek V4 Flash", "provider": "deepseek"},
    {"id": "deepseek-v4-pro", "name": "DeepSeek V4 Pro", "provider": "deepseek"},
]


# Settings / model info endpoint
@app.get("/settings/models")
async def get_available_models():
    """LM Studio loaded models + always-available cloud models (DeepSeek)."""
    models: List[Dict[str, Any]] = []
    source = "fallback"
    try:
        async with httpx.AsyncClient(timeout=3.0, trust_env=False) as client:
            resp = await client.get(_lm_studio_models_url())
            if resp.status_code == 200:
                data = resp.json()
                models = [
                    {
                        "id": m["id"],
                        "name": m["id"].split("/")[-1],
                        "provider": "lm-studio",
                        "owned_by": m.get("owned_by", ""),
                    }
                    for m in data.get("data", [])
                ]
                if models:
                    source = "lm-studio+cloud"
    except Exception as e:
        # LM Studio optional for listing; DeepSeek cloud models still required.
        logger.warning("LM Studio models fetch failed: %s — returning cloud models only", e)
        source = "cloud-only"
        models = []
    if not models:
        models = []
        source = "cloud-only" if source != "lm-studio+cloud" else source
    # DeepSeek is the global default selection — always list it, even when LM Studio responds.
    existing = {m["id"] for m in models}
    # Prepend cloud models so Flash (global default) appears before Pro.
    for cloud in reversed(_CLOUD_MODELS):
        if cloud["id"] not in existing:
            models.insert(0, dict(cloud))
    if not models:
        raise HTTPException(
            status_code=503,
            detail="[settings/models] No models available (Fail Fast)",
        )
    return {"models": models, "source": source, "default": DEFAULT_MODEL}


class LLMSettingsRequest(BaseModel):
    base_url: str


@app.get("/settings/llm")
async def get_llm_settings():
    """Return the current LM Studio base URL and live reachability."""
    reachable = False
    try:
        async with httpx.AsyncClient(timeout=3.0, trust_env=False) as client:
            resp = await client.get(_lm_studio_models_url())
            reachable = resp.status_code == 200
    except Exception:
        reachable = False
    return {"base_url": LM_STUDIO_BASE_URL, "reachable": reachable}


@app.put("/settings/llm")
async def update_llm_settings(request: LLMSettingsRequest):
    """Update and persist the LM Studio base URL, then test reachability."""
    global LM_STUDIO_BASE_URL
    base_url = request.base_url.strip()
    if not base_url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid base_url '{base_url}': must start with http:// or https://",
        )
    LM_STUDIO_BASE_URL = base_url
    _save_llm_config()
    logger.info(f"LM Studio base URL updated to: {base_url}")

    reachable = False
    error: Optional[str] = None
    try:
        async with httpx.AsyncClient(timeout=5.0, trust_env=False) as client:
            resp = await client.get(_lm_studio_models_url())
            reachable = resp.status_code == 200
    except Exception as e:
        error = str(e)
    return {"base_url": LM_STUDIO_BASE_URL, "reachable": reachable, "error": error}


class ModelSelectionRequest(BaseModel):
    model: str


@app.get("/settings/model")
async def get_selected_model():
    """Return the globally selected agent model."""
    return {"model": _selected_model}


@app.put("/settings/model")
async def update_selected_model(request: ModelSelectionRequest):
    """Update and persist the globally selected agent model in agent_config.json."""
    global _selected_model
    model = request.model.strip()
    if not model:
        raise HTTPException(status_code=400, detail="model must not be empty")
    _selected_model = model
    _save_agent_config(_get_skills_manager())
    logger.info(f"Selected agent model updated to: {model}")
    return {"model": _selected_model}


class DeepSeekSecretsRequest(BaseModel):
    api_key: str


@app.get("/settings/deepseek")
async def get_deepseek_settings():
    """Return DeepSeek configuration (key is masked for security)."""
    return {
        "configured": bool(DEEPSEEK_API_KEY),
        "api_key_hint": f"...{DEEPSEEK_API_KEY[-6:]}" if DEEPSEEK_API_KEY else None,
    }


@app.put("/settings/deepseek")
async def update_deepseek_settings(request: DeepSeekSecretsRequest):
    """Save DeepSeek API key to ~/.safeclaw_secrets.json (never committed)."""
    global DEEPSEEK_API_KEY
    key = request.api_key.strip()
    if not key:
        raise HTTPException(status_code=400, detail="api_key must not be empty")
    DEEPSEEK_API_KEY = key
    _save_secrets()
    logger.info("DeepSeek API key updated and persisted to secrets file.")
    return {
        "configured": True,
        "api_key_hint": f"...{DEEPSEEK_API_KEY[-6:]}",
    }


# File upload endpoint
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), path: str = Form(...)):
    """Upload a file into WORKSPACE_DIR (path traversal rejected)."""
    try:
        # Resolve under WORKSPACE_DIR — reject absolute paths outside and ".." traversal
        raw = Path(path)
        if raw.is_absolute():
            candidate = raw.resolve()
        else:
            candidate = (WORKSPACE_DIR / raw).resolve()

        try:
            candidate.relative_to(WORKSPACE_DIR.resolve())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"[Upload] Path escapes WORKSPACE_DIR\n"
                    f"  Requested: {path}\n"
                    f"  Resolved: {candidate}\n"
                    f"  Allowed root: {WORKSPACE_DIR}"
                ),
            )

        candidate.parent.mkdir(parents=True, exist_ok=True)
        content = await file.read()
        candidate.write_bytes(content)
        rel = str(candidate.relative_to(WORKSPACE_DIR.resolve()))
        return {"ok": True, "path": rel, "bytes": len(content)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Upload failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/workspace-file")
async def get_workspace_file(path: str):
    """Serve a file under WORKSPACE_DIR only (PPT previews, etc.)."""
    from fastapi.responses import FileResponse

    raw = (path or "").strip().lstrip("/")
    if not raw:
        raise HTTPException(
            status_code=400,
            detail="[workspace-file] path is required\n  Actual: empty",
        )
    candidate = (WORKSPACE_DIR / raw).resolve()
    try:
        candidate.relative_to(WORKSPACE_DIR.resolve())
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=(
                f"[workspace-file] Path escapes WORKSPACE_DIR\n"
                f"  Requested: {path}\n"
                f"  Resolved: {candidate}\n"
                f"  Allowed root: {WORKSPACE_DIR}"
            ),
        ) from e
    if not candidate.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"[workspace-file] Not found\n  Path: {candidate}",
        )
    return FileResponse(candidate)


# LLM Call Logs endpoint
@app.get("/llm-calls/{message_id}")
async def get_llm_calls(message_id: str):
    """Get LLM call logs (prompts, responses, execution steps, skills) for a specific message"""
    try:
        # Import the function from official_integration
        pkg_root = str(Path(__file__).parent.parent.parent)
        if pkg_root not in sys.path:
            sys.path.insert(0, pkg_root)
        from safe_claw.core.deepagents.official_integration import get_llm_call_logs
        logger.info("get_llm_call_logs...")
        logs = get_llm_call_logs(message_id)

        # Fail Fast: never invent synthetic "fallback mode" logs
        if not logs:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"[llm-calls] No logs for message_id={message_id}\n"
                    f"  Expected: real PromptLoggerMiddleware records"
                ),
            )

        # Enrich logs with execution steps and skills if not already present
        enriched_calls = []
        for i, call in enumerate(logs):
            logger.info("for i, call in enumerate(logs): {}, {}".format(i, call))
            enriched_call = {
                **call,
                # Add execution steps if not present
                "steps": call.get("steps") or [
                    {"id": f"step-{i}-1", "name": "LLM Request", "type": "model_call", "status": "completed",
                     "duration": call.get("duration_ms", 0) / 1000 if call.get("duration_ms") else 0}
                ],
                # Add skills data if not present
                "active_skills": call.get("active_skills") or [],
                "skills_invoked": call.get("skills_invoked") or [],
                "prompt_tokens": call.get("prompt_tokens") or call.get("token_estimate", 0),
                "completion_tokens": call.get("completion_tokens") or call.get("response_tokens", 0),
            }
            enriched_calls.append(enriched_call)

        return {
            "message_id": message_id,
            "calls": enriched_calls,
            "total_calls": len(enriched_calls),
        }
    except Exception as e:
        print(f"LLM call logs error: {e}")
        return {
            "message_id": message_id,
            "calls": [],
            "total_calls": 0,
            "error": str(e),
        }


@app.delete("/llm-calls/{message_id}")
async def clear_llm_calls(message_id: str):
    """Clear LLM call logs for a specific message"""
    try:
        pkg_root = str(Path(__file__).parent.parent.parent)
        if pkg_root not in sys.path:
            sys.path.insert(0, pkg_root)
        from safe_claw.core.deepagents.official_integration import clear_llm_call_logs

        clear_llm_call_logs(message_id)
        return {"success": True, "message_id": message_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
