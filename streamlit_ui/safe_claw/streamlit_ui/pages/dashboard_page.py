"""Dashboard page for SafeClaw"""

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
    required_services = [
        'memory_manager',
        'session_service',
        'skill_registry',
        'safety_checker'
    ]
    
    return all(service in st.session_state for service in required_services)

# Page initialization
if __name__ == "__main__":
    render()
