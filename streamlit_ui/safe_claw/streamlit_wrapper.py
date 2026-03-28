#!/usr/bin/env python3
"""SafeClaw Streamlit Wrapper - Sets up Python path and runs Streamlit"""

import sys
from pathlib import Path

# Add safe_claw's parent directory to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Test imports first
try:
    from streamlit_ui.safe_claw.models.config import SafeClawConfig, LLMConfig
except Exception as e:
    print(f"❌ Wrapper: Import failed: {e}")
    sys.exit(1)

# Now run Streamlit
import subprocess
subprocess.run([
    sys.executable, "-m", "streamlit", "run", 
    "streamlit_ui/app.py"
] + sys.argv[1:])
