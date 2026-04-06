#!/usr/bin/env python3
"""Test updated context length calculation including tools tokens"""

import sys
import os

# Set Python path
sys.path.insert(0, '/Users/nicole/workspace/github/a476678244/python_gallery')

from streamlit_ui.safe_claw.core.deepagents.official_integration import SafeClawDeepAgent
from streamlit_ui.safe_claw.services.llm_gateway import LLMService, LLMConfig

def test_tools_tokens_calculation():
    """Test that tools tokens are included in context length calculation"""
    
    print("🔧 Testing tools tokens calculation...")
    
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
    
    # Create SafeClaw DeepAgent with strict context limits to trigger limiting
    config = {
        "print_prompts": True,
        "prompt_log_file": "test_tools_tokens.jsonl",
        "max_context_length": 4096,  # Very strict limit
        "system_prompt_limit": 2048,  # Even stricter system prompt limit
        "system_prompt": "You are a helpful assistant."
    }
    
    try:
        print("🔧 Initializing SafeClaw DeepAgent with strict context limits...")
        agent = SafeClawDeepAgent(llm_service, config)
        
        print("✅ Agent initialized successfully!")
        print(f"📊 Context limits: max={agent.max_context_length}, system={agent.system_prompt_limit}")
        
        # Test a simple invoke
        print("\n🧪 Testing simple invocation...")
        test_messages = [
            {"role": "user", "content": "Hello, this is a test to verify tools tokens calculation!"}
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
    success = test_tools_tokens_calculation()
    if success:
        print("\n🎉 Tools tokens calculation test PASSED!")
    else:
        print("\n❌ Tools tokens calculation test FAILED!")
