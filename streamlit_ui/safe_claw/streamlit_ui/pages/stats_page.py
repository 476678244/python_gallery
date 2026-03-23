"""Stats page module for SafeClaw"""

import sys
from pathlib import Path

# Add the pages directory to Python path
pages_dir = Path(__file__).parent
sys.path.insert(0, str(pages_dir))

# Import the actual stats page implementation directly
import importlib.util
spec = importlib.util.spec_from_file_location(
    "stats_module", 
    pages_dir / "03_📊_Stats.py"
)
stats_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stats_module)

# Expose the render function
def render():
    """Render the stats page"""
    return stats_module.render()
