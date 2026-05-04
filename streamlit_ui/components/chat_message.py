"""Chat message component for SafeClaw"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any

def format_timestamp(timestamp, fmt='%H:%M') -> str:
    """Format timestamp, handling both datetime objects and ISO format strings"""
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp)
        except (ValueError, TypeError):
            return timestamp  # Return as-is if parsing fails
    if isinstance(timestamp, datetime):
        return timestamp.strftime(fmt)
    return str(timestamp)

def render_message(message: Dict[str, Any]):
    """Render a chat message"""
    role = message.get("role", "user")
    content = message.get("content", "")
    timestamp = message.get("timestamp", datetime.now())
    metadata = message.get("metadata", {})
    
    if role == "user":
        with st.chat_message("user"):
            st.write(content)
            st.caption(f"Sent {format_timestamp(timestamp)}")
    
    elif role == "assistant":
        with st.chat_message("assistant"):
            st.write(content)
            
            # Show metadata if available
            if metadata:
                with st.expander("🔍 Details", expanded=False):
                    if "agent" in metadata:
                        st.write(f"**Agent:** {metadata['agent']}")
                    
                    if "execution_path" in metadata:
                        st.write(f"**Execution Path:** {' → '.join(metadata['execution_path'])}")
                    
                    if "processing_time" in metadata:
                        st.write(f"**Processing Time:** {metadata['processing_time']:.2f}s")
                    
                    if "tool_calls" in metadata and metadata["tool_calls"]:
                        st.write("**Tool Calls:**")
                        for tool_call in metadata["tool_calls"]:
                            st.write(f"- {tool_call.get('name', 'Unknown')}")
    
    elif role == "system":
        with st.chat_message("assistant", avatar="🤖"):
            st.info(content)
            st.caption(f"System message at {format_timestamp(timestamp)}")

def render_streaming_message(content: str, agent: str = "assistant"):
    """Render a streaming message placeholder"""
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Simulate streaming (would be replaced with actual streaming)
        for chunk in content.split():
            full_response += chunk + " "
            message_placeholder.markdown(full_response + "▌")
            st.sleep(0.05)  # Simulate delay
        
        message_placeholder.markdown(full_response)
        st.caption(f"Response from {agent}")

def render_error_message(error: str, timestamp: datetime = None):
    """Render an error message"""
    with st.chat_message("assistant", avatar="❌"):
        st.error(error)
        if timestamp:
            st.caption(f"Error at {format_timestamp(timestamp)}")

def render_confirmation_prompt(prompt: str, callback=None):
    """Render a confirmation prompt for dangerous operations"""
    with st.chat_message("assistant", avatar="⚠️"):
        st.warning(prompt)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Confirm", key="confirm_action"):
                if callback:
                    callback(True)
                return True
        
        with col2:
            if st.button("❌ Cancel", key="cancel_action"):
                if callback:
                    callback(False)
                return False
    
    return None

def render_tool_result(tool_name: str, result: Any, success: bool = True):
    """Render tool execution result"""
    icon = "✅" if success else "❌"
    
    with st.chat_message("assistant", avatar=icon):
        st.write(f"**{tool_name}**")
        
        if success:
            if isinstance(result, str):
                st.write(result)
            elif isinstance(result, dict):
                st.json(result)
            else:
                st.write(str(result))
        else:
            st.error(f"Tool execution failed: {result}")

def render_memory_context(memories: list):
    """Render memory context in chat"""
    if not memories:
        return
    
    with st.expander("🧠 Relevant Memories", expanded=False):
        for i, memory in enumerate(memories[:3], 1):  # Show top 3
            st.write(f"{i}. {memory.get('content', '')[:100]}{'...' if len(memory.get('content', '')) > 100 else ''}")
            st.caption(f"Importance: {memory.get('importance_score', 0):.1f}")

def render_thinking_indicator():
    """Render a thinking indicator"""
    with st.chat_message("assistant"):
        st.write("🤔 Thinking...")
        # Add a spinner
        with st.spinner("Processing..."):
            st.sleep(0.1)  # Minimal delay to show the spinner
