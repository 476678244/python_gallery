"""Memory page module for SafeClaw"""

import sys
from pathlib import Path

# Add the pages directory to Python path
pages_dir = Path(__file__).parent
sys.path.insert(0, str(pages_dir))

# Import the actual memory page implementation directly
import importlib.util
spec = importlib.util.spec_from_file_location(
    "memory_module", 
    pages_dir / "01_📚_Memory.py"
)
memory_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(memory_module)

# Expose the render function
def render():
    """Render the memory page"""
    return memory_module.render()
