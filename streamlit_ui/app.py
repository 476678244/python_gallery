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
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enable debug logging for external deepagents library and all its modules
logging.getLogger('deepagents').setLevel(logging.DEBUG)
logging.getLogger('deepagents.*').setLevel(logging.DEBUG)

# Also enable debug for all related libraries to see deepagents internal logs
logging.getLogger('langchain').setLevel(logging.DEBUG)
logging.getLogger('langgraph').setLevel(logging.DEBUG)
logging.getLogger('langchain_core').setLevel(logging.DEBUG)

# Set root logger to DEBUG to capture everything
logging.getLogger().setLevel(logging.DEBUG)

# Enable DeepAgents debug logging if environment variable is set
if os.getenv('DEEPAGENTS_DEBUG', 'false').lower() == 'true':
    try:
        from streamlit_ui.safe_claw.deepagents_external_debug import setup_external_deepagents_debug, quick_debug_enable
        setup_external_deepagents_debug()
        quick_debug_enable()
        logger.info("External DeepAgents debug logging enabled")
    except ImportError as e:
        logger.warning(f"Could not enable external DeepAgents debug logging: {e}")

# Import SafeClaw components
from streamlit_ui.safe_claw.models.config import SafeClawConfig, LLMConfig
from streamlit_ui.safe_claw.services.llm_gateway import LLMService
from streamlit_ui.safe_claw.core.memory.manager import MemoryManager
from streamlit_ui.safe_claw.core.graph.builder import SafeClawGraphBuilder
from streamlit_ui.safe_claw.core.skills.registry import SkillRegistry
from streamlit_ui.safe_claw.core.safety.checker import SafetyChecker
from streamlit_ui.safe_claw.core.safety.audit import AuditLogger

# User preferences file path
def get_user_prefs_path() -> Path:
    """Get path to user preferences JSON file"""
    prefs_dir = Path.home() / ".safe_claw"
    prefs_dir.mkdir(exist_ok=True)
    return prefs_dir / "user_preferences.json"

