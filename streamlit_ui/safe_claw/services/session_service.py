"""Session service for SafeClaw"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from uuid import uuid4

from models.session import Session, Message

logger = logging.getLogger(__name__)

class SessionService:
    """Service for managing user sessions and messages"""
    
    def __init__(self, workspace_path: str):
        self.workspace_path = Path(workspace_path)
        self.sessions_dir = self.workspace_path / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        # Active sessions cache
        self.active_sessions: Dict[str, Session] = {}
        
        logger.info("Session service initialized")
    
    def create_session(self, user_id: str = "default") -> Session:
        """Create a new session"""
        session = Session(user_id=user_id)
        
        # Save to file
        self._save_session(session)
        
        # Add to active cache
        self.active_sessions[session.id] = session
        
        logger.info(f"Created new session: {session.id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID"""
        # Check cache first
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # Load from file
        session = self._load_session(session_id)
        if session:
            self.active_sessions[session_id] = session
        
        return session
    
    def update_session(self, session: Session) -> bool:
        """Update a session"""
        session.updated_at = datetime.now()
        
        # Update cache
        self.active_sessions[session.id] = session
        
        # Save to file
        return self._save_session(session)
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        # Remove from cache
        self.active_sessions.pop(session_id, None)
        
        # Delete file
        session_file = self.sessions_dir / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
            logger.info(f"Deleted session: {session_id}")
            return True
        
        return False
    
    def add_message(self, session_id: str, role: str, content: str, 
                   metadata: Dict[str, Any] = None) -> Optional[Message]:
        """Add a message to a session"""
        session = self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            return None
        
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        # Add to session
        session.message_count += 1
        
        # Save session
        self.update_session(session)
        
        # Save message
        self._save_message(message)
        
        logger.info(f"Added message to session {session_id}: {role}")
        return message
    
    def get_messages(self, session_id: str, limit: int = 100) -> List[Message]:
        """Get messages for a session"""
        messages_dir = self.sessions_dir / session_id / "messages"
        if not messages_dir.exists():
            return []
        
        messages = []
        message_files = sorted(messages_dir.glob("*.json"), 
                              key=lambda x: x.stat().st_mtime, 
                              reverse=True)
        
        for message_file in message_files[:limit]:
            try:
                with open(message_file, 'r') as f:
                    data = json.load(f)
                message = Message(**data)
                messages.append(message)
            except Exception as e:
                logger.error(f"Error loading message {message_file}: {e}")
        
        # Sort by timestamp (newest first)
        messages.sort(key=lambda x: x.timestamp, reverse=True)
        return messages
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session"""
        session = self.get_session(session_id)
        if not session:
            return {}
        
        messages = self.get_messages(session_id)
        
        # Count by role
        role_counts = {}
        for message in messages:
            role_counts[message.role] = role_counts.get(message.role, 0) + 1
        
        # Calculate duration
        duration = datetime.now() - session.created_at
        
        return {
            "session_id": session_id,
            "user_id": session.user_id,
            "message_count": session.message_count,
            "role_distribution": role_counts,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "metadata": session.metadata
        }
    
    def list_sessions(self, user_id: str = None, limit: int = 50) -> List[Session]:
        """List sessions"""
        sessions = []
        
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                session = self._load_session(session_file.stem)
                if session:
                    if user_id is None or session.user_id == user_id:
                        sessions.append(session)
            except Exception as e:
                logger.error(f"Error loading session {session_file}: {e}")
        
        # Sort by updated time (newest first)
        sessions.sort(key=lambda x: x.updated_at, reverse=True)
        
        return sessions[:limit]
    
    def cleanup_old_sessions(self, days: int = 30) -> int:
        """Clean up old sessions"""
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0
        
        for session_file in self.sessions_dir.glob("*.json"):
            try:
                session = self._load_session(session_file.stem)
                if session and session.updated_at < cutoff_date:
                    # Delete session and its messages
                    session_dir = self.sessions_dir / session.id
                    if session_dir.exists():
                        import shutil
                        shutil.rmtree(session_dir)
                    
                    session_file.unlink()
                    deleted_count += 1
                    
                    # Remove from cache
                    self.active_sessions.pop(session.id, None)
                    
            except Exception as e:
                logger.error(f"Error cleaning up session {session_file}: {e}")
        
        logger.info(f"Cleaned up {deleted_count} old sessions")
        return deleted_count
    
    def export_session(self, session_id: str, format: str = "json") -> str:
        """Export session data"""
        session = self.get_session(session_id)
        if not session:
            return ""
        
        messages = self.get_messages(session_id)
        
        export_data = {
            "session": session.dict(),
            "messages": [message.dict() for message in messages],
            "exported_at": datetime.now().isoformat()
        }
        
        if format == "json":
            return json.dumps(export_data, indent=2, default=str)
        elif format == "markdown":
            return self._export_to_markdown(export_data)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _save_session(self, session: Session) -> bool:
        """Save session to file"""
        try:
            session_file = self.sessions_dir / f"{session.id}.json"
            with open(session_file, 'w') as f:
                json.dump(session.dict(), f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Error saving session {session.id}: {e}")
            return False
    
    def _load_session(self, session_id: str) -> Optional[Session]:
        """Load session from file"""
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            if not session_file.exists():
                return None
            
            with open(session_file, 'r') as f:
                data = json.load(f)
            
            return Session(**data)
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            return None
    
    def _save_message(self, message: Message) -> bool:
        """Save message to file"""
        try:
            messages_dir = self.sessions_dir / message.session_id / "messages"
            messages_dir.mkdir(parents=True, exist_ok=True)
            
            message_file = messages_dir / f"{message.id}.json"
            with open(message_file, 'w') as f:
                json.dump(message.dict(), f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Error saving message {message.id}: {e}")
            return False
    
    def _export_to_markdown(self, export_data: Dict[str, Any]) -> str:
        """Export session as markdown"""
        session = export_data["session"]
        messages = export_data["messages"]
        
        markdown = f"# Session Export\n\n"
        markdown += f"**Session ID:** {session['id']}\n"
        markdown += f"**User ID:** {session['user_id']}\n"
        markdown += f"**Created:** {session['created_at']}\n"
        markdown += f"**Messages:** {len(messages)}\n\n"
        
        markdown += "---\n\n"
        
        for message in messages:
            role_emoji = {"user": "👤", "assistant": "🤖", "system": "⚙️"}
            emoji = role_emoji.get(message["role"], "❓")
            
            markdown += f"{emoji} **{message['role'].title()}** - {message['timestamp']}\n\n"
            markdown += f"{message['content']}\n\n"
            
            if message.get("tool_calls"):
                markdown += "**Tool Calls:**\n"
                for tool_call in message["tool_calls"]:
                    markdown += f"- {tool_call.get('name', 'Unknown')}\n"
                markdown += "\n"
        
        markdown += f"---\n\n*Exported at {export_data['exported_at']}*\n"
        
        return markdown
    
    def get_active_session_count(self) -> int:
        """Get count of active sessions"""
        return len(self.active_sessions)
    
    def get_total_session_count(self) -> int:
        """Get total count of sessions"""
        return len(list(self.sessions_dir.glob("*.json")))
    
    def clear_cache(self):
        """Clear active session cache"""
        self.active_sessions.clear()
        logger.info("Session cache cleared")
