"""Integration tests for SafeClaw workflows"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import json

from safe_claw.core.graph.builder import SafeClawGraphBuilder
from safe_claw.core.graph.state import SafeClawState
from safe_claw.services.llm_gateway import LLMService
from safe_claw.core.memory.manager import MemoryManager
from safe_claw.core.skills.registry import SkillRegistry
from safe_claw.models.config import SafeClawConfig, LLMConfig

class TestWorkflowIntegration:
    """Test end-to-end workflow integration"""
    
    @pytest.fixture
    def integrated_system(self, temp_workspace, mock_llm_service, sample_config):
        """Create fully integrated system for testing"""
        # Create memory manager
        memory_manager = MemoryManager(sample_config.memory, temp_workspace)
        
        # Create graph builder
        graph_builder = SafeClawGraphBuilder(
            mock_llm_service,
            memory_manager,
            {"debug": True}
        )
        
        # Create skill registry
        skill_registry = SkillRegistry()
        
        return {
            "memory_manager": memory_manager,
            "graph_builder": graph_builder,
            "skill_registry": skill_registry,
            "llm_service": mock_llm_service,
            "config": sample_config
        }
    
    def test_simple_chat_workflow(self, integrated_system, sample_user_input):
        """Test simple chat workflow"""
        graph_builder = integrated_system["graph_builder"]
        
        # Create simple chat graph
        graph = graph_builder.build_simple_chat_graph()
        
        # Create state
        state = SafeClawState(
            user_input=sample_user_input,
            session_id="test_session",
            messages=[],
            start_time=datetime.now()
        )
        
        # Execute workflow
        config = {"configurable": {"thread_id": "test_session"}}
        result = graph.invoke(state, config)
        
        # Verify result
        assert "response" in result
        assert "current_agent" in result
        assert result["current_agent"] == "chat_agent"
        assert "execution_path" in result
        assert "chat_agent" in result["execution_path"]
    
    def test_multi_agent_workflow(self, integrated_system, sample_user_input):
        """Test multi-agent workflow"""
        graph_builder = integrated_system["graph_builder"]
        
        # Create multi-agent graph
        graph = graph_builder.build_multi_agent_graph()
        
        # Create state
        state = SafeClawState(
            user_input=sample_user_input,
            session_id="test_session",
            messages=[],
            start_time=datetime.now()
        )
        
        # Execute workflow
        config = {"configurable": {"thread_id": "test_session"}}
        result = graph.invoke(state, config)
        
        # Verify result
        assert "response" in result
        assert "current_agent" in result
        assert "execution_path" in result
        assert "router" in result["execution_path"]
    
    def test_advanced_workflow_with_memory(self, integrated_system, sample_user_input):
        """Test advanced workflow with memory integration"""
        graph_builder = integrated_system["graph_builder"]
        memory_manager = integrated_system["memory_manager"]
        
        # Add some memories
        memory_manager.add_memory(
            content="User is interested in Python programming",
            importance_score=0.8,
            keywords=["python", "programming"]
        )
        
        # Create advanced graph
        graph = graph_builder.build_advanced_graph()
        
        # Create state
        state = SafeClawState(
            user_input="Tell me about Python programming",
            session_id="test_session",
            messages=[],
            start_time=datetime.now()
        )
        
        # Execute workflow
        config = {"configurable": {"thread_id": "test_session"}}
        result = graph.invoke(state, config)
        
        # Verify result
        assert "response" in result
        assert "active_memories" in result
        assert len(result["active_memories"]) > 0
        assert "memory_retrieval" in result["execution_path"]
        assert "router" in result["execution_path"]
    
    def test_memory_integration_workflow(self, integrated_system):
        """Test memory integration across workflow"""
        memory_manager = integrated_system["memory_manager"]
        graph_builder = integrated_system["graph_builder"]
        
        # Create advanced graph
        graph = graph_builder.build_advanced_graph()
        
        # First interaction - should create memories
        state1 = SafeClawState(
            user_input="I love Python programming",
            session_id="test_session",
            messages=[],
            start_time=datetime.now()
        )
        
        config = {"configurable": {"thread_id": "test_session"}}
        result1 = graph.invoke(state1, config)
        
        # Check memories were created
        stats = memory_manager.get_memory_stats()
        assert stats["active_count"] > 0
        
        # Second interaction - should retrieve memories
        state2 = SafeClawState(
            user_input="What do you remember about my interests?",
            session_id="test_session",
            messages=[],
            start_time=datetime.now()
        )
        
        result2 = graph.invoke(state2, config)
        
        # Should have retrieved memories
        assert "active_memories" in result2
        assert len(result2["active_memories"]) > 0
    
    def test_skill_integration_workflow(self, integrated_system):
        """Test skill integration in workflow"""
        # Load built-in skills
        from core.skills.registry import load_builtin_skills
        skill_registry = load_builtin_skills()
        
        graph_builder = integrated_system["graph_builder"]
        
        # Create advanced graph
        graph = graph_builder.build_advanced_graph()
        
        # Test file operation skill
        state = SafeClawState(
            user_input="Read the file test.py",
            session_id="test_session",
            messages=[],
            start_time=datetime.now()
        )
        
        config = {"configurable": {"thread_id": "test_session"}}
        result = graph.invoke(state, config)
        
        # Verify workflow completed
        assert "response" in result
        assert "current_agent" in result
    
    @patch('core.skills.built_in.file_ops.Path.exists')
    @patch('core.skills.built_in.file_ops.Path.is_file')
    def test_file_operation_workflow(self, mock_is_file, mock_exists, integrated_system, temp_workspace):
        """Test file operation workflow"""
        mock_exists.return_value = True
        mock_is_file.return_value = True
        
        # Create test file
        test_file = Path(temp_workspace) / "test.py"
        test_file.write_text("print('Hello, World!')")
        
        graph_builder = integrated_system["graph_builder"]
        
        # Create advanced graph
        graph = graph_builder.build_advanced_graph()
        
        state = SafeClawState(
            user_input="Read the file test.py",
            session_id="test_session",
            messages=[],
            start_time=datetime.now()
        )
        
        config = {"configurable": {"thread_id": "test_session"}}
        result = graph.invoke(state, config)
        
        # Verify result
        assert "response" in result
        assert result["current_agent"] in ["chat_agent", "router_agent"]
    
    def test_error_handling_workflow(self, integrated_system, error_simulator):
        """Test error handling in workflow"""
        graph_builder = integrated_system["graph_builder"]
        
        # Simulate LLM error
        integrated_system["llm_service"].invoke.side_effect = Exception("LLM Error")
        
        # Create simple chat graph
        graph = graph_builder.build_simple_chat_graph()
        
        state = SafeClawState(
            user_input="Test message",
            session_id="test_session",
            messages=[],
            start_time=datetime.now()
        )
        
        config = {"configurable": {"thread_id": "test_session"}}
        
        # Should handle error gracefully
        with pytest.raises(Exception):
            result = graph.invoke(state, config)
    
    def test_concurrent_sessions_workflow(self, integrated_system):
        """Test handling multiple concurrent sessions"""
        graph_builder = integrated_system["graph_builder"]
        graph = graph_builder.build_advanced_graph()
        
        # Create multiple session states
        sessions = []
        for i in range(3):
            state = SafeClawState(
                user_input=f"Message from session {i}",
                session_id=f"session_{i}",
                messages=[],
                start_time=datetime.now()
            )
            sessions.append(state)
        
        # Execute workflows concurrently
        results = []
        for state in sessions:
            config = {"configurable": {"thread_id": state["session_id"]}}
            result = graph.invoke(state, config)
            results.append(result)
        
        # Verify all sessions handled
        assert len(results) == 3
        for i, result in enumerate(results):
            assert "response" in result
            assert result["session_id"] == f"session_{i}"
    
    def test_workflow_state_persistence(self, integrated_system):
        """Test workflow state persistence"""
        graph_builder = integrated_system["graph_builder"]
        graph = graph_builder.build_advanced_graph()
        
        # Create initial state
        state = SafeClawState(
            user_input="Initial message",
            session_id="test_session",
            messages=[],
            start_time=datetime.now()
        )
        
        config = {"configurable": {"thread_id": "test_session"}}
        
        # Execute first step
        result1 = graph.invoke(state, config)
        
        # Create new state with previous context
        state2 = SafeClawState(
            user_input="Follow up message",
            session_id="test_session",
            messages=result1.get("messages", []),
            start_time=datetime.now()
        )
        
        # Execute second step
        result2 = graph.invoke(state2, config)
        
        # Verify state continuity
        assert result2["session_id"] == "test_session"
        assert "response" in result2

class TestMemoryWorkflowIntegration:
    """Test memory system integration with workflows"""
    
    def test_memory_automatic_storage(self, integrated_system):
        """Test automatic memory storage during workflow"""
        memory_manager = integrated_system["memory_manager"]
        graph_builder = integrated_system["graph_builder"]
        
        graph = graph_builder.build_advanced_graph()
        
        # Create conversation
        state = SafeClawState(
            user_input="I'm working on a machine learning project using Python",
            session_id="test_session",
            messages=[],
            start_time=datetime.now()
        )
        
        config = {"configurable": {"thread_id": "test_session"}}
        result = graph.invoke(state, config)
        
        # Check if memory was stored
        stats = memory_manager.get_memory_stats()
        assert stats["active_count"] > 0
        
        # Search for the memory
        memories = memory_manager.search_memories("machine learning", max_results=5)
        assert len(memories) > 0
    
    def test_memory_retrieval_integration(self, integrated_system):
        """Test memory retrieval integration"""
        memory_manager = integrated_system["memory_manager"]
        graph_builder = integrated_system["graph_builder"]
        
        # Pre-populate memory
        memory_manager.add_memory(
            content="User prefers Python for data analysis",
            importance_score=0.8,
            keywords=["python", "data", "analysis"]
        )
        
        graph = graph_builder.build_advanced_graph()
        
        # Query about related topic
        state = SafeClawState(
            user_input="What programming language should I use for data analysis?",
            session_id="test_session",
            messages=[],
            start_time=datetime.now()
        )
        
        config = {"configurable": {"thread_id": "test_session"}}
        result = graph.invoke(state, config)
        
        # Should have retrieved relevant memories
        assert "active_memories" in result
        assert len(result["active_memories"]) > 0
    
    def test_memory_cleanup_integration(self, integrated_system):
        """Test memory cleanup integration"""
        memory_manager = integrated_system["memory_manager"]
        graph_builder = integrated_system["graph_builder"]
        
        # Add many memories to trigger cleanup
        for i in range(25):  # More than active_memory_max
            memory_manager.add_memory(
                content=f"Test memory {i}",
                importance_score=0.5 + (i % 3) * 0.2
            )
        
        # Check initial state
        stats_before = memory_manager.get_memory_stats()
        
        # Run cleanup
        memory_manager.cleanup_old_memories()
        
        # Check after cleanup
        stats_after = memory_manager.get_memory_stats()
        
        # Should have redistributed memories
        assert stats_after["active_count"] <= memory_manager.config.active_memory_max

class TestSafetyWorkflowIntegration:
    """Test safety system integration with workflows"""
    
    def test_safety_check_integration(self, integrated_system):
        """Test safety check integration"""
        from core.safety.checker import SafetyChecker
        from core.safety.policies import PolicyEngine
        
        # Create safety checker
        safety_checker = SafetyChecker(integrated_system["config"].safety)
        
        # Test safe request
        is_safe, message, result = safety_checker.check_request(
            "Tell me about Python programming",
            "test_session"
        )
        
        assert is_safe is True
        assert "Safe" in message
        
        # Test dangerous request
        is_safe, message, result = safety_checker.check_request(
            "rm -rf /",
            "test_session"
        )
        
        assert is_safe is False
        assert "Blocked" in message
    
    def test_safety_tool_call_integration(self, integrated_system):
        """Test safety tool call integration"""
        from core.safety.checker import SafetyChecker
        
        safety_checker = SafetyChecker(integrated_system["config"].safety)
        
        # Test safe tool call
        is_safe, message, result = safety_checker.check_tool_call(
            "read_file",
            {"file_path": "test.txt"},
            "test_session"
        )
        
        assert is_safe is True
        
        # Test dangerous tool call
        is_safe, message, result = safety_checker.check_tool_call(
            "execute_command",
            {"command": "rm -rf /"},
            "test_session"
        )
        
        assert is_safe is False

class TestLLMWorkflowIntegration:
    """Test LLM integration with workflows"""
    
    def test_llm_provider_switching(self, integrated_system):
        """Test switching between LLM providers"""
        llm_service = integrated_system["llm_service"]
        
        # Test OpenAI
        assert llm_service.get_model_info()["provider"] == "openai"
        
        # Update to Anthropic
        from models.config import LLMConfig
        anthropic_config = LLMConfig(
            provider="anthropic",
            model="claude-3-haiku-20240307",
            api_key="test_key"
        )
        
        llm_service.update_config(anthropic_config)
        
        # Should have updated
        assert llm_service.get_model_info()["provider"] == "anthropic"
    
    def test_llm_streaming_integration(self, integrated_system):
        """Test LLM streaming integration"""
        llm_service = integrated_system["llm_service"]
        
        messages = [{"role": "user", "content": "Hello"}]
        
        # Test streaming
        chunks = list(llm_service.stream(messages))
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)
    
    def test_llm_error_handling(self, integrated_system, error_simulator):
        """Test LLM error handling"""
        llm_service = integrated_system["llm_service"]
        
        # Simulate LLM error
        llm_service.gateway.invoke.side_effect = Exception("LLM unavailable")
        
        messages = [{"role": "user", "content": "Hello"}]
        
        # Should handle error gracefully
        result = llm_service.invoke(messages)
        assert "Error" in result

class TestEndToEndWorkflow:
    """End-to-end workflow tests"""
    
    def test_complete_user_interaction(self, integrated_system, temp_workspace):
        """Test complete user interaction flow"""
        memory_manager = integrated_system["memory_manager"]
        graph_builder = integrated_system["graph_builder"]
        
        # Create test file
        test_file = Path(temp_workspace) / "example.py"
        test_file.write_text("""
