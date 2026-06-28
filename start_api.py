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

def _build_log_config() -> dict:
    """Uvicorn logging config.

    - default/error logs -> stdout (also tee'd into logs/server.log via api.main)
    - access logs        -> logs/access.log (tail -f to monitor requests)
    """
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    access_log_path = log_dir / "access.log"

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(asctime)s - %(levelprefix)s %(message)s",
                "use_colors": None,
            },
            "access": {
                "()": "uvicorn.logging.AccessFormatter",
                "fmt": '%(asctime)s - %(client_addr)s - "%(request_line)s" %(status_code)s',
                "use_colors": False,
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "access_file": {
                "formatter": "access",
                "class": "logging.FileHandler",
                "filename": str(access_log_path),
                "mode": "a",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
            "uvicorn.error": {"level": "INFO"},
            "uvicorn.access": {"handlers": ["access_file"], "level": "INFO", "propagate": False},
        },
    }


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
        log_level="info",
        log_config=_build_log_config(),
    )
