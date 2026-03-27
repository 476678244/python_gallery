"""Settings page module for SafeClaw"""

import sys
from pathlib import Path

# Add the pages directory to Python path
pages_dir = Path(__file__).parent
sys.path.insert(0, str(pages_dir))

# Import the actual settings page implementation directly
import importlib.util
spec = importlib.util.spec_from_file_location(
    "settings_module", 
    pages_dir / "02_⚙️_Settings.py"
)
settings_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(settings_module)

# Expose the render function
def render():
    """Render the settings page"""
    return settings_module.render()
