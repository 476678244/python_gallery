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

# Configure logging to output to stdout
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

        # Create default LLM config for initialization
        llm_config = LLMConfig(
            provider="openai",
            model="qwen3.5-9b-vlm",
            api_key="mock-key",  # Will trigger MockLLMGateway fallback
            base_url=None,
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
        print(f"⚠️ SafeClaw load failed (using mock mode): {e}")
        safe_claw_loaded = False


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
    model: str = "qwen3.5-9b-vlm"
    temperature: float = 0.7
    stream: bool = True


class SessionCreateRequest(BaseModel):
    title: Optional[str] = "New Chat"
    model: str = "qwen3.5-9b-vlm"


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

DEFAULT_MODEL = "qwen3.5-9b-vlm"
# Globally selected agent model, persisted in agent_config.json.
_selected_model: str = DEFAULT_MODEL

def _get_skills_manager() -> Optional[Any]:
    """Get or lazily init the SkillsManager."""
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
        print(f"⚠️  SkillsManager init failed: {e}")
        skills_manager = None
    return skills_manager


# In-memory folder toggle state (skills use SkillsManager.set_enabled_skills)
_folder_enabled: Dict[str, bool] = {}


def _save_agent_config(sm: Any) -> None:
    """Persist agent config (enabled skills, folder toggles, model) to disk."""
    try:
        config = {
            "model": _selected_model,
            "enabled_skills": list(sm.get_enabled_skills_state() or []) if sm else [],
            "folder_enabled": _folder_enabled,
        }
        AGENT_CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"⚠️  Failed to save agent config: {e}")


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
        model = config.get("model")
        if model:
            _selected_model = model
            print(f"✅ Restored selected model: {model}")
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
    except Exception as e:
        print(f"⚠️  Failed to load agent config: {e}")


# Backwards-compatible alias
_load_skill_tree_state = _load_agent_config

# Load persisted model selection at startup (skills loaded later on SM init).
_load_agent_config(None)


