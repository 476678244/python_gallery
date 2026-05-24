#!/usr/bin/env python3
"""
Start SafeClaw FastAPI Backend
Usage: python start_api.py
"""

import sys
import os
from pathlib import Path

# Ensure safe_claw is in path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run
from api.main import app
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting SafeClaw FastAPI Server...")
    print("📍 API URL: http://localhost:8000")
    print("📍 Health Check: http://localhost:8000/health")
    print("📍 Docs: http://localhost:8000/docs")
    print()
    print("Press Ctrl+C to stop")
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )
