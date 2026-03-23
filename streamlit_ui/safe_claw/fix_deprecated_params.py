#!/usr/bin/env python3
"""
Fix deprecated use_container_width parameters in SafeClaw
"""

import os
import re
from pathlib import Path

def fix_deprecated_params():
    """Fix use_container_width -> width in all Python files"""
    
    print("🔧 Fixing deprecated use_container_width parameters...")
    
    # Find all Python files in streamlit_ui directory
    streamlit_ui_dir = Path("streamlit_ui")
    
    if not streamlit_ui_dir.exists():
        print("❌ streamlit_ui directory not found")
        return False
    
    files_changed = 0
    
    # Walk through all Python files
    for py_file in streamlit_ui_dir.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Fix use_container_width=True -> width='stretch'
            content = re.sub(r'use_container_width=True', "width='stretch'", content)
            
            # Fix use_container_width=False -> width='content'
            content = re.sub(r'use_container_width=False', "width='content'", content)
            
            # Only write if content changed
            if content != original_content:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                files_changed += 1
                print(f"✅ Fixed: {py_file.relative_to(Path.cwd())}")
        
        except Exception as e:
            print(f"❌ Error processing {py_file}: {e}")
    
    print(f"\n🎉 Fixed {files_changed} files")
    print("🚀 SafeClaw should no longer show use_container_width warnings")
    
    return files_changed > 0

if __name__ == "__main__":
    success = fix_deprecated_params()
    exit(0 if success else 1)
