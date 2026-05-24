"""LangGraph state definitions for SafeClaw"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from langchain_core.messages import BaseMessage


class SafeClawState(TypedDict):
    """LangGraph shared state"""
    # Input
    user_input: str
    session_id: str
    
    # Message history
    messages: List[BaseMessage]
    system_prompt: str
    
    # Memory
    active_memories: List[Dict]
    dormant_memories: List[Dict]
    deep_memories: List[Dict]
    
    # Agent execution
    current_agent: str
    agent_outputs: Dict[str, Any]
    
    # Skills/Tools
    tool_calls: List[Dict]
    tool_results: List[Dict]
    
    # Output
    response: str
    stream_chunks: List[str]
    
    # Metadata
    execution_path: List[str]
    start_time: datetime
    needs_confirmation: bool
    confirmed: bool
