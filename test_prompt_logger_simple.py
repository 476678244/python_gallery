#!/usr/bin/env python3
"""Simple test for PromptLoggerMiddleware functionality"""

import sys
import os

# Set Python path
sys.path.insert(0, '/Users/nicole/workspace/github/a476678244/python_gallery')

from streamlit_ui.safe_claw.core.deepagents.official_integration import PromptLoggerMiddleware

def test_prompt_logger_middleware():
    """Test the PromptLoggerMiddleware directly"""
    
    print("🔧 Testing PromptLoggerMiddleware...")
    
    # Create prompt logger with console output
    logger = PromptLoggerMiddleware(
        log_file="test_prompts.jsonl", 
        print_to_console=True
    )
    
    # Create a mock state with messages
    test_state = {
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": "Hello! This is a test message to verify prompt logging is working correctly."},
            {"role": "assistant", "content": "I understand! I'll help you test the prompt logging functionality."},
            {"role": "tool", "name": "test_tool", "content": "Tool result: Success!"}
        ]
    }
    
    # Create a mock runtime (minimal implementation)
    class MockRuntime:
        pass
    
    runtime = MockRuntime()
    
    print("\n🧪 Simulating model call with prompt logging...")
    
    # Call the before_model method to trigger prompt logging
    result_state = logger.before_model(test_state, runtime)
    
    print(f"\n✅ Test completed!")
    print(f"📊 Total prompts logged: {logger.prompt_count}")
    
    # Check if log file was created
    if os.path.exists("test_prompts.jsonl"):
        print(f"📄 Log file created: test_prompts.jsonl")
        with open("test_prompts.jsonl", "r") as f:
            log_content = f.read()
            print(f"📄 Log file size: {len(log_content)} characters")
    else:
        print("⚠️ Log file was not created")
    
    return logger.prompt_count > 0

if __name__ == "__main__":
    success = test_prompt_logger_middleware()
    if success:
        print("\n🎉 PromptLoggerMiddleware test PASSED!")
    else:
        print("\n❌ PromptLoggerMiddleware test FAILED!")
