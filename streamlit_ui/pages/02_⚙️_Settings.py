"""Settings page for SafeClaw"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import logging
from typing import Dict, Any

from safe_claw.models.config import SafeClawConfig, LLMConfig, SafetyConfig, MemoryConfig

logger = logging.getLogger(__name__)

def render():
    """Render the settings page"""
    logger.info("⚙️ Settings page render started")
    st.title("⚙️ Settings")
    st.caption("Configure SafeClaw behavior and models")
    
    # Load current config
    current_config = st.session_state.get('safe_claw_config')
    logger.info(f"🔍 safe_claw_config in session: {current_config is not None}")
    
    if not current_config:
        logger.error("❌ Configuration not loaded in session state")
        st.error("❌ Configuration not loaded")
        return
    
    logger.info("✅ Configuration loaded successfully")
    st.markdown("---")
    
    # LLM Configuration
    st.subheader("🤖 LLM Configuration")
    
    with st.expander("LLM Settings", expanded=True):
        provider = st.selectbox(
            "LLM Provider",
            ["openai", "anthropic", "ollama"],
            index=["openai", "anthropic", "ollama"].index(current_config.llm.provider),
            key="llm_provider"
        )
        
        if provider == "openai":
            model_options = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"]
        elif provider == "anthropic":
            model_options = ["claude-3-haiku-20240307", "claude-3-sonnet-20240229", "claude-3-opus-20240229"]
        else:  # ollama
            model_options = ["llama2", "llama3", "mistral", "codellama"]
        
        model = st.selectbox(
            "Model",
            model_options,
            index=0,
            key="llm_model"
        )
        
        api_key = st.text_input(
            "API Key",
            value=current_config.llm.api_key or "",
            type="password",
            help="Required for OpenAI and Anthropic. Not needed for Ollama."
        )
        
        base_url = st.text_input(
            "Base URL (Optional)",
            value=current_config.llm.base_url or "",
            help="Custom API endpoint. Leave blank for default."
        )
        
        temperature = st.slider(
            "Temperature",
            0.0, 2.0, current_config.llm.temperature, 0.1,
            help="Higher values make responses more creative, lower values more deterministic."
        )
        
        max_tokens = st.number_input(
            "Max Tokens",
            min_value=100,
            max_value=8000,
            value=current_config.llm.max_tokens,
            step=100
        )
    
    st.markdown("---")
    
    # Safety Configuration
    st.subheader("🛡️ Safety Configuration")
    
    with st.expander("Safety Settings"):
        enable_confirmation = st.checkbox(
            "Enable Confirmation for Dangerous Operations",
            value=current_config.safety.enable_confirmation,
            help="Require user confirmation for potentially dangerous operations."
        )
        
        st.write("**Blacklisted Commands** (comma-separated):")
        blacklist_commands = st.text_area(
            "Commands to block",
            value=", ".join(current_config.safety.blacklist_commands),
            help="These commands will be automatically blocked."
        )
        
        st.write("**Whitelisted Operations** (comma-separated):")
        whitelist_operations = st.text_area(
            "Always-allowed operations",
            value=", ".join(current_config.safety.whitelist_operations),
            help="These operations are always considered safe."
        )
    
    st.markdown("---")
    
    # Memory Configuration
    st.subheader("🧠 Memory Configuration")
    
    with st.expander("Memory Settings"):
        enable_vector_search = st.checkbox(
            "Enable Vector Search",
            value=current_config.memory.enable_vector_search,
            help="Use semantic search with embeddings (requires additional setup)."
        )
        
        active_memory_max = st.number_input(
            "Active Memory Max Count",
            min_value=5,
            max_value=100,
            value=current_config.memory.active_memory_max,
            step=5,
            help="Maximum number of memories to keep in active layer."
        )
        
        dormant_wakeup_threshold = st.slider(
            "Dormant Wakeup Threshold",
            0.0, 1.0, current_config.memory.dormant_wakeup_threshold, 0.1,
            help="Minimum similarity score to wake up dormant memories."
        )
        
        deep_memory_compression = st.selectbox(
            "Deep Memory Compression",
            ["none", "basic", "maximum"],
            index=["none", "basic", "maximum"].index(current_config.memory.deep_memory_compression),
            help="Compression level for deep memory storage."
        )
    
    st.markdown("---")
    
    # Debug Settings
    st.subheader("🔍 Debug Settings")
    
    with st.expander("Debug Options"):
        debug_mode = st.checkbox(
            "Enable Debug Mode",
            value=current_config.debug,
            help="Show detailed execution information and debugging tools."
        )
        
        log_level = st.selectbox(
            "Log Level",
            ["DEBUG", "INFO", "WARNING", "ERROR"],
            index=["DEBUG", "INFO", "WARNING", "ERROR"].index(current_config.log_level)
        )
    
    st.markdown("---")
    
    # Save Configuration
    st.subheader("💾 Save Configuration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Changes", type="primary"):
            # Create new config
            new_config = SafeClawConfig(
                llm=LLMConfig(
                    provider=provider,
                    model=model,
                    api_key=api_key if api_key else None,
                    base_url=base_url if base_url else None,
                    temperature=temperature,
                    max_tokens=int(max_tokens)
                ),
                safety=SafetyConfig(
                    enable_confirmation=enable_confirmation,
                    blacklist_commands=[cmd.strip() for cmd in blacklist_commands.split(",") if cmd.strip()],
                    whitelist_operations=[op.strip() for op in whitelist_operations.split(",") if op.strip()]
                ),
                memory=MemoryConfig(
                    enable_vector_search=enable_vector_search,
                    active_memory_max=int(active_memory_max),
                    dormant_wakeup_threshold=dormant_wakeup_threshold,
                    deep_memory_compression=deep_memory_compression
                ),
                debug=debug_mode,
                log_level=log_level
            )
            
            # Update session state
            st.session_state.safe_claw_config = new_config
            
            # Reinitialize services with new config
            try:
                # Update LLM service
                st.session_state.llm_service = LLMService(new_config.llm)
                
                # Update memory manager
                st.session_state.memory_manager = MemoryManager(
                    new_config.memory,
                    str(st.session_state.workspace_path)
                )
                
                # Update graph builder
                st.session_state.graph_builder = SafeClawGraphBuilder(
                    st.session_state.llm_service,
                    st.session_state.memory_manager,
                    {"debug": new_config.debug}
                )
                
                # Recreate graph
                st.session_state.current_graph = st.session_state.graph_builder.create_graph("advanced")
                
                st.success("✅ Configuration saved and services reinitialized!")
                
            except Exception as e:
                st.error(f"❌ Error reinitializing services: {e}")
    
    with col2:
        if st.button("🔄 Reset to Defaults"):
            # Reset to default configuration
            default_config = SafeClawConfig(
                llm=LLMConfig(
                    provider="openai",
                    model="gpt-3.5-turbo",
                    api_key=None,
                    temperature=0.7,
                    max_tokens=2000
                )
            )
            
            st.session_state.safe_claw_config = default_config
            st.success("✅ Reset to default configuration!")
            st.rerun()
    
    with col3:
        if st.button("📋 Export Config"):
            config_dict = current_config.dict()
            st.json(config_dict)
    
    st.markdown("---")
    
    # Configuration Status
    st.subheader("📊 Configuration Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Current Services:**")
        llm_status = "✅ Connected" if st.session_state.get('llm_service') else "❌ Not Connected"
        st.write(f"LLM Service: {llm_status}")
        
        memory_status = "✅ Active" if st.session_state.get('memory_manager') else "❌ Not Active"
        st.write(f"Memory Manager: {memory_status}")
        
        graph_status = "✅ Ready" if st.session_state.get('current_graph') else "❌ Not Ready"
        st.write(f"Workflow Graph: {graph_status}")
    
    with col2:
        st.write("**Workspace Info:**")
        st.write(f"Path: {st.session_state.workspace_path}")
        st.write(f"Session ID: {st.session_state.session_id[:8]}...")
        
        if st.session_state.get('memory_manager'):
            stats = st.session_state.memory_manager.get_memory_stats()
            total_memories = stats['active_count'] + stats['dormant_count'] + stats['deep_count']
            st.write(f"Total Memories: {total_memories}")
    
    # Test Configuration
    st.markdown("---")
    st.subheader("🧪 Test Configuration")
    
    if st.button("Test LLM Connection"):
        if st.session_state.get('llm_service'):
            with st.spinner("Testing LLM connection..."):
                try:
                    test_messages = [{"role": "user", "content": "Hello! This is a test message."}]
                    response = st.session_state.llm_service.invoke(test_messages)
                    st.success(f"✅ LLM connection successful! Response: {response[:100]}...")
                except Exception as e:
                    st.error(f"❌ LLM connection failed: {e}")
        else:
            st.error("❌ LLM service not initialized")
    
    if st.button("Test Memory System"):
        if st.session_state.get('memory_manager'):
            with st.spinner("Testing memory system..."):
                try:
                    # Add test memory
                    memory_id = st.session_state.memory_manager.add_memory(
                        content="This is a test memory for configuration validation.",
                        importance_score=0.5,
                        keywords=["test", "config"]
                    )
                    
                    # Search for it
                    results = st.session_state.memory_manager.search_memories("test", 5)
                    
                    if results and memory_id:
                        st.success("✅ Memory system working correctly!")
                    else:
                        st.error("❌ Memory system test failed")
                        
                except Exception as e:
                    st.error(f"❌ Memory system test failed: {e}")
        else:
            st.error("❌ Memory manager not initialized")
