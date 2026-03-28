"""SafeClaw Main Application"""

import sys
from pathlib import Path

# Add project root to Python path (where streamlit_ui package can be found)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import logging
from typing import Dict, Any
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import SafeClaw components
from streamlit_ui.safe_claw.models.config import SafeClawConfig, LLMConfig
from streamlit_ui.safe_claw.services.llm_gateway import LLMService
from streamlit_ui.safe_claw.core.memory.manager import MemoryManager
from streamlit_ui.safe_claw.core.graph.builder import SafeClawGraphBuilder
from streamlit_ui.safe_claw.core.skills.registry import SkillRegistry
from streamlit_ui.safe_claw.core.safety.checker import SafetyChecker
from streamlit_ui.safe_claw.core.safety.audit import AuditLogger

# Page imports - import directly to avoid emoji filename issues
import importlib

# Import pages dynamically
def import_page(page_name):
    """Import a page module dynamically"""
    try:
        return importlib.import_module(f'streamlit_ui.pages.{page_name}')
    except ImportError:
        return None

# Get page modules
chat_module = import_page('00_💬_Chat')
memory_module = import_page('01_📚_Memory')
settings_module = import_page('02_⚙️_Settings')
stats_module = import_page('03_📊_Stats')

# Configure Streamlit page
st.set_page_config(
    page_title="SafeClaw - AI Safety Assistant",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
def load_custom_css():
    """Load custom CSS styles"""
    css_path = Path(__file__).parent / "styles" / "custom.css"
    if css_path.exists():
        with open(css_path, 'r') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    logger.info("🔄 Starting session state initialization...")
    
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        logger.info(f"✅ Created session_id: {st.session_state.session_id[:8]}...")
    else:
        logger.info(f"ℹ️ session_id already exists: {st.session_state.session_id[:8]}...")
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
        logger.info("✅ Created messages list")
    else:
        logger.info(f"ℹ️ messages already exists: {len(st.session_state.messages)} messages")
    
    if 'safe_claw_config' not in st.session_state:
        logger.info("🔧 Initializing safe_claw_config...")
        # Try multiple LLM configurations in order of preference
        configs_to_try = [
            # 1. LM Studio Local Server
            SafeClawConfig(
                llm=LLMConfig(
                    provider="openai",
                    model="qwen3-32b",
                    api_key="lm-studio",
                    base_url="http://192.168.50.30:1234/v1",
                    temperature=0.7,
                    max_tokens=2000,
                    context_length=32768  # Match Qwen3-32B context length
                )
            ),
        ]
        
        # Try each configuration until one works
        for i, config in enumerate(configs_to_try):
            try:
                logger.info(f"🔍 Trying LLM config {i+1}: {config.llm.provider} - {config.llm.model}")
                # Test if we can create LLM service
                test_service = LLMService(config.llm)
                st.session_state.safe_claw_config = config
                st.session_state.llm_service = test_service
                logger.info(f"✅ Successfully initialized with LLM config {i+1}")
                break
            except Exception as e:
                logger.warning(f"❌ LLM config {i+1} failed: {e}")
                if i == len(configs_to_try) - 1:  # Last attempt
                    st.session_state.safe_claw_config = config
                    st.session_state.llm_service = None
                    st.error("⚠️ Could not initialize any LLM service. Please check your LLM configuration.")
    else:
        logger.info("ℹ️ safe_claw_config already exists")
    
    if 'workspace_path' not in st.session_state:
        st.session_state.workspace_path = Path.cwd() / "workspace"
        st.session_state.workspace_path.mkdir(exist_ok=True)
        logger.info(f"✅ Created workspace_path: {st.session_state.workspace_path}")
    else:
        logger.info(f"ℹ️ workspace_path already exists: {st.session_state.workspace_path}")
    
    # Initialize memory manager (doesn't depend on LLM)
    if 'memory_manager' not in st.session_state:
        logger.info("🧠 Initializing memory manager...")
        try:
            st.session_state.memory_manager = MemoryManager(
                st.session_state.safe_claw_config.memory,
                str(st.session_state.workspace_path)
            )
            logger.info("✅ Memory manager initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize memory manager: {e}")
            st.session_state.memory_manager = None
    else:
        logger.info("ℹ️ memory_manager already exists")
    
    # Initialize other services only if LLM service is available
    if st.session_state.get('llm_service'):
        logger.info("🤖 LLM service available, initializing graph services...")
        if 'graph_builder' not in st.session_state:
            try:
                st.session_state.graph_builder = SafeClawGraphBuilder(
                    st.session_state.llm_service,
                    st.session_state.memory_manager,
                    {"debug": st.session_state.safe_claw_config.debug}
                )
                logger.info("✅ Graph builder initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize graph builder: {e}")
                st.session_state.graph_builder = None
        
        if 'current_graph' not in st.session_state:
            try:
                if st.session_state.graph_builder:
                    st.session_state.current_graph = st.session_state.graph_builder.create_graph("deep_agent")
                    logger.info("✅ Current graph created successfully")
                else:
                    st.session_state.current_graph = None
                    logger.warning("⚠️ Graph builder not available, skipping graph creation")
            except Exception as e:
                logger.error(f"❌ Failed to create workflow graph: {e}")
                st.session_state.current_graph = None
    else:
        logger.info("⚠️ LLM service not available, skipping graph services")
        # Set graph services to None if LLM is not available
        st.session_state.graph_builder = None
        st.session_state.current_graph = None
    
    # Skill Registry - with pre-loading of external skills
    if 'skill_registry' not in st.session_state:
        try:
            from streamlit_ui.safe_claw.core.skills.registry import SkillRegistry, load_builtin_skills
            from streamlit_ui.safe_claw.core.skills.scanner import get_skill_scanner
            
            # Start with built-in skills
            registry = load_builtin_skills()
            
            # Pre-load external skills from streamlit_ui.safe_claw.configured paths
            skills_paths = [
                Path(__file__).parent / "skills",
            ]
            
            scanner = get_skill_scanner()
            preloaded_skills = scanner.scan_paths(skills_paths, recursive=True)
            
            logger.info(f"✅ Pre-loaded {len(preloaded_skills)} external skills from {len(skills_paths)} paths")
            
            st.session_state.skill_registry = registry
            st.session_state.skill_scanner = scanner
            logger.info("✅ Skill registry initialized with pre-loaded skills")
        except Exception as e:
            logger.error(f"❌ Failed to initialize skill registry: {e}")
            st.session_state.skill_registry = None
            st.session_state.skill_scanner = None
    
    # Safety Checker
    if 'safety_checker' not in st.session_state:
        try:
            st.session_state.safety_checker = SafetyChecker(
                st.session_state.safe_claw_config.safety
            )
            logger.info("✅ Safety checker initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize safety checker: {e}")
            st.session_state.safety_checker = None
    
    # Audit Logger
    if 'audit_logger' not in st.session_state:
        try:
            audit_log_path = st.session_state.workspace_path / "audit.log"
            st.session_state.audit_logger = AuditLogger(log_file=audit_log_path)
            logger.info("✅ Audit logger initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize audit logger: {e}")
            st.session_state.audit_logger = None
    
    # Final status log
    logger.info("📊 Session state initialization completed")
    logger.info(f"🔍 Final session state keys: {list(st.session_state.keys())}")
    
    # Log critical services status
    critical_services = {
        'safe_claw_config': st.session_state.get('safe_claw_config'),
        'llm_service': st.session_state.get('llm_service'),
        'memory_manager': st.session_state.get('memory_manager'),
        'graph_builder': st.session_state.get('graph_builder'),
        'current_graph': st.session_state.get('current_graph'),
        'skill_registry': st.session_state.get('skill_registry'),
        'safety_checker': st.session_state.get('safety_checker'),
        'audit_logger': st.session_state.get('audit_logger')
    }
    
    for service_name, service_value in critical_services.items():
        status = "✅ Available" if service_value else "❌ Missing"
        logger.info(f"   {service_name}: {status}")

def sidebar():
    """Render minimal sidebar - Chat only"""
    with st.sidebar:
        st.title("🛡️ SafeClaw")
        
        # Only Chat option
        st.subheader("Chat")
        
        # Clear chat button
        if st.button("New Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

def main():
    """Main application entry point"""
    # Load custom CSS
    load_custom_css()
    
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    sidebar()
    
    # Main content area - always route to Chat
    logger.info("� Loading Chat page...")
    try:
        from streamlit_ui.pages import chat_page
        if chat_page:
            chat_page.render()
        else:
            logger.error("❌ chat_page module is None")
            st.error("❌ Chat page not available")
    except Exception as e:
        logger.error(f"❌ Error loading chat page: {e}")
        st.error("❌ Failed to load chat page")

if __name__ == "__main__":
    main()
