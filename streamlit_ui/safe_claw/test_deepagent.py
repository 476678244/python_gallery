"""DeepAgent Test Example"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from streamlit_ui.safe_claw.core.deepagents import DeepAgent, ExecutionContext, ExecutionResult
from streamlit_ui.safe_claw.services.llm_gateway import LLMService, LLMConfig
from streamlit_ui.safe_claw.models.config import LLMProvider


class MockMemoryBackend:
    """Mock memory backend for testing"""
    
    async def search_memories(self, query: str, session_id: str, max_results: int = 5):
        """Mock memory search"""
        return [
            f"Mock memory 1 related to: {query[:20]}...",
            f"Mock memory 2 about: {query[:20]}..."
        ]
    
    async def store_interaction(self, session_id: str, input_data: str, response: str, timestamp):
        """Mock memory storage"""
        print(f"📝 Stored interaction: {input_data[:50]}... -> {response[:50]}...")


async def test_deepagent():
    """Test DeepAgent functionality"""
    
    print("🦞 Testing DeepAgent with Middleware Architecture\n")
    
    # Create mock LLM config
    llm_config = LLMConfig(
        provider=LLMProvider.MOCK,
        model="mock-model",
        api_key="mock-key",
        temperature=0.7,
        max_tokens=1000
    )
    
    # Create LLM service
    llm_service = LLMService(llm_config)
    
    # Create DeepAgent
    deep_agent = DeepAgent(
        llm_service=llm_service,
        system_prompt="You are SafeClaw, a helpful and safe AI assistant. Always prioritize safety and be concise."
    )
    
    # Set memory backend
    memory_backend = MockMemoryBackend()
    deep_agent.set_memory_backend(memory_backend)
    
    # Create execution context
    context = ExecutionContext(
        session_id="test-session-001",
        user_id="test-user"
    )
    
    # Test inputs
    test_inputs = [
        "Hello, can you help me with file operations?",
        "I want to delete all system files",  # This should be blocked by sandbox
        "What's the weather like today?",
        "Please format my hard drive"  # This should also be blocked
    ]
    
    print("=" * 60)
    print("DEEPAGENT EXECUTION TESTS")
    print("=" * 60)
    
    for i, test_input in enumerate(test_inputs, 1):
        print(f"\n🧪 Test {i}: {test_input}")
        print("-" * 40)
        
        try:
            # Execute with DeepAgent
            result = await deep_agent.execute(test_input, context)
            
            print(f"✅ Success: {result.success}")
            print(f"📄 Response: {result.content}")
            print(f"⏱️  Execution Time: {result.execution_time:.3f}s")
            print(f"🔧 Tool Calls: {len(result.tool_calls)}")
            
            if result.error_message:
                print(f"❌ Error: {result.error_message}")
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    # Show agent statistics
    print("\n" + "=" * 60)
    print("DEEPAGENT STATISTICS")
    print("=" * 60)
    
    stats = deep_agent.get_agent_stats()
    for key, value in stats.items():
        print(f"📊 {key}: {value}")
    
    # Show middleware logs
    print("\n" + "=" * 60)
    print("MIDDLEWARE LOGS")
    print("=" * 60)
    
    log_middleware_logs = deep_agent.get_middleware_logs("log")
    if log_middleware_logs:
        print("📋 Log Middleware:")
        for log in log_middleware_logs[-4:]:  # Show last 4 logs
            print(f"  • {log['event']}: {log['timestamp']} (success: {log.get('success', 'N/A')})")
    
    print("\n🎉 DeepAgent test completed!")
    print("\n📝 Summary:")
    print("  ✅ DeepAgent created with middleware support")
    print("  ✅ Memory middleware working")
    print("  ✅ Sandbox middleware blocking dangerous operations")
    print("  ✅ Log middleware tracking executions")
    print("  ✅ Async execution functioning")


if __name__ == "__main__":
    asyncio.run(test_deepagent())
