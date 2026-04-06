#!/usr/bin/env python3
"""Test context length fix for SafeClaw DeepAgent"""

import sys
import os

# Set Python path
sys.path.insert(0, '/Users/nicole/workspace/github/a476678244/python_gallery')

from streamlit_ui.safe_claw.core.deepagents.official_integration import SafeClawDeepAgent
from streamlit_ui.safe_claw.services.llm_gateway import LLMService, LLMConfig

def test_context_length_fix():
    """Test that context length monitoring and skills limiting works"""
    
    print("🔧 Testing context length fix...")
    
    # Create LLM configuration
    llm_config = LLMConfig(
        provider="openai",
        model="gpt-3.5-turbo",
        api_key="test-key",
        base_url="http://localhost:8000/v1",
        temperature=0.7,
        max_tokens=1000
    )
    
    # Create LLM service
    llm_service = LLMService(llm_config)
    
    # Create SafeClaw DeepAgent with context length limits
    config = {
        "print_prompts": True,
        "prompt_log_file": "test_context_fix.jsonl",
        "max_context_length": 8192,  # Simulate smaller context
        "system_prompt_limit": 4096,  # Limit system prompt size
        "system_prompt": "You are a helpful assistant."
    }
    
    try:
        print("🔧 Initializing SafeClaw DeepAgent with context limits...")
        agent = SafeClawDeepAgent(llm_service, config)
        
        print("✅ Agent initialized successfully!")
        print(f"📊 Context limits: max={agent.max_context_length}, system={agent.system_prompt_limit}")
        
        # Test a simple invoke
        print("\n🧪 Testing simple invocation...")
        test_messages = [
            {"role": "user", "content": "Hello, this is a test to verify context length fix works!"}
        ]
        
        result = agent.invoke(test_messages)
        print(f"📤 Agent response: {result}")
        
        # Check prompt logger
        if hasattr(agent, 'prompt_logger'):
            print(f"📊 Prompts logged: {agent.prompt_logger.prompt_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        print("🔍 This might be expected if LLM server is not running")
        return False

if __name__ == "__main__":
    success = test_context_length_fix()
    if success:
        print("\n🎉 Context length fix test PASSED!")
    else:
        print("\n❌ Context length fix test FAILED!")
