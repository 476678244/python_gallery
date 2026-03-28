"""Pytest configuration and fixtures for SafeClaw tests"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock
import json

from streamlit_ui.safe_claw.models.config import SafeClawConfig, LLMConfig, SafetyConfig, MemoryConfig
from streamlit_ui.safe_claw.services.llm_gateway import LLMService
from streamlit_ui.safe_claw.core.memory.manager import MemoryManager
from streamlit_ui.safe_claw.core.safety.checker import SafetyChecker
from streamlit_ui.safe_claw.services.session_service import SessionService
from streamlit_ui.safe_claw.services.config_service import ConfigService
from streamlit_ui.safe_claw.core.skills.registry import SkillRegistry
from streamlit_ui.safe_claw.core.graph.builder import SafeClawGraphBuilder

@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return SafeClawConfig(
        llm=LLMConfig(
            provider="openai",
            model="gpt-3.5-turbo",
            api_key="test_key",
            temperature=0.7,
            max_tokens=1000
        ),
        safety=SafetyConfig(
            enable_confirmation=True,
            blacklist_commands=["rm -rf /", "format"],
            whitelist_operations=["read_file", "chat"]
        ),
        memory=MemoryConfig(
            enable_vector_search=False,
            active_memory_max=10,
            dormant_wakeup_threshold=0.6,
            deep_memory_compression="basic"
        ),
        debug=True,
        log_level="DEBUG"
    )

@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing"""
    mock_service = Mock(spec=LLMService)
    mock_service.invoke.return_value = "Test response"
    mock_service.stream.return_value = iter(["Test", " ", "response"])
    mock_service.get_model_info.return_value = {
        "provider": "openai",
        "model": "gpt-3.5-turbo"
    }
    return mock_service

@pytest.fixture
def memory_manager(temp_workspace, sample_config):
    """Memory manager instance for testing"""
    return MemoryManager(sample_config.memory, temp_workspace)

@pytest.fixture
def safety_checker(sample_config):
    """Safety checker instance for testing"""
    return SafetyChecker(sample_config.safety)

@pytest.fixture
def session_service(temp_workspace):
    """Session service instance for testing"""
    return SessionService(temp_workspace)

@pytest.fixture
def config_service(temp_workspace, sample_config):
    """Configuration service instance for testing"""
    service = ConfigService(temp_workspace)
    service.update_config(sample_config)
    return service

@pytest.fixture
def skill_registry():
    """Skill registry instance for testing"""
    return SkillRegistry()

@pytest.fixture
def graph_builder(mock_llm_service, memory_manager, sample_config):
    """Graph builder instance for testing"""
    return SafeClawGraphBuilder(mock_llm_service, memory_manager, {"debug": True})

@pytest.fixture
def sample_user_input():
    """Sample user input for testing"""
    return "Hello, SafeClaw! Can you help me analyze this code?"

@pytest.fixture
def sample_memory_data():
    """Sample memory data for testing"""
    return [
        {
            "id": "mem1",
            "content": "User likes Python programming",
            "layer": "active",
            "importance_score": 0.8,
            "keywords": ["python", "programming"],
            "created_at": "2024-01-01T00:00:00",
            "accessed_at": "2024-01-01T00:00:00",
            "access_count": 5
        },
        {
            "id": "mem2",
            "content": "User is working on a data analysis project",
            "layer": "dormant",
            "importance_score": 0.6,
            "keywords": ["data", "analysis", "project"],
            "created_at": "2024-01-02T00:00:00",
            "accessed_at": "2024-01-02T00:00:00",
            "access_count": 2
        }
    ]

@pytest.fixture
def sample_file_content():
    """Sample file content for testing"""
    return """def hello_world():
    print("Hello, World!")
    return "Hello, World!"

if __name__ == "__main__":
    hello_world()
"""

@pytest.fixture
def sample_code_snippet():
    """Sample code snippet for testing"""
    return """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Test the function
for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")
"""

@pytest.fixture(scope="session")
def test_data_dir():
    """Directory containing test data files"""
    return Path(__file__).parent / "test_data"

