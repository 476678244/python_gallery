"""Chat page module for SafeClaw"""

import sys
import os
from pathlib import Path

# Add the pages directory to Python path
pages_dir = Path(__file__).parent
sys.path.insert(0, str(pages_dir))

# Import the actual chat page implementation directly
import importlib.util
spec = importlib.util.spec_from_file_location(
    "chat_module", 
    pages_dir / "00_Chat.py"
)
chat_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chat_module)

# Expose the render function
def render():
    """Render the chat page"""
    return chat_module.render()
