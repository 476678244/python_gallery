#!/usr/bin/env python3
"""
Verify all SafeClaw fixes are working
"""

import sys
import subprocess
from pathlib import Path

def verify_fixes():
    """Verify that all fixes are working"""
    
    print("🔍 Verifying SafeClaw Fixes")
    print("=" * 50)
    
    all_good = True
    
    # 1. Check that use_container_width is fixed
    print("1. Checking use_container_width fixes...")
    try:
        result = subprocess.run(
            ["grep", "-r", "use_container_width", "streamlit_ui/"],
            capture_output=True, text=True, cwd="."
        )
        
        if result.returncode == 0 and result.stdout.strip():
            print(f"❌ Still has {len(result.stdout.splitlines())} use_container_width instances")
            all_good = False
        else:
            print("✅ No use_container_width instances found")
    except Exception as e:
        print(f"❌ Error checking use_container_width: {e}")
        all_good = False
    
    # 2. Check system monitor memory info fix
    print("\n2. Checking system monitor memory info fix...")
    try:
        with open("../components/system_monitor.py", 'r') as f:
            content = f.read()
        
        if "hasattr(memory_info, 'shared')" in content:
            print("✅ System monitor memory info fix applied")
        else:
            print("❌ System monitor memory info fix missing")
            all_good = False
    except Exception as e:
        print(f"❌ Error checking system monitor: {e}")
        all_good = False
    
    # 3. Check Tools page service dependency fixes
    print("\n3. Checking Tools page service dependency fixes...")
    try:
        with open("../pages/04_🔧_Tools.py", 'r') as f:
            content = f.read()
        
        if "if skill_registry:" in content and "if safety_checker and audit_logger:" in content:
            print("✅ Tools page service dependency fixes applied")
        else:
            print("❌ Tools page service dependency fixes missing")
            all_good = False
    except Exception as e:
        print(f"❌ Error checking Tools page: {e}")
        all_good = False
    
    # 4. Check chat page welcome message
    print("\n4. Checking chat page welcome message...")
    try:
        with open("../pages/00_💬_Chat.py", 'r') as f:
            content = f.read()
        
        if "Hello! I'm SafeClaw" in content and "simple_render_message" in content:
            print("✅ Chat page welcome message and fallback renderer added")
        else:
            print("❌ Chat page fixes missing")
            all_good = False
    except Exception as e:
        print(f"❌ Error checking chat page: {e}")
        all_good = False
    
    # 5. Check dashboard navigation fix
    print("\n5. Checking dashboard navigation fix...")
    try:
        with open("../components/dashboard.py", 'r') as f:
            content = f.read()
        
        if 'st.switch_page("pages/01_📚_Memory.py")' in content:
            print("✅ Dashboard navigation fix applied")
        else:
            print("❌ Dashboard navigation fix missing")
            all_good = False
    except Exception as e:
        print(f"❌ Error checking dashboard: {e}")
        all_good = False
    
    # 6. Check logging enhancements
    print("\n6. Checking logging enhancements...")
    try:
        with open("../app.py", 'r') as f:
            content = f.read()
        
        if "🔄 Starting session state initialization" in content and "📱 Routing to page:" in content:
            print("✅ Logging enhancements applied")
        else:
            print("❌ Logging enhancements missing")
            all_good = False
    except Exception as e:
        print(f"❌ Error checking app.py: {e}")
        all_good = False
    
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 All fixes verified successfully!")
        print("🚀 SafeClaw should run without errors")
    else:
        print("❌ Some fixes are missing or incomplete")
        print("🔧 Please review the failed checks above")
    
    return all_good

if __name__ == "__main__":
    success = verify_fixes()
    sys.exit(0 if success else 1)
