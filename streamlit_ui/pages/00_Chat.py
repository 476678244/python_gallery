"""Chat page for SafeClaw"""

import sys
from pathlib import Path

from streamlit_ui.safe_claw.core.deepagents.official_integration import DeepAgentFactory, get_shell_output, clear_shell_output

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import logging
from typing import Dict, Any
from datetime import datetime
from streamlit_ui.components.skill_tree import get_enabled_skills_from_tree
from streamlit_ui.components.file_dropzone import (
    render_file_dropzone_in_chat,
    get_pending_attachments,
    has_pending_attachments
)

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
    
    # Sidebar: Session Management & Skill Tree
    with st.sidebar:
        st.divider()

        # Session Management Section
        with st.expander("💬 Sessions", expanded=True):
            from streamlit_ui.components.session_manager import (
                create_new_session, save_session_to_file, load_session_from_file,
                list_saved_sessions, delete_session
            )

            # Current session info
            session_id = st.session_state.get('session_id', 'Unknown')[:8]
            message_count = len(st.session_state.get('messages', []))
            st.caption(f"Current: **{session_id}** | {message_count} messages")

            # New Session button
            if st.button("➕ New Session", key="new_session_btn", use_container_width=True):
                create_new_session()
                st.rerun()

            # Session History
            saved_sessions = list_saved_sessions()
            if saved_sessions:
                st.divider()
                st.caption("📁 Session History")
                for session in saved_sessions[:10]:  # Show top 10
                    session_id_short = session['session_id'][:8]
                    msg_count = session['message_count']
                    is_current = session['session_id'] == st.session_state.get('session_id')

                    # Session item row
                    cols = st.columns([4, 1])
                    with cols[0]:
                        label = f"**{session_id_short}** ({msg_count} msgs)" if is_current else f"{session_id_short} ({msg_count} msgs)"
                        if st.button(label, key=f"load_{session['session_id']}", use_container_width=True):
                            if load_session_from_file(session['session_id']):
                                st.rerun()
                    with cols[1]:
                        if not is_current:
                            if st.button("🗑️", key=f"del_{session['session_id']}", help="Delete session"):
                                if delete_session(session['session_id']):
                                    st.rerun()

        # Skill Tree Section
        with st.expander("🌳 Skill Tree", expanded=False):
            # Initialize SkillsManager early if not exists (backend owns state)
            if "skills_manager" not in st.session_state:
                from streamlit_ui.safe_claw.core.skills import SkillsManager
                import os
                external_skills = os.environ.get("SAFECLAW_EXTERNAL_SKILLS", "").split(",")
                if not external_skills or external_skills == [""]:
                    external_skills = [
                        str(Path.home() / "workspace/github/ljg-skills/skills"),
                        "streamlit_ui/skills/private_skills"
                    ]
                st.session_state["skills_manager"] = SkillsManager(external_skills_paths=external_skills)
                logger.info("Initialized SkillsManager for skill tree")
            
            from streamlit_ui.components.skill_tree import render_skill_tree_component
            render_skill_tree_component(
                session_state_key="skill_tree_state",
                use_complete_tree=True
            )
    
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
    
    # File dropzone (collapsible)
    render_file_dropzone_in_chat(
        chat_input_key="chat_file_drop",
        on_file_confirmed=lambda file_data: st.toast(f"📎 File ready: {file_data['name']}")
    )
    
    # Show pending attachments indicator
    if has_pending_attachments():
        attachments = get_pending_attachments()
        st.caption(f"📎 {len(attachments)} file(s) ready to send: " + ", ".join([f['name'] for f in attachments]))
    
    # Chat input
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Get any pending file attachments
        attachments = get_pending_attachments()
        
        # Build message content
        content = user_input
        if attachments:
            file_info = attachments[0]  # Use first attachment for context
            content = f"{user_input}\n\n[Attached file: {file_info['name']} ({file_info['path']})]\n```\n{file_info['content'][:2000]}\n```"
        
        # Add user message to chat
        user_message = {
            "role": "user",
            "content": content,
            "timestamp": datetime.now(),
            "id": len(st.session_state.messages),
            "metadata": {
                "attachments": [{"name": f['name'], "path": f['path'], "size": f['size']} for f in attachments]
            } if attachments else {}
        }
        st.session_state.messages.append(user_message)

        # Auto-save session after user message
        try:
            from streamlit_ui.components.session_manager import save_session_to_file
            save_session_to_file()
        except Exception as save_error:
            logger.warning(f"Auto-save failed: {save_error}")

        # Process with workflow
        try:
            if llm_service:
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
                
                # Get enabled skills from Skill Tree (if configured)
                enabled_skills = get_enabled_skills_from_tree("skill_tree_state")
                if enabled_skills:
                    logger.info(f"Using {len(enabled_skills)} enabled skills from Skill Tree")
                else:
                    logger.info("No Skill Tree configuration found, using all available skills")
                
                config = {
                    "external_skills_paths": external_skills,
                    "enabled_skills": enabled_skills  # Filter by Skill Tree selection
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
                        
                        # Check if this is thinking content (shell output)
                        if chunk.get("thinking"):
                            thinking_output = chunk.get("thinking", "")
                            if not has_started_thinking:
                                has_started_thinking = True
                                thinking_content.append({"tool_name": "Shell Output", "tool_content": thinking_output})
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
                                thinking_content.append({"tool_name": "Shell Output", "tool_content": thinking_output})
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
                    shell_output = get_shell_output()
                    if shell_output:
                        with st.expander("🤔 Agent Thinking Process (Shell Output)", expanded=True):
                            st.markdown("### 🔧 Shell Command Output")
                            for line in shell_output:
                                st.code(line, language=None)
                        # Clear shell output after displaying
                        clear_shell_output()
                    
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
                    "agent": "chat_agent",
                    "execution_path": ["direct_llm"],
                    "processing_time": 0.1
                }
            }
            st.session_state.messages.append(assistant_message)

            # Auto-save session after each message exchange
            try:
                from streamlit_ui.components.session_manager import save_session_to_file
                save_session_to_file()
            except Exception as save_error:
                logger.warning(f"Auto-save failed: {save_error}")

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

            # Auto-save even on error
            try:
                from streamlit_ui.components.session_manager import save_session_to_file
                save_session_to_file()
            except:
                pass

            st.rerun()
    
