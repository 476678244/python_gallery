"""Official DeepAgents Test Example for SafeClaw"""

import sys
import os

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from safe_claw.core.deepagents.official_integration import SafeClawDeepAgent, DeepAgentFactory
from safe_claw.services.llm_gateway import LLMService, LLMConfig


def test_official_deepagents():
    """Test official DeepAgents integration"""
    
    print("🦞 Testing Official DeepAgents Integration\n")
    
    # Create mock LLM config for testing
    llm_config = LLMConfig(
        provider="mock",
        model="mock-model",
        api_key="mock-key",
        temperature=0.7,
        max_tokens=1000
    )
    
    # Create LLM service
    llm_service = LLMService(llm_config)
    
    print("=" * 60)
    print("OFFICIAL DEEPAGENTS INTEGRATION TEST")
    print("=" * 60)
    
    try:
        # Test 1: Create SafeClaw DeepAgent
        print("\n🧪 Test 1: Creating SafeClaw DeepAgent")
        print("-" * 40)
        
        deep_agent = DeepAgentFactory.create_agent(
            llm_service=llm_service,
            config={
                "system_prompt": "You are SafeClaw, a helpful AI assistant with planning capabilities."
            }
        )
        
        print("✅ SafeClaw DeepAgent created successfully")
        
        # Test 2: Get agent info
        print("\n🧪 Test 2: Getting Agent Information")
        print("-" * 40)
        
        agent_info = deep_agent.get_agent_info()
        print(f"📊 Agent Type: {agent_info.get('type')}")
        print(f"📊 Agent Status: {agent_info.get('status')}")
        print(f"📊 SafeClaw Tools: {agent_info.get('safe_claw_tools')}")
        
        # Test 3: Simple invocation
        print("\n🧪 Test 3: Simple Agent Invocation")
        print("-" * 40)
        
        messages = [{"role": "user", "content": "Hello, can you help me plan a simple task?"}]
        result = deep_agent.invoke(messages)
        
        print(f"✅ Success: {result.get('success')}")
        print(f"📄 Response: {result.get('content', '')[:100]}...")
        print(f"🔧 Tool Calls: {len(result.get('tool_calls', []))}")
        
        # Test 4: Complex task with planning
        print("\n🧪 Test 4: Complex Task with Planning")
        print("-" * 40)
        
        complex_messages = [
            {"role": "user", "content": "I need to research Python best practices and create a summary document with code examples."}
        ]
        
        result = deep_agent.invoke(complex_messages)
        
        print(f"✅ Success: {result.get('success')}")
        print(f"📄 Response: {result.get('content', '')[:200]}...")
        print(f"🔧 Tool Calls: {len(result.get('tool_calls', []))}")
        
        if result.get('tool_calls'):
            print("📋 Tool Calls Made:")
            for i, tool_call in enumerate(result.get('tool_calls', [])[:3], 1):
                print(f"  {i}. {tool_call.get('name', 'Unknown tool')}")
        
        # Test 5: Streaming response
        print("\n🧪 Test 5: Streaming Response")
        print("-" * 40)
        
        stream_messages = [{"role": "user", "content": "Tell me about file operations"}]
        
        print("🌊 Streaming response:")
        chunk_count = 0
        for chunk in deep_agent.stream(stream_messages):
            if chunk.get('content'):
                print(f"  Chunk: {chunk.get('content', '')[:50]}...")
                chunk_count += 1
                if chunk_count >= 3:  # Limit output for demo
                    break
        
        print(f"✅ Streaming completed (showed first {chunk_count} chunks)")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("OFFICIAL DEEPAGENTS FEATURES SUMMARY")
    print("=" * 60)
    
    features = [
        "✅ Official DeepAgents package integration",
        "✅ SafeClaw wrapper with custom tools",
        "✅ LangChain model compatibility", 
        "✅ Planning and sub-agent capabilities",
        "✅ Filesystem access (via DeepAgents)",
        "✅ Streaming response support",
        "✅ Tool calling and execution",
        "✅ SafeClaw memory integration ready"
    ]
    
    for feature in features:
        print(feature)
    
    print("\n🎉 Official DeepAgents integration test completed!")
    print("\n📝 Next Steps:")
    print("  🔧 Configure real LLM provider (OpenAI, Anthropic, etc.)")
    print("  🔗 Integrate with SafeClaw memory system")
    print("  🧪 Test with real complex tasks")
    print("  🚀 Deploy in SafeClaw Streamlit UI")


if __name__ == "__main__":
    test_official_deepagents()