@pytest.fixture
def mock_streamlit():
    """Mock Streamlit for UI testing"""
    import streamlit as st
    st.session_state = {}
    st.sidebar = Mock()
    st.chat_input = Mock(return_value="")
    st.chat_message = Mock()
    st.write = Mock()
    st.error = Mock()
    st.success = Mock()
    st.warning = Mock()
    st.info = Mock()
    st.spinner = Mock()
    st.expander = Mock()
    st.button = Mock(return_value=False)
    st.selectbox = Mock(return_value="option1")
    st.slider = Mock(return_value=0.5)
    st.text_input = Mock(return_value="")
    st.text_area = Mock(return_value="")
    st.checkbox = Mock(return_value=False)
    st.columns = Mock(return_value=[Mock(), Mock()])
    st.metric = Mock()
    st.dataframe = Mock()
    st.plotly_chart = Mock()
    st.file_uploader = Mock(return_value=None)
    st.download_button = Mock()
    return st

# Test utilities
def create_test_file(file_path: str, content: str = "Test content"):
    """Create a test file with given content"""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path

def create_test_directory(dir_path: str):
    """Create a test directory"""
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def assert_valid_memory(memory):
    """Assert that a memory object has valid structure"""
    assert "id" in memory
    assert "content" in memory
    assert "layer" in memory
    assert "importance_score" in memory
    assert "created_at" in memory
    assert "accessed_at" in memory
    assert "access_count" in memory
    assert isinstance(memory["importance_score"], (int, float))
    assert 0 <= memory["importance_score"] <= 1

def assert_valid_session(session):
    """Assert that a session object has valid structure"""
    assert "id" in session
    assert "user_id" in session
    assert "created_at" in session
    assert "updated_at" in session
    assert "message_count" in session
    assert isinstance(session["message_count"], int)
    assert session["message_count"] >= 0

def assert_valid_config(config):
    """Assert that a config object has valid structure"""
    assert "llm" in config
    assert "safety" in config
    assert "memory" in config
    assert "debug" in config
    assert "log_level" in config
    
    # Validate LLM config
    llm = config["llm"]
    assert "provider" in llm
    assert "model" in llm
    assert "temperature" in llm
    assert "max_tokens" in llm
    assert 0 <= llm["temperature"] <= 2
    assert llm["max_tokens"] > 0

# Async test utilities
@pytest.fixture
def event_loop():
    """Create an event loop for async tests"""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# Database fixtures for testing
@pytest.fixture
def mock_database():
    """Mock database for testing"""
    class MockDB:
        def __init__(self):
            self.data = {}
        
        def get(self, key):
            return self.data.get(key)
        
        def set(self, key, value):
            self.data[key] = value
        
        def delete(self, key):
            return self.data.pop(key, None)
        
        def clear(self):
            self.data.clear()
    
    return MockDB()

# API client fixtures
@pytest.fixture
def mock_api_client():
    """Mock API client for testing"""
    client = Mock()
    client.get.return_value = Mock(status_code=200, json=lambda: {"status": "ok"})
    client.post.return_value = Mock(status_code=201, json=lambda: {"id": "123"})
    client.put.return_value = Mock(status_code=200, json=lambda: {"updated": True})
    client.delete.return_value = Mock(status_code=204)
    return client

# Performance testing fixtures
@pytest.fixture
def performance_monitor():
    """Performance monitoring fixture"""
    import time
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.measurements = []
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
            if self.start_time:
                duration = self.end_time - self.start_time
                self.measurements.append(duration)
                return duration
            return None
        
        def get_average_time(self):
            if not self.measurements:
                return 0
            return sum(self.measurements) / len(self.measurements)
        
        def get_max_time(self):
            return max(self.measurements) if self.measurements else 0
        
        def get_min_time(self):
            return min(self.measurements) if self.measurements else 0
    
    return PerformanceMonitor()

# Error simulation fixtures
@pytest.fixture
def error_simulator():
    """Error simulation fixture"""
    class ErrorSimulator:
        def __init__(self):
            self.should_fail = False
            self.error_message = "Simulated error"
            self.error_type = Exception
        
        def enable_failure(self, message="Simulated error", error_type=Exception):
            self.should_fail = True
            self.error_message = message
            self.error_type = error_type
        
        def disable_failure(self):
            self.should_fail = False
        
        def check_failure(self):
            if self.should_fail:
                raise self.error_type(self.error_message)
    
    return ErrorSimulator()
