#!/usr/bin/env python3
"""Test script for DeepAgents + Skills integration"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from streamlit_ui.safe_claw.core.skills import SkillDiscovery, get_skill_scanner
from streamlit_ui.safe_claw.core.deepagents.official_integration import SafeClawDeepAgent

def test_skills_discovery():
    """Test skills discovery system"""
    print("=== Testing Skills Discovery ===")
    
    scanner = get_skill_scanner()
    discovery = SkillDiscovery(scanner)
    
    # Test 1: List available skills
    print("\n1. Testing skill_list_available...")
    result = discovery.find_skill("list available skills")
    print(f"Result: {result.success}")
    if result.execution_result:
        print(f"Output: {result.execution_result.get('result', '')[:200]}...")
    
    # Test 2: Try to find a specific skill
    print("\n2. Testing skill discovery for 'data processing'...")
    result = discovery.find_skill("process csv data", min_confidence=0.1)
    print(f"Found skill: {result.skill_name}")
    print(f"Discovery level: {result.level.name}")
    print(f"Success: {result.success}")
    
    # Test 3: Get skill prompt
    if result.skill_name:
        print(f"\n3. Getting prompt for skill '{result.skill_name}'...")
        prompt = discovery.get_skill_prompt(result.skill_name)
        if prompt:
            print(f"Prompt preview: {prompt[:150]}...")
        else:
            print("No prompt available")

def test_deepagents_integration():
    """Test DeepAgents integration (mock)"""
    print("\n=== Testing DeepAgents Integration ===")
    
    # Since we don't have actual LLM service, we'll just test the tool creation
    try:
        # Create a mock LLM service config
        class MockLLMService:
            def __init__(self):
                self.gateway = MockGateway()
        
        class MockGateway:
            def __init__(self):
                self.config = MockConfig()
            def get_model_info(self):
                return {"model": "mock-model", "provider": "mock"}
        
        class MockConfig:
            def __init__(self):
                self.model = "gpt-4"
                self.provider = "openai"
                self.api_key = "mock-key"
                self.base_url = None
                self.temperature = 0.7
                self.max_tokens = 4000
        
        # Test tool creation
        mock_llm = MockLLMService()
        agent = SafeClawDeepAgent(mock_llm, {"test_mode": True})
        
        # Get tools
        tools = agent._get_safe_claw_tools()
        print(f"✅ Successfully created {len(tools)} tools")
        
        # List tool names
        tool_names = [tool.name for tool in tools if hasattr(tool, 'name')]
        print(f"Tools: {tool_names}")
        
        # Get agent info
        info = agent.get_agent_info()
        print(f"✅ Agent info: {info.get('status')}")
        if 'skills_system' in info:
            skills_stats = info['skills_system'].get('skills_stats', {})
            print(f"Skills loaded: {skills_stats.get('total_skills', 0)}")
        
    except Exception as e:
        print(f"❌ Error in DeepAgents integration test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing DeepAgents + Skills Integration")
    print("=" * 50)
    
    test_skills_discovery()
    test_deepagents_integration()
    
    print("\n" + "=" * 50)
    print("Test completed!")
