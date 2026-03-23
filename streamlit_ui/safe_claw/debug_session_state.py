#!/usr/bin/env python3
"""
Debug script to check SafeClaw session state initialization
"""

import sys
from pathlib import Path

def debug_session_state():
    """Debug session state initialization"""
    
    print("🔍 Debugging SafeClaw Session State")
    print("=" * 50)
    
    # Add project root to path
    project_root = Path('.').absolute()
    sys.path.insert(0, str(project_root))
    
    # Mock streamlit session state
    class MockSessionState:
        def __init__(self):
            self.state = {}
        
        def get(self, key, default=None):
            return self.state.get(key, default)
        
        def __setitem__(self, key, value):
            self.state[key] = value
        
        def __getitem__(self, key):
            return self.state[key]
        
        def __contains__(self, key):
            return key in self.state
        
        def keys(self):
            return self.state.keys()
        
        def __len__(self):
            return len(self.state)
    
    try:
        import streamlit as st
        st.session_state = MockSessionState()
        
        # Test initialization
        from streamlit_ui.app import initialize_session_state
        
        # Force initialization by clearing session state first
        st.session_state.state.clear()
        print("🔄 Cleared session state, forcing initialization...")
        
        initialize_session_state()
        
        print("📊 Session State Contents:")
        for key in st.session_state.keys():
            value = st.session_state.get(key)
            status = "✅" if value else "❌"
            print(f"   {status} {key}: {type(value).__name__}")
        
        # Debug: Print actual values for critical services
        print("")
        print("🔍 Critical Service Values:")
        critical_keys = ['safe_claw_config', 'llm_service', 'memory_manager']
        for key in critical_keys:
            value = st.session_state.get(key)
            if value:
                print(f"   ✅ {key}: {value}")
            else:
                print(f"   ❌ {key}: None")
        
        print("")
        print("🔍 Service Status Check:")
        
        # Check specific services
        checks = [
            ('safe_claw_config', 'Configuration'),
            ('llm_service', 'LLM Service'),
            ('memory_manager', 'Memory Manager'),
            ('graph_builder', 'Graph Builder'),
            ('current_graph', 'Current Graph'),
            ('workspace_path', 'Workspace Path'),
            ('session_id', 'Session ID'),
            ('messages', 'Messages')
        ]
        
        all_good = True
        for key, name in checks:
            value = st.session_state.get(key)
            if value:
                print(f"   ✅ {name}: Available")
            else:
                print(f"   ❌ {name}: Missing")
                if key in ['safe_claw_config', 'memory_manager']:
                    all_good = False
        
        print("")
        if all_good:
            print("🎉 All critical services are available!")
            print("🚀 SafeClaw should work properly")
        else:
            print("❌ Some critical services are missing")
            print("🔧 This explains the 'Required services not available' error")
        
        # Test page checks
        print("")
        print("📱 Page Service Checks:")
        
        # Test Settings page check
        config = st.session_state.get('safe_claw_config')
        settings_ok = config is not None
        print(f"   {'✅' if settings_ok else '❌'} Settings Page: {'Ready' if settings_ok else 'Not Ready'}")
        
        # Test Stats page check
        memory_manager = st.session_state.get('memory_manager')
        stats_ok = memory_manager is not None
        print(f"   {'✅' if stats_ok else '❌'} Stats Page: {'Ready' if stats_ok else 'Not Ready'}")
        
        # Test Chat page check
        llm_service = st.session_state.get('llm_service')
        memory_manager = st.session_state.get('memory_manager')
        chat_ok = memory_manager is not None  # Only memory is essential
        print(f"   {'✅' if chat_ok else '❌'} Chat Page: {'Ready' if chat_ok else 'Not Ready'}")
        
        return all_good
        
    except Exception as e:
        print(f"❌ Error during debug: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_session_state()
    sys.exit(0 if success else 1)
