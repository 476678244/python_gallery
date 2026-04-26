"""Chat page for SafeClaw"""

import sys
from pathlib import Path

from streamlit_ui.safe_claw.core.deepagents.official_integration import DeepAgentFactory

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import logging
from typing import Dict, Any, Iterator
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage

from components.session_manager import get_session_state
from streamlit_ui.safe_claw.core.graph.state import SafeClawState

logger = logging.getLogger(__name__)

# Simple message renderer as fallback
def simple_render_message(message: Dict[str, Any]):
    """Simple message renderer if component import fails"""
    role = message.get("role", "user")
    content = message.get("content", "")
    
    if role == "user":
        with st.chat_message("user"):
            st.write(content)
    elif role == "assistant":
        with st.chat_message("assistant"):
            st.write(content)
    else:
        st.write(f"{role}: {content}")

# Try to import component, use fallback if it fails
try:
    from streamlit_ui.components.chat_message import render_message
except ImportError:
    logger.warning("Could not import render_message component, using fallback")
    render_message = simple_render_message

def render():
    """Render the chat page"""
    st.title("💬 Chat with SafeClaw")
    st.caption("Your AI Safety Assistant")
    
    # Check if services are available
    llm_service = st.session_state.get('llm_service')
    memory_manager = st.session_state.get('memory_manager')
    
    if not llm_service:
        st.warning("⚠️ LLM service is not available. Running in demo mode.")
        st.info("📝 Configure your LLM in Settings to enable full functionality.")
        # Don't return - allow the page to render with limited functionality
    
    if not memory_manager:
        st.error("❌ Memory service not available. Please check your configuration.")
        return
    
    # Display chat messages
    messages_container = st.container()
    with messages_container:
        # Show welcome message if chat is empty
        if not st.session_state.messages:
            st.chat_message("assistant").write("👋 Hello! I'm SafeClaw, your AI safety assistant. How can I help you today?")
        
        # Display existing messages
        for message in st.session_state.messages:
            render_message(message)
    
    # Chat input
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Add user message to chat
        user_message = {
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now(),
            "id": len(st.session_state.messages)
        }
        st.session_state.messages.append(user_message)
        
        # Create state for LangGraph
        state = SafeClawState(
            user_input=user_input,
            session_id=st.session_state.session_id,
            messages=[HumanMessage(content=msg["content"]) if msg["role"] == "user" 
                     else AIMessage(content=msg["content"]) for msg in st.session_state.messages[:-1]],
            start_time=datetime.now()
        )
        
        # Process with workflow
        try:
            if st.session_state.get('current_graph') and llm_service:
                # Use streaming response
                messages = [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.messages]
                
                # Create SafeClawDeepAgent with memory and external skills paths
                import os
                external_skills = os.environ.get("SAFECLAW_EXTERNAL_SKILLS", "").split(",")
                if not external_skills or external_skills == [""]:
                    # Default relative paths
                    external_skills = [
                        str(Path.home() / "workspace/github/ljg-skills/skills"),
                        "streamlit_ui/skills/private_skills"
                    ]
                
                config = {
                    "external_skills_paths": external_skills
                }
                deep_agent = DeepAgentFactory.create_agent(llm_service, config)
                
                # Display assistant message container with streaming
                with st.chat_message("assistant"):
                    # Show thinking indicator immediately
                    thinking_placeholder = st.empty()
                    with thinking_placeholder.container():
                        st.markdown("""
                        <div style="padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 0.5rem; margin-bottom: 1rem;">
                            <div style="display: flex; align-items: center; color: white;">
                                <div style="margin-right: 0.5rem;">🤔</div>
                                <div>
                                    <div style="font-weight: bold;">SafeClaw is thinking...</div>
                                    <div style="font-size: 0.8rem; opacity: 0.8;">Analyzing your request and preparing response</div>
                                </div>
                                <div style="margin-left: auto;">
                                    <div class="thinking-dots">
                                        <span style="animation: thinking 1.4s infinite ease-in-out both;">.</span>
                                        <span style="animation: thinking 1.4s infinite ease-in-out both; animation-delay: 0.2s;">.</span>
                                        <span style="animation: thinking 1.4s infinite ease-in-out both; animation-delay: 0.4s;">.</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <style>
                        .thinking-dots span {
                            display: inline-block;
                            font-size: 1.5rem;
                            margin-left: 0.2rem;
                        }
                        @keyframes thinking {
                            0%, 60%, 100% { opacity: 0.3; transform: scale(1); }
                            30% { opacity: 1; transform: scale(1.2); }
                        }
                        </style>
                        """, unsafe_allow_html=True)
                    
                    response_placeholder = st.empty()
                    response_chunks = []
                    full_response = ""
                    thinking_content = []
                    has_started_thinking = False

                    for chunk in deep_agent.stream(messages):
                        # Check if this is a tool message
                        if chunk.get("tool"):
                            tool_name = chunk.get("tool")
                            tool_content = chunk.get("content", "")

                            # Update thinking indicator to show tool usage
                            if not has_started_thinking:
                                has_started_thinking = True
                                thinking_content.append({"tool_name": tool_name, "tool_content": tool_content})
                                with thinking_placeholder.container():
                                    st.markdown("""
                                    <div style="padding: 1rem; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 0.5rem; margin-bottom: 1rem;">
                                        <div style="display: flex; align-items: center; color: white;">
                                            <div style="margin-right: 0.5rem;">🔧</div>
                                            <div>
                                                <div style="font-weight: bold;">Using tools to help...</div>
                                                <div style="font-size: 0.8rem; opacity: 0.8;">Processing with specialized capabilities</div>
                                            </div>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    with st.expander("🤔 Agent Thinking Process", expanded=True):
                                        for item in thinking_content:
                                            st.markdown(f"🔧 **{item['tool_name']}**")
                                            with st.container():
                                                st.code(item['tool_content'], language=None)
                                            st.divider()
                            else:
                                thinking_content.append({"tool_name": tool_name, "tool_content": tool_content})
                                with thinking_placeholder.container():
                                    st.markdown("""
                                    <div style="padding: 1rem; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); border-radius: 0.5rem; margin-bottom: 1rem;">
                                        <div style="display: flex; align-items: center; color: white;">
                                            <div style="margin-right: 0.5rem;">🔧</div>
                                            <div>
                                                <div style="font-weight: bold;">Using tools to help...</div>
                                                <div style="font-size: 0.8rem; opacity: 0.8;">Processing with specialized capabilities</div>
                                            </div>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    with st.expander("🤔 Agent Thinking Process", expanded=True):
                                        for item in thinking_content:
                                            st.markdown(f"🔧 **{item['tool_name']}**")
                                            with st.container():
                                                st.code(item['tool_content'], language=None)
                                            st.divider()
                            continue
                        
                        # Handle regular content chunks - clear thinking indicator when response starts
                        chunk_content = chunk.get("content", "")
                        if chunk_content:
                            if not has_started_thinking:
                                # Clear the thinking indicator when actual response starts
                                thinking_placeholder.empty()
                                has_started_thinking = True
                            
                            response_chunks.append(chunk_content)
                            full_response += chunk_content
                            response_placeholder.write(full_response)
                    
                    # Clear thinking indicator if it's still showing
                    if not has_started_thinking:
                        thinking_placeholder.empty()
                    
                    # Get and display shell output as thinking content
                    shell_output = deep_agent.get_thinking_content()
                    if shell_output:
                        with st.expander("🤔 Agent Thinking Process (Shell Output)", expanded=True):
                            st.markdown("### 🔧 Shell Command Output")
                            for line in shell_output:
                                st.code(line, language=None)
                        # Clear thinking content after displaying
                        deep_agent.clear_thinking_content()
                    
                    response = full_response
            else:
                # Fallback to blocking call with enhanced thinking UI
                with st.chat_message("assistant"):
                    thinking_placeholder = st.empty()
                    with thinking_placeholder.container():
                        st.markdown("""
                        <div style="padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 0.5rem; margin-bottom: 1rem;">
                            <div style="display: flex; align-items: center; color: white;">
                                <div style="margin-right: 0.5rem;">🤔</div>
                                <div>
                                    <div style="font-weight: bold;">SafeClaw is thinking...</div>
                                    <div style="font-size: 0.8rem; opacity: 0.8;">Analyzing your request and preparing response</div>
                                </div>
                                <div style="margin-left: auto;">
                                    <div class="thinking-dots">
                                        <span style="animation: thinking 1.4s infinite ease-in-out both;">.</span>
                                        <span style="animation: thinking 1.4s infinite ease-in-out both; animation-delay: 0.2s;">.</span>
                                        <span style="animation: thinking 1.4s infinite ease-in-out both; animation-delay: 0.4s;">.</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <style>
                        .thinking-dots span {
                            display: inline-block;
                            font-size: 1.5rem;
                            margin-left: 0.2rem;
                        }
                        @keyframes thinking {
                            0%, 60%, 100% { opacity: 0.3; transform: scale(1); }
                            30% { opacity: 1; transform: scale(1.2); }
                        }
                        </style>
                        """, unsafe_allow_html=True)
                    
                    # Process the response
                    messages = [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.messages]
                    response = llm_service.invoke(messages) if llm_service else "I'm SafeClaw AI assistant running in demo mode. Please configure an LLM in Settings for full functionality."
                    
                    # Clear thinking indicator and show response
                    thinking_placeholder.empty()
                    st.write(response)
            
            # Add assistant message to chat
            assistant_message = {
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now(),
                "id": len(st.session_state.messages),
                "metadata": {
                    "agent": "chat_agent" if st.session_state.get('current_graph') else "mock_agent",
                    "execution_path": ["direct_llm"],
                    "processing_time": 0.1
                }
            }
            st.session_state.messages.append(assistant_message)
            
            # Rerun to display the new message
            st.rerun()
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_message = {
                "role": "assistant",
                "content": f"❌ Sorry, I encountered an error: {str(e)}",
                "timestamp": datetime.now(),
                "id": len(st.session_state.messages)
            }
            st.session_state.messages.append(error_message)
            st.rerun()
    
    # Add some helpful tips at the bottom
    with st.expander("💡 Tips for using SafeClaw"):
        st.markdown("""
        **Memory Commands:**
        - "Remember that [information]" - Store important information
        - "Search for [topic]" - Find relevant memories
        - "What do you remember about [topic]?" - Recall memories
        
        **General Chat:**
        - Ask questions about any topic
        - Request help with tasks
        - Have natural conversations
        
        **Safety Features:**
        - All operations are subject to safety checks
        - File operations require confirmation
        - Your data is stored locally
        """)
    
    # Display execution info if debug mode is on
    if st.session_state.safe_claw_config.debug and st.session_state.messages:
        last_message = st.session_state.messages[-1]
        if last_message["role"] == "assistant" and "metadata" in last_message:
            metadata = last_message["metadata"]
            with st.expander("🔍 Debug Info"):
                st.json({
                    "Agent": metadata.get("agent"),
                    "Execution Path": metadata.get("execution_path"),
                    "Processing Time": f"{metadata.get('processing_time', 0):.2f}s"
                })

def stream_response(state: SafeClawState) -> Iterator[str]:
    """Stream response from the workflow (future enhancement)"""
    # This would be used for streaming responses
    # For now, we'll use the synchronous approach
    config = {"configurable": {"thread_id": st.session_state.session_id}}
    
    try:
        # Stream the response (when LangGraph streaming is properly set up)
        for chunk in st.session_state.current_graph.stream(state, config):
            if "response" in chunk:
                yield chunk["response"]
    except Exception as e:
        logger.error(f"Error in streaming: {e}")
        yield f"Error: {str(e)}"
