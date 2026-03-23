"""Dashboard page for SafeClaw - Main overview"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from typing import Dict, Any

def render():
    """Render the dashboard page"""
    
    # Check if required services are available
    if not check_services():
        st.error("❌ Required services not available. Please check your configuration.")
        return
    
    # Render dashboard
    from streamlit_ui.components.dashboard import render_dashboard
    render_dashboard()

def check_services() -> bool:
    """Check if required services are available"""
    # Only check for essential services
    essential_services = ['memory_manager']
    
    # Check essential services
    if not all(service in st.session_state for service in essential_services):
        return False
    
    # Show warnings for optional services but don't fail
    optional_services = ['session_service', 'skill_registry', 'safety_checker']
    missing_optional = [s for s in optional_services if s not in st.session_state]
    
    if missing_optional:
        st.warning(f"⚠️ Some optional services not available: {', '.join(missing_optional)}")
        st.info("Some dashboard features may be limited.")
    
    return True

# Page initialization
if __name__ == "__main__":
    render()
