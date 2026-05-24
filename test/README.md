# SafeClaw Test Suite

This directory contains comprehensive tests for the SafeClaw AI assistant system.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                # Pytest configuration and fixtures
├── pytest.ini                 # Pytest configuration file
├── test_runner.py              # Test runner script
├── README.md                   # This file
├── unit/                       # Unit tests
│   ├── __init__.py
│   ├── test_models.py          # Test data models
│   ├── test_services.py        # Test service layer
│   └── test_memory.py          # Test memory system
└── integration/                # Integration tests
    ├── __init__.py
    ├── test_workflows.py       # Test workflow integration
    └── test_ui.py              # Test UI integration
```

## Test Categories

### Unit Tests (`tests/unit/`)

- **Models**: Test Pydantic models and data validation
- **Services**: Test LLM gateway, session service, config service
- **Memory**: Test memory layers, storage, and retrieval
- **Skills**: Test skill framework and built-in skills
- **Safety**: Test safety policies and validation
- **Utils**: Test utility functions and helpers

### Integration Tests (`tests/integration/`)

- **Workflows**: Test end-to-end LangGraph workflows
- **UI**: Test Streamlit UI components and pages
- **API**: Test external API integrations
- **Database**: Test database operations (if applicable)

## Running Tests

### Quick Start

```bash
# Run all tests
python tests/test_runner.py

# Run with coverage
python tests/test_runner.py --coverage

# Run specific test types
python tests/test_runner.py unit
python tests/test_runner.py integration
python tests/test_runner.py ui
```

### Using Pytest Directly

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio pytest-mock pytest-timeout

# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=services --cov=models --cov=utils --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py

# Run with markers
pytest -m unit
pytest -m integration
pytest -m ui
pytest -m workflow
pytest -m memory
pytest -m safety
```

### Test Markers

- `unit`: Unit tests (fast, isolated)
- `integration`: Integration tests (slower, external dependencies)
- `ui`: UI tests (requires Streamlit mocking)
- `workflow`: Workflow tests (LangGraph integration)
- `memory`: Memory system tests
- `safety`: Safety system tests
- `llm`: LLM integration tests
- `skills`: Skill framework tests
- `slow`: Slow tests (network I/O, large datasets)

## Fixtures

### Core Fixtures

- `temp_workspace`: Temporary directory for test data
- `sample_config`: Sample SafeClaw configuration
- `mock_llm_service`: Mocked LLM service
- `memory_manager`: Real memory manager with temp storage
- `safety_checker`: Real safety checker
- `session_service`: Real session service
- `config_service`: Real config service
- `skill_registry`: Real skill registry
- `graph_builder`: Real graph builder with mocked LLM

### Data Fixtures

- `sample_user_input`: Sample user message
- `sample_memory_data`: Sample memory records
- `sample_file_content`: Sample file for testing
- `sample_code_snippet`: Sample code for analysis

### Utility Fixtures

- `mock_streamlit`: Mocked Streamlit functions
- `performance_monitor`: Performance measurement utility
- `error_simulator`: Error simulation utility
- `mock_database`: Mock database for testing

## Test Configuration

### Pytest Configuration (`pytest.ini`)

```ini
[tool:pytest]
minversion = 6.0
addopts = -ra -q --strict-markers
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

[pytest.markers]
slow = marks tests as slow
integration = marks tests as integration tests
unit = marks tests as unit tests
ui = marks tests as UI tests
workflow = marks tests as workflow tests
```

### Environment Variables

```bash
# For LLM tests
export OPENAI_API_KEY="your_test_key"
export ANTHROPIC_API_KEY="your_test_key"

# For test configuration
export SAFECLAW_TEST_MODE="true"
export SAFECLAW_ENCRYPTION_KEY="test_key"
```

## Writing Tests

### Unit Test Example

```python
def test_memory_creation(temp_workspace, sample_config):
    """Test creating a memory"""
    manager = MemoryManager(sample_config.memory, temp_workspace)
    
    memory_id = manager.add_memory(
        content="Test memory",
        importance_score=0.8,
        keywords=["test"]
    )
    
    assert memory_id is not None
    assert manager.get_memory(memory_id) is not None
```

### Integration Test Example

```python
def test_workflow_execution(integrated_system, sample_user_input):
    """Test complete workflow execution"""
    graph_builder = integrated_system["graph_builder"]
    graph = graph_builder.build_advanced_graph()
    
    state = SafeClawState(
        user_input=sample_user_input,
        session_id="test_session"
    )
    
    result = graph.invoke(state)
    
    assert "response" in result
    assert result["current_agent"] in ["chat_agent", "memory_agent"]
```

### UI Test Example

