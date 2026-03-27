#!/usr/bin/env python3
"""
Test script to verify dashboard navigation fix
"""

import sys
from pathlib import Path

def test_dashboard_navigation():
    """Test that dashboard navigation uses correct file paths"""
    
    print("🔍 Testing Dashboard Navigation Fix")
    print("=" * 50)
    
    # Check that the fixed file exists
    dashboard_file = Path("../components/dashboard.py")
    if not dashboard_file.exists():
        print("❌ Dashboard component not found")
        return False
    
    # Read the file and check for correct st.switch_page usage
    with open(dashboard_file, 'r') as f:
        content = f.read()
    
    # Check for correct file paths in st.switch_page calls
    expected_paths = [
        'st.switch_page("pages/01_📚_Memory.py")',
        'st.switch_page("pages/04_🔧_Tools.py")'
    ]
    
    all_correct = True
    for expected_path in expected_paths:
        if expected_path in content:
            print(f"✅ Found correct path: {expected_path}")
        else:
            print(f"❌ Missing correct path: {expected_path}")
            all_correct = False
    
    # Check that incorrect paths are not present
    incorrect_paths = [
        'st.switch_page("📚 Memory")',
        'st.switch_page("🔧 Tools")'
    ]
    
    for incorrect_path in incorrect_paths:
        if incorrect_path in content:
            print(f"❌ Still has incorrect path: {incorrect_path}")
            all_correct = False
        else:
            print(f"✅ Correctly removed: {incorrect_path}")
    
    # Check that the target files exist
    print("")
    print("📁 Checking target page files:")
    pages_dir = Path("../pages")
    
    target_files = [
        "01_📚_Memory.py",
        "04_🔧_Tools.py"
    ]
    
    for target_file in target_files:
        file_path = pages_dir / target_file
        if file_path.exists():
            print(f"✅ {target_file}: exists")
        else:
            print(f"❌ {target_file}: missing")
            all_correct = False
    
    if all_correct:
        print("")
        print("🎉 Dashboard navigation fix verified!")
        print("🚀 SafeClaw should now work without navigation errors")
        return True
    else:
        print("")
        print("❌ Some issues remain in dashboard navigation")
        return False

if __name__ == "__main__":
    success = test_dashboard_navigation()
    sys.exit(0 if success else 1)