def greet(name):
    return f"Hello, {name}!"

print(greet("World"))
""")
        
        graph = graph_builder.build_advanced_graph()
        
        # Step 1: Initial greeting
        state1 = SafeClawState(
            user_input="Hello, I'm working on a Python project",
            session_id="test_session",
            messages=[],
            start_time=datetime.now()
        )
        
        config = {"configurable": {"thread_id": "test_session"}}
        result1 = graph.invoke(state1, config)
        
        # Step 2: File operation request
        state2 = SafeClawState(
            user_input="Can you read the file example.py?",
            session_id="test_session",
            messages=[],
            start_time=datetime.now()
        )
        
        result2 = graph.invoke(state2, config)
        
        # Step 3: Memory-based question
        state3 = SafeClawState(
            user_input="What do you remember about my project?",
            session_id="test_session",
            messages=[],
            start_time=datetime.now()
        )
        
        result3 = graph.invoke(state3, config)
        
        # Verify complete flow
        assert "response" in result1
        assert "response" in result2
        assert "response" in result3
        
        # Check memories were created and retrieved
        stats = memory_manager.get_memory_stats()
        assert stats["active_count"] > 0
        
        assert "active_memories" in result3
        assert len(result3["active_memories"]) > 0
    
    def test_workflow_performance(self, integrated_system, performance_monitor):
        """Test workflow performance"""
        graph_builder = integrated_system["graph_builder"]
        graph = graph_builder.build_simple_chat_graph()
        
        # Measure performance
        times = []
        for i in range(10):
            performance_monitor.start()
            
            state = SafeClawState(
                user_input=f"Test message {i}",
                session_id=f"perf_test_{i}",
                messages=[],
                start_time=datetime.now()
            )
            
            config = {"configurable": {"thread_id": f"perf_test_{i}"}}
            result = graph.invoke(state, config)
            
            duration = performance_monitor.stop()
            times.append(duration)
            
            assert "response" in result
        
        # Check performance metrics
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        assert avg_time < 5.0  # Should complete within 5 seconds on average
        assert max_time < 10.0  # Should never take more than 10 seconds