```python
@patch('streamlit_ui.pages.chat_page.st')
def test_chat_page_rendering(mock_st, mock_streamlit):
    """Test chat page rendering"""
    setup_session_state()
    
    from streamlit_ui.pages.chat_page import render
    render()
    
    mock_st.title.assert_called()
    mock_st.caption.assert_called()
```

## Test Data

### Test Data Directory

Create test data files in `tests/test_data/`:

```
tests/test_data/
├── sample_code.py
├── sample_document.md
├── sample_config.json
└── sample_memory.json
```

### Mock Data Generation

Use fixtures to generate test data:

```python
@pytest.fixture
def sample_memory_data():
    return [
        {
            "id": "mem1",
            "content": "User likes Python",
            "layer": "active",
            "importance_score": 0.8
        }
    ]
```

## Coverage

### Running Coverage

```bash
# Generate HTML coverage report
pytest --cov=core --cov=services --cov=models --cov=utils --cov-report=html

# Generate XML coverage report
pytest --cov=core --cov=services --cov=models --cov=utils --cov-report=xml

# Coverage with specific markers
pytest -m unit --cov=core --cov-report=term-missing
```

### Coverage Targets

- **Unit Tests**: > 90% coverage
- **Integration Tests**: > 80% coverage
- **Overall**: > 85% coverage

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.10, 3.11]

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio
    
    - name: Run tests
      run: |
        pytest --cov=core --cov=services --cov=models --cov=utils --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Debugging Tests

### Running Single Test

```bash
# Run single test function
pytest tests/unit/test_memory.py::test_memory_creation -v

# Run with debugging
pytest tests/unit/test_memory.py::test_memory_creation -v -s --tb=short

# Run with Python debugger
pytest --pdb tests/unit/test_memory.py::test_memory_creation
```

### Test Logging

```bash
# Enable test logging
pytest --log-cli-level=DEBUG

# Capture output
pytest -s --capture=no
```

## Performance Testing

### Benchmark Tests

```python
def test_memory_search_performance(memory_manager, performance_monitor):
    """Test memory search performance"""
    performance_monitor.start()
    
    results = memory_manager.search_memories("test query", max_results=100)
    
    duration = performance_monitor.stop()
    assert duration < 1.0  # Should complete within 1 second
    assert len(results) > 0
```

### Running Performance Tests

```bash
# Run performance tests
pytest -m performance --benchmark-only

# Generate benchmark report
pytest --benchmark-only --benchmark-json=benchmark.json
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from project root
2. **Missing Fixtures**: Check `conftest.py` for fixture definitions
3. **Async Tests**: Use `pytest-asyncio` and `@pytest.mark.asyncio`
4. **Mock Issues**: Verify mock setup in `conftest.py`
5. **Path Issues**: Use `temp_workspace` fixture for file operations

### Debug Tips

```bash
# Show test discovery
pytest --collect-only

# Dry run to check syntax
pytest --dry-run

# Verbose output
pytest -vv

# Stop on first failure
pytest -x

# Run with specific Python path
PYTHONPATH=. pytest
```

## Contributing Tests

### Adding New Tests

1. Choose appropriate test type (unit/integration)
2. Use existing fixtures when possible
3. Follow naming conventions (`test_*`)
4. Add appropriate markers (`@pytest.mark.unit`)
5. Include docstrings explaining test purpose
6. Test both success and failure cases

### Test Review Checklist

- [ ] Test has clear purpose
- [ ] Uses appropriate fixtures
- [ ] Has proper assertions
- [ ] Handles edge cases
- [ ] Is isolated from other tests
- [ ] Has meaningful assertions
- [ ] Follows naming conventions
- [ ] Includes appropriate markers

## Best Practices

1. **Arrange-Act-Assert**: Structure tests clearly
2. **Descriptive Names**: Use meaningful test names
3. **One Assertion**: Test one thing per test
4. **Fixtures**: Reuse fixtures for common setup
5. **Mocking**: Mock external dependencies
6. **Cleanup**: Clean up after tests
7. **Documentation**: Document complex test logic
8. **Error Messages**: Provide helpful assertion messages

## Test Metrics

### Coverage Goals

- Core modules: > 95%
- Service modules: > 90%
- Model modules: > 90%
- Utility modules: > 85%

### Performance Goals

- Unit tests: < 1 second each
- Integration tests: < 5 seconds each
- UI tests: < 2 seconds each
- Full test suite: < 5 minutes

### Quality Goals

- Zero flaky tests
- All tests pass consistently
- Clear error messages
- Comprehensive edge case coverage
- Good documentation

---

For more information, see the [Pytest documentation](https://docs.pytest.org/) and [Testing Best Practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html).