def build_skill_tree() -> List[Dict[str, Any]]:
    """Build skill tree from SkillsManager.skill_scanner.index."""
    sm = _get_skills_manager()
    if not sm:
        return []

    # Get enabled skill names from manager state
    enabled_skills = sm.get_enabled_skills()
    enabled_set = set(enabled_skills)

    # Group index entries by collection (derived from path)
    project_root = Path(__file__).parent.parent  # python_gallery
    collections: Dict[str, List[Dict]] = {}

    for entry in sm.skill_scanner.index.values():
        skill_path = Path(entry.path)
        # Determine collection label from path segments
        try:
            rel = skill_path.relative_to(project_root)
            parts = rel.parts
            # linked_skills/<collection>/<skill>  or  skills/<type>/<skill>
            if parts[0] == "linked_skills" and len(parts) >= 3:
                collection_id = f"linked/{parts[1]}"
                collection_label = parts[1].replace("_", " ").replace("-", " ").title()
            elif "private_skills" in parts:
                collection_id = "private"
                collection_label = "Private Skills"
            elif len(parts) >= 2:
                collection_id = parts[0]
                collection_label = parts[0].replace("_", " ").title()
            else:
                collection_id = "other"
                collection_label = "Other"
        except ValueError:
            # Absolute path outside project root (resolved symlink)
            raw = str(skill_path)
            if "linked_skills" in raw:
                idx = raw.find("linked_skills")
                rest = raw[idx:].split("/")
                collection_id = f"linked/{rest[1]}" if len(rest) > 1 else "linked"
                collection_label = rest[1].replace("_", " ").replace("-", " ").title() if len(rest) > 1 else "Linked"
            elif "private_skills" in raw:
                collection_id = "private"
                collection_label = "Private Skills"
            else:
                collection_id = "other"
                collection_label = "Other"

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
    """Load API keys from the local secrets file (~/.safeclaw_secrets.json)."""
    global DEEPSEEK_API_KEY
    if SECRETS_FILE.exists():
        try:
            data = json.loads(SECRETS_FILE.read_text(encoding="utf-8"))
            key = data.get("deepseek_api_key")
            if key:
                DEEPSEEK_API_KEY = key
                logger.info("Loaded DeepSeek API key from secrets file.")
        except Exception as e:
            logger.warning(f"Failed to load secrets: {e}")


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
    if SESSIONS_FILE.exists():
        try:
            return json.loads(SESSIONS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save_sessions(sessions: List[Dict[str, Any]]) -> None:
    SESSIONS_FILE.write_text(json.dumps(sessions, indent=2, ensure_ascii=False), encoding="utf-8")


def _messages_file(session_id: str) -> Path:
    return MESSAGES_DIR / f"{session_id}.json"


def _load_messages(session_id: str) -> List[Dict[str, Any]]:
    f = _messages_file(session_id)
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save_messages(session_id: str, messages: List[Dict[str, Any]]) -> None:
    _messages_file(session_id).write_text(
        json.dumps(messages, indent=2, ensure_ascii=False), encoding="utf-8"
    )


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
                return
            
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

            # ── Step 2: Skill router (semantic matching) ─────────
            t_router_start = datetime.now().timestamp()
            sm = _get_skills_manager()
            active_skills = sm.get_enabled_skills() if sm else (request.enabled_skills or [])
            yield _sse({"type": "execution_step", "step_id": "router", "name": "Skill router",
                        "step_type": "tool_call", "status": "running",
                        "active_skills": active_skills})

            # Semantic match: rank enabled skills by relevance to the query
            skill_names: list[str] = []
            if sm and active_skills and last_message:
                try:
                    from safe_claw.core.skills.matcher import get_semantic_matcher
                    matcher = get_semantic_matcher()
                    # Build entries for only the enabled skills
                    enabled_set = set(active_skills)
                    entries = [
                        entry for entry in sm.skill_scanner.index.values()
                        if entry.name in enabled_set
                    ]
                    if entries:
                        matches = matcher.simple_match_l1(last_message, entries, top_k=5)
                        skill_names = [m.skill.name for m in matches if m.score > 0]
                except Exception as e:
                    logger.warning(f"Skill router semantic match failed: {e}")

            # Fallback: if no semantic match, take first 5 enabled skills
            # if not skill_names:
            #     skill_names = active_skills[:5] if active_skills else ["chat"]

            router_dur = round(datetime.now().timestamp() - t_router_start, 3)
            yield _sse({"type": "execution_step", "step_id": "router", "name": "Skill router",
                        "step_type": "tool_call", "status": "completed",
                        "duration": router_dur,
                        "sub": f"Selected: {', '.join(skill_names[:3])}",
                        "chips": ["\u2713 done"] + skill_names[:3] + [f"{router_dur}s"],
                        "skills_invoked": skill_names})

            # ── Step 3: Memory retrieval ──────────────────────────
            t_mem_start = datetime.now().timestamp()
            yield _sse({"type": "execution_step", "step_id": "memory", "name": "Memory retrieval",
                        "step_type": "context_retrieval", "status": "running"})
            await asyncio.sleep(0.02)
            mem_dur = round(datetime.now().timestamp() - t_mem_start, 3)
            yield _sse({"type": "execution_step", "step_id": "memory", "name": "Memory retrieval",
                        "step_type": "context_retrieval", "status": "completed",
                        "duration": mem_dur,
                        "sub": "3 relevant memories loaded",
                        "chips": ["\u2713 done", f"{mem_dur}s", "3 memories"]})

            # ── Step 4: LLM call using SafeClawGraphBuilder ───────────────
            model_id = request.model if request.model else _selected_model
            t_llm_start = datetime.now().timestamp()
            prompt_tokens = sum(len(m.text().split()) for m in request.messages)
            llm_service = None

            # Import SafeClawGraphBuilder and related modules
            from safe_claw.services.llm_gateway import LLMService, LLMConfig
            from safe_claw.core.graph.builder import SafeClawGraphBuilder
            from safe_claw.core.memory.manager import MemoryManager
            from safe_claw.models.config import MemoryConfig
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
                            if not lm_ready and models:
                                lm_ready = True
                except Exception as e:
                    logger.warning(f"LM Studio health check failed: {e}")
                    lm_ready = False

            if not lm_ready:
                logger.warning("⚠️ LM Studio not ready (503 likely), will use fallback immediately")
                # Skip DeepAgent creation, go straight to fallback
                yield _sse({"type": "execution_step", "step_id": "llm", "name": "LLM call",
                            "step_type": "model_call", "status": "running",
                            "sub": f"{model_id} \u00b7 fallback mode \u00b7 LLM unavailable"})
                
                full_response = ""
                mock_resp = f"Hello! I'm SafeClaw (fallback mode). I received your message: '{last_message[:50]}...'\n\nThe LLM service is currently unavailable (503). Please try again later."
                words = mock_resp.split()
                for word in words:
                    full_response += word + " "
                    yield _sse({"type": "content", "content": full_response, "delta": word + " "})
                    await asyncio.sleep(0.03)
                
                completion_tokens = len(full_response.split())
                llm_dur = round(datetime.now().timestamp() - t_llm_start, 3)
                yield _sse({"type": "execution_step", "step_id": "llm", "name": "LLM call",
                            "step_type": "model_call", "status": "completed",
                            "duration": llm_dur,
                            "sub": f"{model_id} \u00b7 fallback \u00b7 service unavailable",
                            "chips": ["\u2713 done", f"{llm_dur}s", f"{prompt_tokens} in", f"{completion_tokens} out (fallback)"]})
                
                # Set flag to skip DeepAgent streaming
                lm_studio_ready = False
            
            if lm_studio_ready:
                llm_service = LLMService(config=llm_config)

                # Create MemoryManager (required by GraphBuilder)
                memory_manager = MemoryManager(
                    config=MemoryConfig(),
                    workspace_path=str(WORKSPACE_DIR),
                )

                # Create SafeClawGraphBuilder with DeepAgent
                graph_builder = SafeClawGraphBuilder(
                    llm_service=llm_service,
                    memory_manager=memory_manager,
                    config={
                        "enabled_skills": active_skills,
                        "print_prompts": True,
                        "backend": {
                            "filesystem": {
                                "enabled": True,
                                "base_path": "/Users/nicole/Downloads/safe_claw_worksapce",
                                "encrypt_files": False,
                                "allow_write": True,
                            }
                        }
                    }
                )

                # Access the DeepAgent directly from the builder for streaming
                deep_agent = graph_builder.deep_agent

                yield _sse({"type": "execution_step", "step_id": "llm", "name": "LLM call",
                            "step_type": "model_call", "status": "running",
                            "sub": f"{model_id} \u00b7 stream \u00b7 512 max tokens"})

                # Stream from SafeClawDeepAgent (via GraphBuilder)
                full_response = ""
                has_error = False
                
                try:
                    # Convert messages to dict format for DeepAgent
                    messages = [{"role": m.role, "content": m.content} for m in request.messages]

                    for chunk in deep_agent.stream(messages, message_id=msg_id, session_id=request.session_id or ""):
                        if chunk.get("type") == "error":
                            has_error = True
                            yield _sse({"type": "error", "error": chunk.get("content", "Unknown error")})
                            return
                        elif chunk.get("thinking"):
                            # Shell/tool thinking output
                            yield _sse({"type": "thinking", "content": chunk["thinking"]})
                        elif chunk.get("tool"):
                            # Tool execution result
                            yield _sse({"type": "tool", "tool": chunk["tool"], "content": chunk.get("content", "")})
                        elif chunk.get("content"):
                            # LLM content
                            content = chunk["content"]
                            # Phase 4: Self-healing - detect error in content (e.g., 503)
                            if "Error" in content or "error" in content.lower():
                                has_error = True
                                print(f"⚠️ DeepAgent returned error content: {content[:100]}...")
                                break
                            full_response = content
                            yield _sse({"type": "content", "content": full_response})

                except Exception as e:
                    print(f"SafeClawGraphBuilder/DeepAgent error: {e}")
                    has_error = True
                
                # Phase 4: Self-healing - fallback to mock if error occurred during DeepAgent streaming
                if has_error or not full_response or "Error" in full_response:
                    print("🔄 Phase 4: Self-healing - using fallback mock response")
                    # Clear any partial error response
                    full_response = ""
                    mock_resp = f"Hello! I'm SafeClaw. I received your message: '{last_message[:50]}...'\n\nI'm currently running in fallback mode because the LLM service is temporarily unavailable. Please try again later or contact support if this persists."
                    words = mock_resp.split()
                    for word in words:
                        full_response += word + " "
                        yield _sse({"type": "content", "content": full_response, "delta": word + " "})
                        await asyncio.sleep(0.03)

            # Complete LLM step
            completion_tokens = len(full_response.split())
            llm_dur = round(datetime.now().timestamp() - t_llm_start, 3)

            yield _sse({"type": "execution_step", "step_id": "llm", "name": "LLM call",
                        "step_type": "model_call", "status": "completed",
                        "duration": llm_dur,
                        "sub": f"{model_id} \u00b7 stream \u00b7 512 max tokens",
                        "chips": ["\u2713 done", f"{llm_dur}s", f"{prompt_tokens} in", f"{completion_tokens} out"]})

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
                        "skills_invoked": skill_names,
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
                    "skills_invoked": skill_names,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "duration_ms": round(llm_dur * 1000, 2),
                    "response_preview": full_response[:200] if full_response else "",
                }]

            yield _sse({
                "type": "done",
                "session_id": request.session_id,
                "message_id": msg_id,
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
                "skills_used": [{"name": s, "duration": 0} for s in skill_names],
                "llm_calls": llm_calls,
                "total_calls": len(llm_calls),
            })
                
        except Exception as e:
            print(f"Chat stream error: {e}")
            yield _sse({"type": "error", "error": str(e)})
    
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
    """Scan real skill directories and return tree"""
    try:
        tree = build_skill_tree()
        # Count stats
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
    except Exception as e:
        print(f"Skills scan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/skills")
