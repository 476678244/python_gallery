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
    
    try:
        from safe_claw.services.llm_gateway import LLMService
        from safe_claw.core.agents.chat_agent import ChatAgent
        from safe_claw.core.skills.manager import SkillsManager
        from safe_claw.core.memory.manager import MemoryManager
        
        # Initialize services
        llm_service = LLMService()
        skills_manager = SkillsManager()
        memory_manager = MemoryManager()
        
        # Initialize chat agent
        chat_agent = ChatAgent(
            llm_service=llm_service,
            config={
                "personality": "helpful_assistant",
                "max_response_length": 4000,
            }
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


# ── Real skill scanner ────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent.parent  # python_gallery/streamlit_ui
REPO_DIR = BASE_DIR.parent              # python_gallery

SKILL_DIRS = {
    "private":  BASE_DIR / "skills" / "private_skills",
    "linked":   REPO_DIR / "linked_skills",
}

# In-memory toggle state: skill_id -> bool (True = enabled)
_skill_enabled: Dict[str, bool] = {}
_folder_enabled: Dict[str, bool] = {}


def _parse_frontmatter(skill_md: Path) -> Dict[str, Any]:
    """Extract YAML frontmatter from SKILL.md (no external deps)."""
    try:
        text = skill_md.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm_text = text[3:end].strip()
    result: Dict[str, Any] = {}
    current_key = None
    current_list: Optional[list] = None
    for line in fm_text.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        list_item = re.match(r'^\s+-\s+(.*)', line)
        if list_item and current_key and current_list is not None:
            current_list.append(list_item.group(1).strip())
            continue
        kv = re.match(r'^([\w_-]+):\s*(.*)', line)
        if kv:
            current_key = kv.group(1)
            val = kv.group(2).strip()
            if val == "":
                current_list = []
                result[current_key] = current_list
            else:
                current_list = None
                result[current_key] = val
    return result


def _scan_skill_dir(folder_path: Path, collection_id: str) -> Dict[str, Any]:
    """Scan a single collection folder (e.g. private_skills/lyric-image-generation)."""
    children = []
    if not folder_path.exists():
        return {}
    for skill_dir in sorted(folder_path.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        meta = _parse_frontmatter(skill_md) if skill_md.exists() else {}
        skill_id = f"{collection_id}/{skill_dir.name}"
        enabled = _skill_enabled.get(skill_id, True)
        children.append({
            "id": skill_id,
            "name": meta.get("name", skill_dir.name),
            "path": skill_id,
            "is_folder": False,
            "enabled": enabled,
            "expanded": False,
            "children": [],
            "skill_entry": {
                "name": meta.get("name", skill_dir.name),
                "description": meta.get("description", ""),
                "version": meta.get("version", "1.0.0"),
                "author": meta.get("author", ""),
                "category": meta.get("category", ""),
                "tags": meta.get("tags") if isinstance(meta.get("tags"), list) else [],
                "aliases": meta.get("aliases") if isinstance(meta.get("aliases"), list) else [],
            }
        })
    return children


def build_skill_tree() -> List[Dict[str, Any]]:
    """Scan all skill directories and return tree."""
    tree = []

    # ── private_skills: flat folder → one collection node
    private_path = SKILL_DIRS["private"]
    if private_path.exists():
        skills = _scan_skill_dir(private_path, "private")
        if skills:
            folder_id = "private"
            tree.append({
                "id": folder_id,
                "name": "Private Skills",
                "path": folder_id,
                "is_folder": True,
                "enabled": _folder_enabled.get(folder_id, True),
                "expanded": True,
                "children": skills,
            })

    # ── linked_skills: each subdir is a collection (symlink → real repo)
    linked_path = SKILL_DIRS["linked"]
    if linked_path.exists():
        for collection_dir in sorted(linked_path.iterdir()):
            # resolve symlink
            real = collection_dir.resolve() if collection_dir.is_symlink() else collection_dir
            if not real.is_dir():
                continue
            folder_id = f"linked/{collection_dir.name}"
            skills = _scan_skill_dir(real, folder_id)
            if skills:
                tree.append({
                    "id": folder_id,
                    "name": collection_dir.name.replace("_", " ").replace("-", " ").title(),
                    "path": folder_id,
                    "is_folder": True,
                    "enabled": _folder_enabled.get(folder_id, True),
                    "expanded": False,
                    "children": skills,
                })

    return tree

MOCK_SESSIONS = [
    {
        "id": "sess-001",
        "title": "Analyze Macan tire market",
        "status": "active",
        "message_count": 2,
        "settings": {"model": "gemma-4b", "enabled_skills": []},
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "last_activity_at": datetime.now().isoformat()
    }
]


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
                yield f"data: {json.dumps({'type': 'done', 'session_id': request.session_id, 'message_id': msg_id, 'usage': {'prompt_tokens': 50, 'completion_tokens': words, 'total_tokens': 50 + words}})}\n\n"
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
    """Toggle skill or folder enabled state"""
    if request.folder_id:
        _folder_enabled[request.folder_id] = request.enabled
    elif request.skill_id:
        _skill_enabled[request.skill_id] = request.enabled
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
        # Mock for now - integrate with SafeClaw memory system
        return {
            "sessions": MOCK_SESSIONS,
            "total": len(MOCK_SESSIONS),
            "limit": limit,
            "offset": offset,
            "has_more": False
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
        MOCK_SESSIONS.insert(0, new_session)
        
        return {
            "session": new_session,
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get single session by ID"""
    session = next((s for s in MOCK_SESSIONS if s["id"] == session_id), None)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session": session}


@app.patch("/sessions/{session_id}")
async def update_session(session_id: str, request: SessionUpdateRequest):
    """Update a session"""
    session = next((s for s in MOCK_SESSIONS if s["id"] == session_id), None)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if request.title is not None:
        session["title"] = request.title
    if request.status is not None:
        session["status"] = request.status
    if request.settings is not None:
        session["settings"].update(request.settings)
    session["updated_at"] = datetime.now().isoformat()
    return {"session": session, "success": True}


@app.delete("/sessions")
async def delete_session(id: str):
    """Delete session by query param: DELETE /sessions?id=xxx"""
    try:
        global MOCK_SESSIONS
        MOCK_SESSIONS = [s for s in MOCK_SESSIONS if s["id"] != id]
        return {"success": True, "deleted_id": id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sessions/{session_id}")
async def delete_session_by_path(session_id: str):
    """Delete session by path param: DELETE /sessions/{id}"""
    global MOCK_SESSIONS
    MOCK_SESSIONS = [s for s in MOCK_SESSIONS if s["id"] != session_id]
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


@app.post("/memory/cleanup")
async def cleanup_memories():
    """Run memory cleanup"""
    try:
        if safe_claw_loaded and memory_manager:
            memory_manager.cleanup_old_memories()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


# Settings / model info endpoint
@app.get("/settings/models")
async def get_available_models():
    """Get available LLM models"""
    return {
        "models": [
            {"id": "qwen/qwen3.5-35b-a3b", "name": "Qwen 3.5 35B", "provider": "qwen"},
            {"id": "claude-opus-4-7", "name": "Claude Opus 4.7", "provider": "anthropic"},
            {"id": "gemma-4b", "name": "Gemma 4B", "provider": "google"},
            {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai"},
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
