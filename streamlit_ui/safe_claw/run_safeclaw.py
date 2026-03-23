#!/usr/bin/env python3
"""
SafeClaw Startup Script
Run this script to start SafeClaw with proper configuration
"""

import sys
import os
from pathlib import Path

def main():
    """Main startup function"""
    print("🦞 SafeClaw AI Safety Assistant")
    print("=" * 40)
    print("")
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required. Current version:", sys.version.split()[0])
        sys.exit(1)
    
    # Check if we're in the right directory
    if not Path("streamlit_ui/app.py").exists():
        print("❌ Please run this script from the SafeClaw root directory")
        print("   (where streamlit_ui/app.py is located)")
        sys.exit(1)
    
    # Check conda environment
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    if conda_env != 'safe_claw':
        print("⚠️ Warning: Not in 'safe_claw' conda environment")
        print("   Please run: conda activate safe_claw")
        print("")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    print("✅ Environment checks passed")
    print("🚀 Starting SafeClaw...")
    print("")
    
    # Import and test services
    try:
        from services.llm_gateway import LLMService
        from models.config import LLMConfig
        
        # Test LLM service
        llm_config = LLMConfig(
            provider="openai",
            model="gpt-3.5-turbo", 
            api_key="mock-key"
        )
        llm_service = LLMService(llm_config)
        response = llm_service.invoke([{"role": "user", "content": "test"}])
        
        if "mock response" in response.lower():
            print("✅ LLM Service: Mock mode (demo)")
        else:
            print("✅ LLM Service: Real LLM connected")
            
    except Exception as e:
        print(f"⚠️ LLM Service Warning: {e}")
        print("   SafeClaw will run in limited mode")
    
    print("")
    print("🌐 Launching web interface...")
    print("   SafeClaw will open in your browser")
    print("   Press Ctrl+C to stop")
    print("")
    
    # Start Streamlit
    try:
        import subprocess
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "streamlit_ui/app.py",
            "--server.headless=false",
            "--server.port=8501"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 SafeClaw stopped")
    except Exception as e:
        print(f"❌ Failed to start SafeClaw: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
