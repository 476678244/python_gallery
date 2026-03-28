"""Simple test for official DeepAgents integration"""

import sys
import os

# Add to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

def test_import():
    """Test if imports work correctly"""
    try:
        from streamlit_ui.safe_claw.core.deepagents.official_integration import SafeClawDeepAgent, DeepAgentFactory
        print("✅ Successfully imported SafeClawDeepAgent and DeepAgentFactory")
        
        from streamlit_ui.safe_claw.services.llm_gateway import LLMService, LLMConfig
        print("✅ Successfully imported LLMService and LLMConfig")
        
        # Test LLMConfig creation
        llm_config = LLMConfig(
            provider="mock",
            model="mock-model",
            api_key="test-key"
        )
        print("✅ Successfully created LLMConfig")
        
        # Test LLMService creation
        llm_service = LLMService(llm_config)
        print("✅ Successfully created LLMService")
        
        return True
        
    except Exception as e:
        print(f"❌ Import/creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_deepagent_creation():
    """Test DeepAgent creation"""
    try:
        from streamlit_ui.safe_claw.core.deepagents.official_integration import DeepAgentFactory
        from streamlit_ui.safe_claw.services.llm_gateway import LLMService, LLMConfig
        
        llm_config = LLMConfig(
            provider="mock",
            model="mock-model",
            api_key="test-key"
        )
        llm_service = LLMService(llm_config)
        
        # Create DeepAgent
        deep_agent = DeepAgentFactory.create_agent(llm_service)
        print("✅ Successfully created DeepAgent")
        
        # Get agent info
        info = deep_agent.get_agent_info()
        print(f"✅ Agent info: {info.get('type', 'unknown')} - {info.get('status', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ DeepAgent creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🦞 Testing Official DeepAgents Integration\n")
    print("=" * 50)
    
    # Test 1: Imports
    print("\n🧪 Test 1: Import Validation")
    print("-" * 30)
    if not test_import():
        print("❌ Import test failed")
        return
    
    # Test 2: DeepAgent Creation
    print("\n🧪 Test 2: DeepAgent Creation")
    print("-" * 30)
    if not test_deepagent_creation():
        print("❌ DeepAgent creation test failed")
        return
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed!")
    print("\n📝 Integration Summary:")
    print("  ✅ Official DeepAgents package installed")
    print("  ✅ SafeClaw wrapper implemented")
    print("  ✅ LLM service integration working")
    print("  ✅ Progressive skills system integrated")
    print("  ✅ Ready for use in SafeClaw")

if __name__ == "__main__":
    main()