def load_user_preferences() -> Dict[str, Any]:
    """Load user preferences from JSON file"""
    prefs_path = get_user_prefs_path()
    if prefs_path.exists():
        try:
            with open(prefs_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load user preferences: {e}")
    return {}

def save_user_preferences(prefs: Dict[str, Any]) -> bool:
    """Save user preferences to JSON file"""
    try:
        prefs_path = get_user_prefs_path()
        with open(prefs_path, 'w') as f:
            json.dump(prefs, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save user preferences: {e}")
        return False

def save_skill_tree_preferences(enabled_skills: set, disabled_folders: set) -> bool:
    """Save skill tree state to user preferences"""
    try:
        prefs = load_user_preferences()
        prefs['skill_tree'] = {
            'enabled_skills': list(enabled_skills),
            'disabled_folders': list(disabled_folders),
            'last_updated': datetime.now().isoformat()
        }
        return save_user_preferences(prefs)
    except Exception as e:
        logger.error(f"Failed to save skill tree preferences: {e}")
        return False

def load_skill_tree_preferences() -> tuple[set, set]:
    """Load skill tree state from user preferences"""
    try:
        prefs = load_user_preferences()
        skill_tree_prefs = prefs.get('skill_tree', {})
        enabled_skills = set(skill_tree_prefs.get('enabled_skills', []))
        disabled_folders = set(skill_tree_prefs.get('disabled_folders', []))
        return enabled_skills, disabled_folders
    except Exception as e:
        logger.warning(f"Failed to load skill tree preferences: {e}")
        return set(), set()

# Page imports - import directly to avoid emoji filename issues
import importlib

# Define available models
AVAILABLE_MODELS = {
    "Qwen3.5-9B-VLM": {
        "provider": "openai",
        "model": "Qwen3.5-9B-VLM",
        "api_key": "lm-studio",
        "base_url": "http://192.168.50.30:1234/v1",
        "temperature": 0.7,
        "max_tokens": 2000,
        "context_length": 262144,
        "show_thinking": False
    },
    "qwen/qwen3.5-35b-a3b": {
        "provider": "openai",
        "model": "qwen/qwen3.5-35b-a3b",
        "api_key": "lm-studio",
        "base_url": "http://192.168.50.30:1234/v1",
        "temperature": 0.7,
        "max_tokens": 2000,
        "context_length": 30000,
        "show_thinking": False
    },
    "qwen/qwen3.6-27b": {
        "provider": "openai",
        "model": "qwen/qwen3.6-27b",
        "api_key": "lm-studio",
        "base_url": "http://192.168.50.30:1234/v1",
        "temperature": 0.7,
        "max_tokens": 2000,
        "context_length": 128000,
        "show_thinking": False
    },
    "gpt_oss": {
        "provider": "openai",
        "model": "gpt-oss-20b",
        "api_key": "lm-studio",
        "base_url": "http://192.168.50.30:1234/v1",
        "temperature": 0.7,
        "max_tokens": 2000,
        "context_length": 30000,
        "show_thinking": False
    },
    "google/gemma-4-31b": {
        "provider": "openai",
        "model": "google/gemma-4-31b",
        "api_key": "lm-studio",
        "base_url": "http://192.168.50.30:1234/v1",
        "temperature": 0.7,
        "max_tokens": 2000,
        "context_length": 128000,
        "show_thinking": False
    },
    "google/gemma-4-e4b": {
        "provider": "openai",
        "model": "google/gemma-4-e4b",
        "api_key": "lm-studio",
        "base_url": "http://192.168.50.30:1234/v1",
        "temperature": 0.7,
        "max_tokens": 2000,
        "context_length": 128000,
        "show_thinking": False
    },
}

# Import pages dynamically
def import_page(page_name):
    """Import a page module dynamically"""
    try:
        return importlib.import_module(f'streamlit_ui.pages.{page_name}')
    except ImportError:
        return None

# Get page modules
chat_module = import_page('00_Chat')
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

    # Initialize workspace_path first (needed for session restore)
    if 'workspace_path' not in st.session_state:
        st.session_state.workspace_path = Path.cwd() / "workspace"
        st.session_state.workspace_path.mkdir(exist_ok=True)
        logger.info(f"✅ Created workspace_path: {st.session_state.workspace_path}")
    else:
        logger.info(f"ℹ️ workspace_path already exists: {st.session_state.workspace_path}")

    # Try to auto-restore last session on first load
    if 'session_id' not in st.session_state:
        from streamlit_ui.components.session_manager import list_saved_sessions, load_session_from_file
        saved_sessions = list_saved_sessions()
        if saved_sessions:
            # Load the most recent session
            last_session = saved_sessions[0]
            logger.info(f"📂 Auto-loading last session: {last_session['session_id'][:8]}...")
            try:
                if load_session_from_file(last_session['session_id']):
                    logger.info(f"✅ Restored session with {len(st.session_state.get('messages', []))} messages")
                else:
                    st.session_state.session_id = str(uuid.uuid4())
                    st.session_state.messages = []
                    st.session_state.session_start = datetime.now()
                    st.session_state.last_activity = datetime.now()
            except Exception as e:
                logger.error(f"❌ Failed to restore session: {e}")
                st.session_state.session_id = str(uuid.uuid4())
                st.session_state.messages = []
                st.session_state.session_start = datetime.now()
                st.session_state.last_activity = datetime.now()
        else:
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.session_state.session_start = datetime.now()
            st.session_state.last_activity = datetime.now()
            logger.info(f"✅ Created new session_id: {st.session_state.session_id[:8]}...")
    else:
        logger.info(f"ℹ️ session_id already exists: {st.session_state.session_id[:8]}...")

    if 'messages' not in st.session_state:
        st.session_state.messages = []
        logger.info("✅ Created messages list")
    else:
        logger.info(f"ℹ️ messages already exists: {len(st.session_state.messages)} messages")
    
    # Initialize selected model if not set
    if 'selected_model' not in st.session_state:
        # Try to load from user preferences JSON file
        prefs = load_user_preferences()
        saved_model = prefs.get('selected_model')
        if saved_model and saved_model in AVAILABLE_MODELS:
            st.session_state.selected_model = saved_model
            logger.info(f"✅ Loaded model from preferences: {st.session_state.selected_model}")
        else:
            st.session_state.selected_model = "qwen/qwen3.5-35b-a3b"
            logger.info(f"✅ Set default model: {st.session_state.selected_model}")
    else:
        # Validate restored model is in available models
        if st.session_state.selected_model not in AVAILABLE_MODELS:
            logger.warning(f"⚠️ Restored model '{st.session_state.selected_model}' not in AVAILABLE_MODELS, resetting to default")
            st.session_state.selected_model = "qwen/qwen3.5-35b-a3b"
        else:
            logger.info(f"✅ Using restored model: {st.session_state.selected_model}")
    
    # Initialize skill tree state from user preferences
    if 'skill_tree_state' not in st.session_state:
        enabled_skills, disabled_folders = load_skill_tree_preferences()
        st.session_state.skill_tree_state = {
            "enabled_skills": enabled_skills,
            "disabled_folders": disabled_folders,
            "tree": None,
            "use_complete_tree": True
        }
        logger.info(f"✅ Loaded skill tree preferences: {len(enabled_skills)} enabled, {len(disabled_folders)} disabled folders")
    
    if 'safe_claw_config' not in st.session_state:
        logger.info("🔧 Initializing safe_claw_config...")
        # Use the selected model from AVAILABLE_MODELS
        model_key = st.session_state.selected_model
        model_config = AVAILABLE_MODELS[model_key]
        
        try:
            logger.info(f"🔍 Trying LLM config: {model_config['provider']} - {model_config['model']}")
            config = SafeClawConfig(llm=LLMConfig(**model_config))
            test_service = LLMService(config.llm)
            st.session_state.safe_claw_config = config
            st.session_state.llm_service = test_service
            logger.info(f"✅ Successfully initialized with model: {model_key}")
        except Exception as e:
            logger.error(f"❌ LLM config failed: {e}")
            raise RuntimeError(f"LLM service is required but failed to initialize: {e}. Please check your API keys and configuration.") from e
    else:
        logger.info("ℹ️ safe_claw_config already exists")
        # Check if llm_service needs to be restored (session restore case)
        if 'llm_service' not in st.session_state or st.session_state.llm_service is None:
            logger.info("🔧 Initializing llm_service from existing config...")
            try:
                st.session_state.llm_service = LLMService(st.session_state.safe_claw_config.llm)
                logger.info("✅ llm_service initialized from existing config")
            except Exception as e:
                logger.error(f"❌ Failed to initialize llm_service from existing config: {e}")
                raise RuntimeError(f"LLM service is required but failed to initialize from saved config: {e}") from e

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

    # Initialize graph services (LLM service is guaranteed to exist)
    logger.info("🤖 Initializing graph services...")
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
            raise RuntimeError(f"Graph builder is required but failed to initialize: {e}") from e

    # if 'current_graph' not in st.session_state:
    #     try:
    #         if st.session_state.graph_builder:
    #             st.session_state.current_graph = st.session_state.graph_builder.create_graph("deep_agent")
    #             logger.info("✅ Current graph created successfully")
    #         else:
    #             raise RuntimeError("Graph builder is required but not available")
    #     except Exception as e:
    #         logger.error(f"❌ Failed to create workflow graph: {e}")
    #         raise RuntimeError(f"Workflow graph is required but failed to create: {e}") from e
    
    # Skill Registry - with pre-loading of external skills
    if 'skill_registry' not in st.session_state:
        try:
            from streamlit_ui.safe_claw.core.skills.registry import SkillRegistry, load_builtin_skills
            from streamlit_ui.safe_claw.core.skills.scanner import get_skill_scanner
            
            # Start with built-in skills
            registry = load_builtin_skills()
            
            # Pre-load external skills from all sources (including linked_skills)
            scanner = get_skill_scanner()
            preloaded_skills = scanner.scan_all_skills()
            
            logger.info(f"✅ Pre-loaded {len(preloaded_skills)} external skills from all sources")
            
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
        
        # Model selection
        st.subheader("Model Selection")
        if 'selected_model' not in st.session_state:
            st.session_state.selected_model = "qwen/qwen3.5-35b-a3b"
        
        selected_model = st.selectbox(
            "Select Model",
            options=list(AVAILABLE_MODELS.keys()),
            index=list(AVAILABLE_MODELS.keys()).index(st.session_state.selected_model),
            key="model_selector"
        )
        
        # Update selected model if changed
        if selected_model != st.session_state.selected_model:
            st.session_state.selected_model = selected_model
            # Reinitialize LLM service with new model
            if 'safe_claw_config' in st.session_state:
                model_config = AVAILABLE_MODELS[selected_model]
                st.session_state.safe_claw_config.llm = LLMConfig(**model_config)
                try:
                    st.session_state.llm_service = LLMService(st.session_state.safe_claw_config.llm)
                    st.success(f"✅ Switched to {selected_model}")
                except Exception as e:
                    st.error(f"❌ Failed to switch to {selected_model}: {e}")
            # Save session immediately to persist model selection
            try:
                from streamlit_ui.components.session_manager import save_session_to_file
                save_session_to_file()
            except Exception as e:
                logger.warning(f"Failed to save session after model change: {e}")
            # Save to user preferences JSON file for cross-session persistence
            try:
                prefs = load_user_preferences()
                prefs['selected_model'] = selected_model
                prefs['last_updated'] = datetime.now().isoformat()
                save_user_preferences(prefs)
                logger.info(f"✅ Saved model preference: {selected_model}")
            except Exception as e:
                logger.warning(f"Failed to save user preferences: {e}")
            st.rerun()
        
        # Display current model info
        current_model = AVAILABLE_MODELS[st.session_state.selected_model]
        st.caption(f"Current: {current_model['model']}")
        
        st.divider()
        
        # Chat options
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