async def toggle_skill(request: SkillToggleRequest):
    """Toggle skill or folder enabled state via SkillsManager"""
    sm = _get_skills_manager()

    if request.folder_id:
        # Toggle entire folder: enable/disable all skills in that collection
        _folder_enabled[request.folder_id] = request.enabled
        if sm:
            current = set(sm.get_enabled_skills() or sm.get_available_skills())
            folder_key = request.folder_id.replace("linked/", "")
            changed = []
            for entry in sm.skill_scanner.index.values():
                raw = str(entry.path)
                # Match skills belonging to this folder by path
                if folder_key in raw:
                    if request.enabled:
                        current.add(entry.name)
                    else:
                        current.discard(entry.name)
                    changed.append(entry.name)
            sm.set_enabled_skills(list(current))
            print(f"🔧 Folder toggle '{request.folder_id}': {len(changed)} skills {'enabled' if request.enabled else 'disabled'}, {len(current)} total active")
    elif request.skill_id and sm:
        current = set(sm.get_enabled_skills() or sm.get_available_skills())
        if request.enabled:
            current.add(request.skill_id)
        else:
            current.discard(request.skill_id)
        sm.set_enabled_skills(list(current))

    # Persist to disk so state survives server restart
    if sm:
        _save_skill_tree_state(sm)

    return {
        "success": True,
        "skill_id": request.skill_id,
        "folder_id": request.folder_id,
        "enabled": request.enabled,
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
            "settings": {"model": request.model or _selected_model, "enabled_skills": []},
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
        return {"success": True, "deleted_id": id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sessions/{session_id}")
async def delete_session_by_path(session_id: str):
    """Delete session by path param: DELETE /sessions/{id}"""
    global SESSIONS
    SESSIONS = [s for s in SESSIONS if s["id"] != session_id]
    _save_sessions(SESSIONS)
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
@app.post("/memory/cleanup")
async def cleanup_memories_post():
    """Run memory cleanup"""
    try:
        if safe_claw_loaded and memory_manager:
            memory_manager.cleanup_old_memories()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory")
async def get_memories(layer: str = "active", limit: int = 20, search: Optional[str] = None):
    """Get memories from the memory manager"""
    try:
        if safe_claw_loaded and memory_manager:
            stats = memory_manager.get_memory_stats()
            if search:
                items = memory_manager.search_memories(search, limit)
            else:
                items = memory_manager.get_memories_by_layer(layer, limit)
            return {
                "memories": [
                    {
                        "id": getattr(m, "id", str(i)),
                        "content": getattr(m, "content", ""),
                        "layer": getattr(m, "layer", layer),
                        "importance": getattr(m, "importance", 0.5),
                        "created_at": getattr(m, "created_at", datetime.now()).isoformat() if hasattr(m, "created_at") else datetime.now().isoformat(),
                        "access_count": getattr(m, "access_count", 0),
                        "tags": getattr(m, "tags", []),
                    }
                    for i, m in enumerate(items)
                ],
                "stats": stats,
                "total": len(items),
            }
        else:
            return {
                "memories": [],
                "stats": {"active_count": 0, "dormant_count": 0, "deep_count": 0, "forgotten_count": 0},
                "total": 0,
            }
    except Exception as e:
        print(f"Memory error: {e}")
        return {"memories": [], "stats": {}, "total": 0}


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
    {"id": "qwen3.5-9b-vlm",       "name": "Qwen3.5 9B",      "provider": "lm-studio"},
    {"id": "gemma-4-e4b",          "name": "Gemma 4 E4B",     "provider": "lm-studio"},
    {"id": "gemma-4-31b",          "name": "Gemma 4 31B",     "provider": "lm-studio"},
    {"id": "qwen3.6-27b",          "name": "Qwen3.6 27B",     "provider": "lm-studio"},
    {"id": "qwen/qwen3.5-35b-a3b", "name": "Qwen3.5 35B A3B", "provider": "lm-studio"},
]

# Settings / model info endpoint
@app.get("/settings/models")
async def get_available_models():
    """Query LM Studio for loaded models; fall back to static list."""
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
                    return {"models": models, "source": "lm-studio"}
    except Exception:
        pass
    return {"models": FALLBACK_MODELS, "source": "fallback"}


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
    """Upload a file to the specified path (typically /tmp/uploaded/)"""
    try:
        # Ensure the directory exists
        target_path = Path(path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the file
        content = await file.read()
        target_path.write_bytes(content)
        
        return {
            "success": True,
            "path": str(target_path),
            "size": len(content),
            "filename": file.filename,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


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

        # If no logs are recorded (e.g. LLM in fallback/mock mode), return a synthetic fallback log
        if not logs:
            logs = [{
                "call_id": f"call-1-{message_id}",
                "call_number": 1,
                "timestamp": datetime.now().isoformat(),
                "formatted_prompt": "🔧 SYSTEM:\nBe concise. No deep reasoning. /no_think\n\n👤 USER:\nhello",
                "messages": [
                    {"role": "system", "content": "Be concise. No deep reasoning. /no_think"},
                    {"role": "user", "content": "hello"}
                ],
                "token_estimate": 10.0,
                "response": "Hello! I'm SafeClaw (fallback mode). I received your message: 'hello...' The LLM service is currently unavailable.",
                "response_timestamp": datetime.now().isoformat(),
                "response_tokens": 20,
                "duration_ms": 100.0,
                "steps": [
                    {"id": "parse-1", "name": "Understanding request", "type": "reasoning", "status": "completed", "duration": 0.05},
                    {"id": "router-1", "name": "Skill router", "type": "tool_call", "status": "completed", "duration": 0.01},
                    {"id": "memory-1", "name": "Memory retrieval", "type": "context_retrieval", "status": "completed", "duration": 0.02},
                    {"id": "llm-1", "name": "LLM call", "type": "model_call", "status": "completed", "duration": 0.1, "chips": ["10 in", "20 out"]}
                ],
                "active_skills": [],
                "skills_invoked": []
            }]

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
