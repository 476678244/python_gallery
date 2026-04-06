#!/usr/bin/env python3
"""Test LangChain message format compatibility with PromptLoggerMiddleware"""

import sys
import os

# Set Python path
sys.path.insert(0, '/Users/nicole/workspace/github/a476678244/python_gallery')

from streamlit_ui.safe_claw.core.deepagents.official_integration import PromptLoggerMiddleware
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

def test_langchain_message_logging():
    """Test the PromptLoggerMiddleware with LangChain message objects"""
    
    print("🔧 Testing PromptLoggerMiddleware with LangChain messages...")
    
    # Create prompt logger with console output
    logger = PromptLoggerMiddleware(
        log_file="test_langchain_prompts.jsonl", 
        print_to_console=True
    )
    
    # Create a mock state with LangChain message objects
    test_state = {
        "messages": [
            SystemMessage(content="You are a helpful AI assistant."),
            HumanMessage(content="Hello! This is a test message to verify LangChain message logging works correctly."),
            AIMessage(content="I understand! I'll help you test the LangChain message logging functionality."),
            HumanMessage(content="Can you show me how the prompt logging works with different message types?"),
        ]
    }
    
    # Create a mock runtime (minimal implementation)
    class MockRuntime:
        pass
    
    runtime = MockRuntime()
    
    print("\n🧪 Simulating model call with LangChain messages...")
    
    # Call the before_model method to trigger prompt logging
    result_state = logger.before_model(test_state, runtime)
    
    print(f"\n✅ Test completed!")
    print(f"📊 Total prompts logged: {logger.prompt_count}")
    
    # Check if log file was created
    if os.path.exists("test_langchain_prompts.jsonl"):
        print(f"📄 Log file created: test_langchain_prompts.jsonl")
        with open("test_langchain_prompts.jsonl", "r") as f:
            log_content = f.read()
            print(f"📄 Log file size: {len(log_content)} characters")
            
            # Show a snippet of the logged data
            lines = log_content.strip().split('\n')
            if lines:
                print(f"📄 Logged entries: {len(lines)}")
                print(f"📄 First entry preview:")
                print(lines[0][:200] + "..." if len(lines[0]) > 200 else lines[0])
    else:
        print("⚠️ Log file was not created")
    
    return logger.prompt_count > 0

if __name__ == "__main__":
    success = test_langchain_message_logging()
    if success:
        print("\n🎉 LangChain message logging test PASSED!")
    else:
        print("\n❌ LangChain message logging test FAILED!")
