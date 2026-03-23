#!/usr/bin/env python3
"""
Test script to verify logging is working in SafeClaw
"""

import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_logging():
    """Test that logging works in SafeClaw components"""
    
    print("🔍 Testing SafeClaw Logging")
    print("=" * 50)
    
    # Add project root to path
    project_root = Path('.').absolute()
    sys.path.insert(0, str(project_root))
    
    try:
        # Test app.py logging
        print("1. Testing app.py logging...")
        from streamlit_ui.app import initialize_session_state, logger as app_logger
        app_logger.info("🧪 Test log from app.py")
        print("✅ app.py logging works")
        
        # Test settings page logging
        print("2. Testing settings page logging...")
        from streamlit_ui.pages.settings_page import logger as settings_logger
        settings_logger.info("🧪 Test log from settings page")
        print("✅ Settings page logging works")
        
        # Test stats page logging
        print("3. Testing stats page logging...")
        from streamlit_ui.pages.stats_page import logger as stats_logger
        stats_logger.info("🧪 Test log from stats page")
        print("✅ Stats page logging works")
        
        print("")
        print("🎉 All logging tests passed!")
        print("🚀 SafeClaw should now provide detailed debug information")
        
        return True
        
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_logging()
    sys.exit(0 if success else 1)
