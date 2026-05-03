"""Session management utilities for SafeClaw"""

import streamlit as st
import uuid
from datetime import datetime
from typing import Dict, Any, List
import json
from pathlib import Path

def get_session_state() -> Dict[str, Any]:
    """Get current session state"""
    return {
        'session_id': st.session_state.get('session_id'),
        'message_count': len(st.session_state.get('messages', [])),
        'start_time': st.session_state.get('session_start', datetime.now()),
        'last_activity': st.session_state.get('last_activity', datetime.now())
    }

def update_session_activity():
    """Update session activity timestamp"""
    st.session_state.last_activity = datetime.now()

def create_new_session():
    """Create a new session"""
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.session_start = datetime.now()
    st.session_state.last_activity = datetime.now()

def save_session_to_file():
    """Save current session to file"""
    try:
        session_data = {
            'session_id': st.session_state.session_id,
            'messages': st.session_state.messages,
            'session_start': st.session_state.session_start.isoformat(),
            'last_activity': st.session_state.last_activity.isoformat(),
            'selected_model': st.session_state.get('selected_model'),
            'config': st.session_state.safe_claw_config.dict() if st.session_state.get('safe_claw_config') else None
        }
        
        session_dir = Path(st.session_state.workspace_path) / "sessions"
        session_dir.mkdir(exist_ok=True)
        
        session_file = session_dir / f"{st.session_state.session_id}.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f, default=str, indent=2)
        
        return True
    except Exception as e:
        st.error(f"Failed to save session: {e}")
        return False

def load_session_from_file(session_id: str):
    """Load a session from file"""
    try:
        session_dir = Path(st.session_state.workspace_path) / "sessions"
        session_file = session_dir / f"{session_id}.json"
        
        if not session_file.exists():
            return False
        
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        # Restore session state
        st.session_state.session_id = session_data['session_id']
        st.session_state.messages = session_data['messages']
        st.session_state.session_start = datetime.fromisoformat(session_data['session_start'])
        st.session_state.last_activity = datetime.fromisoformat(session_data['last_activity'])
        
        if session_data.get('selected_model'):
            st.session_state.selected_model = session_data['selected_model']
        
        if session_data.get('config'):
            from models.config import SafeClawConfig
            st.session_state.safe_claw_config = SafeClawConfig(**session_data['config'])
        
        return True
    except Exception as e:
        st.error(f"Failed to load session: {e}")
        return False

def list_saved_sessions() -> List[Dict[str, Any]]:
    """List all saved sessions"""
    try:
        session_dir = Path(st.session_state.workspace_path) / "sessions"
        if not session_dir.exists():
            return []
        
        sessions = []
        for session_file in session_dir.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                
                sessions.append({
                    'session_id': session_data['session_id'],
                    'message_count': len(session_data['messages']),
                    'session_start': session_data['session_start'],
                    'last_activity': session_data['last_activity'],
                    'file_path': session_file
                })
            except:
                continue
        
        # Sort by last activity
        sessions.sort(key=lambda x: x['last_activity'], reverse=True)
        return sessions
    except Exception as e:
        st.error(f"Failed to list sessions: {e}")
        return []

def delete_session(session_id: str) -> bool:
    """Delete a saved session"""
    try:
        session_dir = Path(st.session_state.workspace_path) / "sessions"
        session_file = session_dir / f"{session_id}.json"
        
        if session_file.exists():
            session_file.unlink()
            return True
        return False
    except Exception as e:
        st.error(f"Failed to delete session: {e}")
        return False

def export_session() -> str:
    """Export current session as JSON string"""
    try:
        session_data = {
            'session_id': st.session_state.session_id,
            'messages': st.session_state.messages,
            'session_start': st.session_state.session_start.isoformat(),
            'last_activity': st.session_state.last_activity.isoformat(),
            'export_timestamp': datetime.now().isoformat()
        }
        
        return json.dumps(session_data, default=str, indent=2)
    except Exception as e:
        st.error(f"Failed to export session: {e}")
        return ""

def import_session(json_data: str) -> bool:
    """Import session from JSON string"""
    try:
        session_data = json.loads(json_data)
        
        # Validate required fields
        if not all(key in session_data for key in ['session_id', 'messages']):
            st.error("Invalid session data format")
            return False
        
        # Import session
        st.session_state.session_id = session_data['session_id']
        st.session_state.messages = session_data['messages']
        st.session_state.session_start = datetime.now()  # Reset start time
        st.session_state.last_activity = datetime.now()
        
        return True
    except Exception as e:
        st.error(f"Failed to import session: {e}")
        return False

def get_session_summary() -> Dict[str, Any]:
    """Get summary of current session"""
    messages = st.session_state.get('messages', [])
    
    user_messages = [m for m in messages if m.get('role') == 'user']
    assistant_messages = [m for m in messages if m.get('role') == 'assistant']
    
    # Calculate session duration
    start_time = st.session_state.get('session_start', datetime.now())
    duration = datetime.now() - start_time
    
    # Extract topics (simple keyword extraction)
    all_text = " ".join([m.get('content', '') for m in messages])
    words = all_text.lower().split()
    common_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they']
    
    filtered_words = [word for word in words if word not in common_words and len(word) > 2]
    word_freq = {}
    for word in filtered_words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    top_topics = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        'session_id': st.session_state.get('session_id', 'Unknown'),
        'message_count': len(messages),
        'user_message_count': len(user_messages),
        'assistant_message_count': len(assistant_messages),
        'duration_seconds': duration.total_seconds(),
        'duration_formatted': format_duration(duration),
        'top_topics': [{'word': word, 'count': count} for word, count in top_topics],
        'start_time': start_time,
        'last_activity': st.session_state.get('last_activity', datetime.now())
    }

def format_duration(duration) -> str:
    """Format duration as human readable string"""
    total_seconds = int(duration.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds}s"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}m {seconds}s"
    else:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h {minutes}m"
