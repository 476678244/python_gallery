"""
SafeClaw FastAPI Backend
Bridges Next.js UI with SafeClaw Python Core
"""

import asyncio
import json
import sys
import os
import re
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

import httpx

from fastapi import FastAPI, HTTPException, Request
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
        from streamlit_ui.safe_claw.services.llm_gateway import LLMService
        from streamlit_ui.safe_claw.core.agents.chat_agent import ChatAgent
        from streamlit_ui.safe_claw.core.skills.manager import SkillsManager
        from streamlit_ui.safe_claw.core.memory.manager import MemoryManager

        llm_service = LLMService()
        if not skills_manager:
            skills_manager = SkillsManager()
            if not skills_manager.skill_scanner.loaded:
                skills_manager.skill_scanner.scan_all_skills()
        from streamlit_ui.safe_claw.models.config import MemoryConfig
        memory_manager = MemoryManager(
            config=MemoryConfig(),
            workspace_path=str(DATA_DIR),
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
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    session_id: Optional[str] = None
    enabled_skills: List[str] = Field(default_factory=list)
    model: str = "gemma-4b"
    temperature: float = 0.7
    stream: bool = True


class SessionCreateRequest(BaseModel):
    title: Optional[str] = "New Chat"
    model: str = "gemma-4b"


class SessionUpdateRequest(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class SkillToggleRequest(BaseModel):
    skill_id: Optional[str] = None
    folder_id: Optional[str] = None
    enabled: bool = True


# ── Skills tree builder using safe_claw SkillsManager ────────────────────────

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
        from streamlit_ui.safe_claw.core.skills.manager import SkillsManager as SM
        skills_manager = SM()
        if not skills_manager.skill_scanner.loaded:
            skills_manager.skill_scanner.scan_all_skills()
        print(f"✅ SkillsManager loaded: {skills_manager.get_skill_count()} skills")
    except Exception as e:
        print(f"⚠️  SkillsManager init failed: {e}")
        skills_manager = None
    return skills_manager


# In-memory folder toggle state (skills use SkillsManager.set_enabled_skills)
_folder_enabled: Dict[str, bool] = {}


def build_skill_tree() -> List[Dict[str, Any]]:
    """Build skill tree from SkillsManager.skill_scanner.index."""
    sm = _get_skills_manager()
    if not sm:
        return []

    # Get enabled skill names from manager state
    enabled_skills = sm.get_enabled_skills()
    enabled_set = set(enabled_skills)

    # Group index entries by collection (derived from path)
    project_root = Path(__file__).parent.parent.parent  # python_gallery
    collections: Dict[str, List[Dict]] = {}

    for entry in sm.skill_scanner.index.values():
        skill_path = Path(entry.path)
        # Determine collection label from path segments
        try:
            rel = skill_path.relative_to(project_root)
            parts = rel.parts
            # linked_skills/<collection>/<skill>  or  streamlit_ui/skills/<type>/<skill>
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

# ── File-backed session storage ──────────────────────────────────────────────

DATA_DIR = Path(__file__).parent.parent / ".safeclaw_data"
SESSIONS_FILE = DATA_DIR / "sessions.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_sessions() -> List[Dict[str, Any]]:
    if SESSIONS_FILE.exists():
        try:
            return json.loads(SESSIONS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save_sessions(sessions: List[Dict[str, Any]]) -> None:
    SESSIONS_FILE.write_text(json.dumps(sessions, indent=2, ensure_ascii=False), encoding="utf-8")


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


# Chat streaming endpoint
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat responses from SafeClaw"""
    
    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # Get last user message
            last_message = None
            for msg in reversed(request.messages):
                if msg.role == "user":
                    last_message = msg.content
                    break
            
            if not last_message:
                yield f"data: {json.dumps({'type': 'error', 'error': 'No user message found'})}\n\n"
                return
            
            # Resolve enabled skills from SkillsManager
            sm = _get_skills_manager()
            active_skills = sm.get_enabled_skills() if sm else (request.enabled_skills or [])

            # Try real LM Studio first, fall back to mock
            lm_studio_url = "http://192.168.50.30:1234"
            model_id = request.model if request.model not in ("gemma-4b", "") else "qwen3.5-9b-vlm"
            
            lm_ok = False
            try:
                payload = {
                    "model": model_id,
                    "messages": [{"role": m.role, "content": m.content} for m in request.messages],
                    "stream": True,
                    "temperature": request.temperature,
                    "max_tokens": 512,
                }
                full_response = ""
                async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
                    async with client.stream(
                        "POST",
                        f"{lm_studio_url}/v1/chat/completions",
                        json=payload,
                        headers={"Authorization": "Bearer lm-studio"},
                    ) as resp:
                        if resp.status_code != 200:
                            raise RuntimeError(f"LM Studio returned {resp.status_code}")
                        lm_ok = True
                        async for line in resp.aiter_lines():
                            if not line.startswith("data:"):
                                continue
                            raw = line[5:].strip()
                            if raw == "[DONE]":
                                break
                            try:
                                evt = json.loads(raw)
                                delta = evt["choices"][0]["delta"].get("content", "")
                                if delta:
                                    full_response += delta
                                    yield f"data: {json.dumps({'type': 'content', 'content': full_response, 'delta': delta})}\n\n"
                            except Exception:
                                continue
                msg_id = f"msg-{datetime.now().timestamp()}"
                words = len(full_response.split())
                yield f"data: {json.dumps({'type': 'done', 'session_id': request.session_id, 'message_id': msg_id, 'skills_used': active_skills, 'usage': {'prompt_tokens': 50, 'completion_tokens': words, 'total_tokens': 50 + words}})}\n\n"
            except Exception as e:
                print(f"LM Studio error: {e}")
                if not lm_ok:
                    # Fall back to mock
                    async for chunk in mock_stream_response(last_message):
                        yield chunk
                
        except Exception as e:
            print(f"Chat stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


async def mock_stream_response(user_message: str):
    """Generate mock streaming response"""
    import json
    
    # Mock thinking steps
    thinking_steps = [
        ("Understanding request", 0.5),
        ("Analyzing context", 0.8),
        ("Formulating response", 1.2)
    ]
    
    for step, duration in thinking_steps:
        yield f"data: {json.dumps({'type': 'thinking', 'step': step.replace(' ', '-'), 'name': step, 'status': 'running'})}\n\n"
        await asyncio.sleep(duration * 0.3)
        yield f"data: {json.dumps({'type': 'thinking', 'step': step.replace(' ', '-'), 'name': step, 'status': 'completed', 'duration': duration})}\n\n"
    
    # Mock response content
    mock_response = f"I received your message: '{user_message[:50]}...'\n\nThis is a mock response from SafeClaw API. The full integration will use the actual SafeClaw Python core for processing."
    
    # Stream content
    words = mock_response.split()
    full_content = ""
    for word in words:
        full_content += word + " "
        yield f"data: {json.dumps({'type': 'content', 'content': full_content, 'delta': word + ' '})}\n\n"
        await asyncio.sleep(0.05)
    
    # Done event
    yield f"data: {json.dumps({'type': 'done', 'session_id': 'mock-session', 'message_id': f'msg-{datetime.now().timestamp()}', 'usage': {'prompt_tokens': 50, 'completion_tokens': len(words), 'total_tokens': 50 + len(words)}, 'timing': {'start_time': datetime.now().timestamp(), 'end_time': datetime.now().timestamp(), 'total_duration': 2.5}, 'execution_path': [{'name': 'Understand', 'duration': 0.5}, {'name': 'Analyze', 'duration': 0.8}, {'name': 'Respond', 'duration': 1.2}], 'skills_used': [{'name': 'chat', 'duration': 2.5}]})}\n\n"


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
            for entry in sm.skill_scanner.index.values():
                raw = str(entry.path)
                # Match skills belonging to this folder by path
                folder_key = request.folder_id.replace("linked/", "")
                if folder_key in raw:
                    if request.enabled:
                        current.add(entry.name)
                    else:
                        current.discard(entry.name)
            sm.set_enabled_skills(list(current))
    elif request.skill_id and sm:
        current = set(sm.get_enabled_skills() or sm.get_available_skills())
        if request.enabled:
            current.add(request.skill_id)
        else:
            current.discard(request.skill_id)
        sm.set_enabled_skills(list(current))

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
            "settings": {"model": request.model, "enabled_skills": []},
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
    {"id": "qwen/qwen3.5-35b-a3b", "name": "Qwen 3.5 35B", "provider": "lm-studio"},
    {"id": "claude-opus-4-7", "name": "Claude Opus 4.7", "provider": "anthropic"},
    {"id": "gemma-4b", "name": "Gemma 4B", "provider": "google"},
    {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai"},
]

# Settings / model info endpoint
@app.get("/settings/models")
async def get_available_models():
    """Query LM Studio for loaded models; fall back to static list."""
    try:
        async with httpx.AsyncClient(timeout=3.0, trust_env=False) as client:
            resp = await client.get("http://192.168.50.30:1234/v1/models")
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
