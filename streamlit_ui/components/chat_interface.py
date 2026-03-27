"""Enhanced chat interface component for SafeClaw"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Any, Optional
import time

def render_enhanced_chat_interface(llm_service, memory_manager, graph_builder, safety_checker):
    """Render enhanced chat interface with advanced features"""
    
    # Chat header
    render_chat_header()
    
    # Chat messages container
    render_chat_messages()
    
    # Chat input with enhanced features
    render_enhanced_chat_input(llm_service, memory_manager, graph_builder, safety_checker)
    
    # Chat sidebar
    render_chat_sidebar()

def render_chat_header():
    """Render chat header with status and controls"""
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.title("💬 SafeClaw Chat")
        st.caption("AI-powered assistant with safety-first approach")
    
    with col2:
        # Connection status
        if st.session_state.get('llm_service'):
            st.success("🟢 Connected")
        else:
            st.error("🔴 Disconnected")
    
    with col3:
        # Active session info
        if 'session_id' in st.session_state:
            st.info(f"Session: {st.session_state['session_id'][:8]}...")

def render_chat_messages():
    """Render chat messages with enhanced display"""
    
    # Messages container
    messages_container = st.container()
    
    with messages_container:
        if 'messages' in st.session_state and st.session_state['messages']:
            for i, message in enumerate(st.session_state['messages']):
                # Determine message type and styling
                if message.get('role') == 'user':
                    render_user_message(message, i)
                elif message.get('role') == 'assistant':
                    render_assistant_message(message, i)
                elif message.get('role') == 'system':
                    render_system_message(message, i)
                else:
                    render_generic_message(message, i)
        else:
            # Welcome message
            render_welcome_message()
    
    # Auto-scroll to latest message
    if st.session_state.get('messages'):
        st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)

def render_user_message(message: Dict[str, Any], index: int):
    """Render user message with enhanced features"""
    
    with st.chat_message("user", avatar="👤"):
        # Message content
        st.markdown(message.get('content', ''))
        
        # Message metadata
        if st.checkbox(f"📋 Details (User Message {index + 1})", key=f"user_details_{index}"):
            render_message_metadata(message)
        
        # Message actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📝 Edit", key=f"edit_user_{index}"):
                edit_user_message(index)
        
        with col2:
            if st.button("🗑️ Delete", key=f"delete_user_{index}"):
                delete_message(index)
        
        with col3:
            if st.button("📤 Export", key=f"export_user_{index}"):
                export_message(message, f"user_message_{index}")

def render_assistant_message(message: Dict[str, Any], index: int):
    """Render assistant message with enhanced features"""
    
    # Determine avatar based on agent
    agent_name = message.get('metadata', {}).get('agent', 'assistant')
    avatar = get_agent_avatar(agent_name)
    
    with st.chat_message("assistant", avatar=avatar):
        # Agent info
        if message.get('metadata'):
            metadata = message['metadata']
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if metadata.get('agent'):
                    st.caption(f"🤖 {metadata['agent']}")
                
                if metadata.get('execution_path'):
                    path = " → ".join(metadata['execution_path'])
                    st.caption(f"🔄 Path: {path}")
            
            with col2:
                if metadata.get('processing_time'):
                    st.caption(f"⏱️ {metadata['processing_time']:.2f}s")
        
        # Message content
        content = message.get('content', '')
        
        # Handle different content types
        if content.startswith('```'):
            # Code block
            st.code(content[3:-3], language=get_code_language(content))
        elif content.startswith('!['):
            # Image or other media
            st.markdown(content)
        elif content.startswith('|'):
            # Table
            st.markdown(content)
        else:
            # Regular text
            st.markdown(content)
        
        # Tool calls if present
        if message.get('tool_calls'):
            render_tool_calls(message['tool_calls'])
        
        # Memory context if present
        if message.get('active_memories'):
            render_memory_context(message['active_memories'])
        
        # Message details
        if st.checkbox(f"📋 Details (Assistant Message {index + 1})", key=f"assistant_details_{index}"):
            render_message_metadata(message)
        
        # Message actions
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔄 Regenerate", key=f"regenerate_{index}"):
                regenerate_response(index)
        
        with col2:
            if st.button("📝 Edit", key=f"edit_assistant_{index}"):
                edit_assistant_message(index)
        
        with col3:
            if st.button("🗑️ Delete", key=f"delete_assistant_{index}"):
                delete_message(index)
        
        with col4:
            if st.button("📤 Export", key=f"export_assistant_{index}"):
                export_message(message, f"assistant_message_{index}")

def render_system_message(message: Dict[str, Any], index: int):
    """Render system message"""
    
    with st.chat_message("system", avatar="⚙️"):
        st.markdown(message.get('content', ''))
        
        if st.checkbox(f"📋 Details (System Message {index + 1})", key=f"system_details_{index}"):
            render_message_metadata(message)

def render_generic_message(message: Dict[str, Any], index: int):
    """Render generic message"""
    
    role = message.get('role', 'unknown')
    avatar = get_role_avatar(role)
    
    with st.chat_message(role, avatar=avatar):
        st.markdown(message.get('content', ''))
        
        if st.checkbox(f"📋 Details (Message {index + 1})", key=f"generic_details_{index}"):
            render_message_metadata(message)

def render_welcome_message():
    """Render welcome message for new chat"""
    
    with st.chat_message("assistant", avatar="🦞"):
        st.markdown("👋 Hello! I'm **SafeClaw**, your AI safety assistant!")
        
        st.markdown("""
        I'm here to help you with various tasks while ensuring your safety and privacy. Here's what I can do:
        
        🧠 **Memory Management**: I remember our conversations and learn from them
        🔧 **File Operations**: Read, write, and manage files safely
        💻 **Code Analysis**: Analyze and help with programming tasks
        🛡️ **Safety First**: All operations are checked for safety
        🤖 **Multi-Agent**: I use specialized agents for different tasks
        
        **Try asking me:**
        - "Read the file example.py"
        - "Analyze this Python code: `print('Hello, World!')`"
        - "What do you remember about our conversation?"
        - "Help me understand machine learning"
        
        Let's start chatting! 🚀
        """)

def render_enhanced_chat_input(llm_service, memory_manager, graph_builder, safety_checker):
    """Render enhanced chat input with advanced features"""
    
    # Input container
    with st.container():
        # Input mode selection
        col1, col2 = st.columns([4, 1])
        
        with col2:
            input_mode = st.selectbox(
                "Mode:",
                ["Chat", "Command", "Code"],
                key="input_mode",
                help="Choose input mode"
            )
        
        # Chat input based on mode
        if input_mode == "Chat":
            render_chat_input_mode(llm_service, memory_manager, graph_builder, safety_checker)
        elif input_mode == "Command":
            render_command_input_mode()
        elif input_mode == "Code":
            render_code_input_mode()

def render_chat_input_mode(llm_service, memory_manager, graph_builder, safety_checker):
    """Render standard chat input mode"""
    
    # Chat input with enhanced features
    col1, col2, col3 = st.columns([4, 1, 1])
    
    with col1:
        user_input = st.chat_input(
            "Type your message...",
            key="chat_input",
            max_chars=4000
        )
    
    with col2:
        # Voice input (placeholder)
        st.button("🎤", key="voice_input", help="Voice input (coming soon)")
    
    with col3:
        # File upload
        uploaded_file = st.file_uploader(
            "📎",
            type=["txt", "py", "js", "md", "json"],
            key="file_upload",
            help="Upload file"
        )
    
    # Process input
    if user_input:
        process_user_input(user_input, llm_service, memory_manager, graph_builder, safety_checker)
    
    # Process uploaded file
    if uploaded_file:
        process_uploaded_file(uploaded_file)

def render_command_input_mode():
    """Render command input mode"""
    
    st.subheader("🔧 Command Mode")
    
    # Command templates
    commands = {
        "Read File": "read_file",
        "Write File": "write_file", 
        "List Files": "list_files",
        "Analyze Code": "analyze_code",
        "Memory Search": "search_memory",
        "System Info": "system_info"
    }
    
    selected_command = st.selectbox(
        "Select Command:",
        options=list(commands.keys()),
        key="command_selection"
    )
    
    # Command parameters
    if selected_command:
        render_command_parameters(commands[selected_command])

def render_code_input_mode():
    """Render code input mode"""
    
    st.subheader("💻 Code Mode")
    
    # Language selection
    language = st.selectbox(
        "Language:",
        ["python", "javascript", "java", "cpp", "sql", "html", "css"],
        key="code_language"
    )
    
    # Code input
    code_input = st.text_area(
        "Enter your code:",
        height=200,
        key="code_input",
        help="Enter code to analyze or execute"
    )
    
    # Code actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Analyze", key="analyze_code"):
            analyze_code(code_input, language)
    
    with col2:
        if st.button("🎨 Format", key="format_code"):
            format_code(code_input, language)
    
    with col3:
        if st.button("🔧 Execute", key="execute_code"):
            execute_code(code_input, language)

def render_chat_sidebar():
    """Render chat sidebar with additional features"""
    
    with st.sidebar:
        st.subheader("🛠️ Chat Tools")
        
        # Quick actions
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            clear_chat()
        
        if st.button("💾 Save Session", key="save_session"):
            save_chat_session()
        
        if st.button("📤 Export Chat", key="export_chat"):
            export_chat()
        
        # Chat settings
        st.subheader("⚙️ Chat Settings")
        
        # Memory context
        memory_context = st.slider(
            "Memory Context:",
            min_value=0,
            max_value=10,
            value=3,
            key="memory_context",
            help="Number of memories to include in context"
        )
        
        # Temperature
        temperature = st.slider(
            "Temperature:",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1,
            key="chat_temperature"
        )
        
        # Max tokens
        max_tokens = st.slider(
            "Max Tokens:",
            min_value=100,
            max_value=4000,
            value=2000,
            step=100,
            key="max_tokens"
        )
        
        # Safety level
        safety_level = st.selectbox(
            "Safety Level:",
            ["Strict", "Standard", "Permissive"],
            key="safety_level"
        )
        
        # Session info
        st.subheader("📊 Session Info")
        
        if 'session_id' in st.session_state:
            st.write(f"**Session ID:** {st.session_state['session_id']}")
            st.write(f"**Messages:** {len(st.session_state.get('messages', []))}")
            
            if 'session_start' in st.session_state:
                duration = datetime.now() - st.session_state['session_start']
                st.write(f"**Duration:** {str(duration).split('.')[0]}")
        
        # Active memories
        memory_manager = st.session_state.get('memory_manager')
        if memory_manager:
            st.subheader("🧠 Active Memories")
            
            active_memories = memory_manager.active_layer.get_all_memories()
            if active_memories:
                st.write(f"**Count:** {len(active_memories)}")
                
                for memory in active_memories[:5]:  # Show top 5
                    with st.expander(f"📄 {memory.content[:50]}...", expanded=False):
                        st.write(memory.content)
                        st.write(f"**Importance:** {memory.importance_score:.2f}")
            else:
                st.info("No active memories")

def get_agent_avatar(agent_name: str) -> str:
    """Get avatar emoji for agent"""
    avatars = {
        'chat_agent': '🤖',
        'router_agent': '🔀',
        'memory_agent': '🧠',
        'safety_agent': '🛡️',
        'file_agent': '📁',
        'code_agent': '💻',
        'assistant': '🦞'
    }
    return avatars.get(agent_name, '🤖')

def get_role_avatar(role: str) -> str:
    """Get avatar emoji for role"""
    avatars = {
        'user': '👤',
        'assistant': '🤖',
        'system': '⚙️',
        'tool': '🔧',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️'
    }
    return avatars.get(role, '📝')

def get_code_language(content: str) -> str:
    """Extract language from code block"""
    lines = content.split('\n')
    if lines and lines[0].startswith('```'):
        return lines[0][3:].strip()
    return 'python'

def render_message_metadata(message: Dict[str, Any]):
    """Render message metadata"""
    
    metadata = message.get('metadata', {})
    
    if metadata:
        st.write("**Metadata:**")
        st.json(metadata)
    
    st.write(f"**Timestamp:** {message.get('timestamp', datetime.now())}")
    st.write(f"**ID:** {message.get('id', 'Unknown')}")
    st.write(f"**Role:** {message.get('role', 'Unknown')}")

def render_tool_calls(tool_calls: List[Dict[str, Any]]):
    """Render tool calls made by assistant"""
    
    st.subheader("🔧 Tool Calls")
    
    for i, tool_call in enumerate(tool_calls):
        with st.expander(f"🔧 {tool_call.get('name', 'Unknown Tool')}", expanded=False):
            st.write(f"**Tool:** {tool_call.get('name', 'Unknown')}")
            st.write(f"**Arguments:**")
            st.json(tool_call.get('args', {}))
            
            if 'result' in tool_call:
                st.write(f"**Result:**")
                if isinstance(tool_call['result'], dict):
                    st.json(tool_call['result'])
                else:
                    st.write(str(tool_call['result']))

def render_memory_context(memories: List[Any]):
    """Render memory context used in response"""
    
    st.subheader("🧠 Memory Context")
    
    for i, memory in enumerate(memories):
        with st.expander(f"📄 Memory {i+1} (Score: {getattr(memory, 'score', 'N/A')})", expanded=False):
            st.write(f"**Content:** {memory.content}")
            st.write(f"**Importance:** {memory.importance_score:.2f}")
            st.write(f"**Layer:** {memory.layer.value}")
            st.write(f"**Access Count:** {memory.access_count}")

def process_user_input(user_input: str, llm_service, memory_manager, graph_builder, safety_checker):
    """Process user input through the workflow"""
    
    try:
        # Add user message to chat
        user_message = {
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now(),
            "id": f"user_{len(st.session_state.get('messages', []))}"
        }
        
        if 'messages' not in st.session_state:
            st.session_state['messages'] = []
        
        st.session_state['messages'].append(user_message)
        
        # Safety check
        is_safe, safety_msg, safety_result = safety_checker.check_request(
            user_input, 
            st.session_state.get('session_id', 'default')
        )
        
        if not is_safe:
            # Add safety error message
            error_message = {
                "role": "assistant",
                "content": f"🛡️ **Safety Check Failed**\n\n{safety_msg}",
                "timestamp": datetime.now(),
                "id": f"safety_{len(st.session_state['messages'])}",
                "metadata": {
                    "agent": "safety_agent",
                    "safety_result": safety_result,
                    "blocked": True
                }
            }
            st.session_state['messages'].append(error_message)
            st.error("Request blocked by safety system")
            st.rerun()
            return
        
        # Process through graph
        from core.graph.state import SafeClawState
        
        state = SafeClawState(
            user_input=user_input,
            session_id=st.session_state.get('session_id', 'default'),
            messages=st.session_state['messages'],
            start_time=datetime.now()
        )
        
        # Execute workflow
        with st.spinner("🤔 Thinking..."):
            try:
                config = {"configurable": {"thread_id": st.session_state.get('session_id', 'default')}}
                result = graph_builder.current_graph.invoke(state, config)
                
                # Add assistant response
                assistant_message = {
                    "role": "assistant",
                    "content": result.get('response', 'I apologize, but I could not generate a response.'),
                    "timestamp": datetime.now(),
                    "id": f"assistant_{len(st.session_state['messages'])}",
                    "metadata": {
                        "agent": result.get('current_agent', 'unknown'),
                        "execution_path": result.get('execution_path', []),
                        "active_memories": result.get('active_memories', []),
                        "processing_time": result.get('processing_time', 0)
                    }
                }
                
                st.session_state['messages'].append(assistant_message)
                
            except Exception as e:
                # Add error message
                error_message = {
                    "role": "assistant",
                    "content": f"❌ **Error**\n\nI encountered an error while processing your request: {str(e)}",
                    "timestamp": datetime.now(),
                    "id": f"error_{len(st.session_state['messages'])}",
                    "metadata": {
                        "agent": "error_handler",
                        "error": str(e)
                    }
                }
                st.session_state['messages'].append(error_message)
                st.error(f"Error: {str(e)}")
        
        st.rerun()
        
    except Exception as e:
        st.error(f"Error processing input: {str(e)}")

def process_uploaded_file(uploaded_file):
    """Process uploaded file"""
    
    try:
        # Read file content
        content = uploaded_file.read().decode('utf-8')
        
        # Add file info message
        file_message = {
            "role": "user",
            "content": f"📎 **Uploaded File:** {uploaded_file.name}\n\n```\n{content}\n```",
            "timestamp": datetime.now(),
            "id": f"file_{len(st.session_state.get('messages', []))}",
            "metadata": {
                "file_name": uploaded_file.name,
                "file_size": uploaded_file.size,
                "file_type": uploaded_file.type
            }
        }
        
        if 'messages' not in st.session_state:
            st.session_state['messages'] = []
        
        st.session_state['messages'].append(file_message)
        st.success(f"File uploaded: {uploaded_file.name}")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")

def clear_chat():
    """Clear chat messages"""
    
    if 'messages' in st.session_state:
        st.session_state['messages'] = []
    
    st.success("Chat cleared!")
    st.rerun()

def save_chat_session():
    """Save current chat session"""
    
    session_service = st.session_state.get('session_service')
    
    if session_service and 'messages' in st.session_state:
        try:
            # Save messages to session
            for message in st.session_state['messages']:
                session_service.add_message(
                    st.session_state.get('session_id', 'default'),
                    message['role'],
                    message['content'],
                    message.get('metadata', {})
                )
            
            st.success("Session saved!")
        except Exception as e:
            st.error(f"Error saving session: {str(e)}")
    else:
        st.error("Session service not available")

def export_chat():
    """Export chat history"""
    
    if 'messages' in st.session_state and st.session_state['messages']:
        import json
        
        export_data = {
            "session_id": st.session_state.get('session_id', 'unknown'),
            "exported_at": datetime.now().isoformat(),
            "messages": st.session_state['messages']
        }
        
        st.download_button(
            label="📥 Download Chat History",
            data=json.dumps(export_data, indent=2, default=str),
            file_name=f"safe_claw_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    else:
        st.info("No messages to export")

# Additional helper functions for command and code modes
def render_command_parameters(command_name: str):
    """Render parameters for selected command"""
    
    parameter_templates = {
        "read_file": {"file_path": "Enter file path"},
        "write_file": {"file_path": "Enter file path", "content": "Enter content"},
        "list_files": {"directory": "Enter directory path"},
        "analyze_code": {"code": "Enter code to analyze"},
        "search_memory": {"query": "Enter search query"},
        "system_info": {}
    }
    
    params = parameter_templates.get(command_name, {})
    
    if params:
        st.write("**Parameters:**")
        param_values = {}
        
        for param_name, param_label in params.items():
            param_values[param_name] = st.text_input(param_label, key=f"param_{param_name}")
        
        if st.button("🚀 Execute Command", key="execute_command"):
            execute_command(command_name, param_values)
    else:
        st.info("No parameters required")
        if st.button("🚀 Execute Command", key="execute_command_no_params"):
            execute_command(command_name, {})

def execute_command(command_name: str, params: Dict[str, str]):
    """Execute command with parameters"""
    
    # This would integrate with the skill system
    st.info(f"Executing {command_name} with parameters: {params}")
    # Implementation would go here

def analyze_code(code: str, language: str):
    """Analyze code"""
    
    st.info(f"Analyzing {language} code...")
    # Implementation would go here

def format_code(code: str, language: str):
    """Format code"""
    
    st.info(f"Formatting {language} code...")
    # Implementation would go here

def execute_code(code: str, language: str):
    """Execute code"""
    
    st.warning(f"Executing {language} code (safety checks apply)...")
    # Implementation would go here

# Additional helper functions for message actions
def edit_user_message(index: int):
    """Edit user message"""
    st.info(f"Edit user message {index}")
    # Implementation would go here

def edit_assistant_message(index: int):
    """Edit assistant message"""
    st.info(f"Edit assistant message {index}")
    # Implementation would go here

def regenerate_response(index: int):
    """Regenerate assistant response"""
    st.info(f"Regenerating response for message {index}")
    # Implementation would go here

def delete_message(index: int):
    """Delete message"""
    
    if 'messages' in st.session_state and index < len(st.session_state['messages']):
        st.session_state['messages'].pop(index)
        st.success("Message deleted!")
        st.rerun()

def export_message(message: Dict[str, Any], filename: str):
    """Export single message"""
    
    import json
    
    st.download_button(
        label="📥 Download Message",
        data=json.dumps(message, indent=2, default=str),
        file_name=f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )
