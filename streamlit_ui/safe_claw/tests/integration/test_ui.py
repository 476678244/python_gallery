"""Integration tests for SafeClaw UI components"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import streamlit as st
import pandas as pd

# Mock streamlit before importing UI modules
@pytest.fixture(autouse=True)
def mock_streamlit():
    """Mock Streamlit for UI testing"""
    # Mock streamlit functions
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
    st.set_page_config = Mock()
    st.markdown = Mock()
    st.title = Mock()
    st.caption = Mock()
    st.subheader = Mock()
    st.code = Mock()
    st.json = Mock()
    st.table = Mock()
    st.progress = Mock()
    st.toggle = Mock(return_value=False)
    st.radio = Mock(return_value="option1")
    st.multiselect = Mock(return_value=[])
    st.number_input = Mock(return_value=1)
    st.date_input = Mock(return_value=datetime.now())
    st.time_input = Mock(return_value=datetime.now().time())
    st.color_picker = Mock(return_value="#000000")
    st.camera_input = Mock(return_value=None)
    st.image = Mock()
    st.audio = Mock()
    st.video = Mock()
    st.balloons = Mock()
    st.snow = Mock()
    st.toast = Mock()
    st.set_option = Mock()
    st.get_option = Mock(return_value=None)
    st.experimental_get_query_params = Mock(return_value={})
    st.experimental_set_query_params = Mock()

class TestChatPage:
    """Test chat page functionality"""
    
    @patch('streamlit_ui.pages.chat_page.st')
    def test_chat_page_rendering(self, mock_st, mock_streamlit, temp_workspace, sample_config):
        """Test chat page rendering"""
        # Setup session state
        st.session_state.update({
            'session_id': 'test_session',
            'messages': [],
            'safe_claw_config': sample_config,
            'workspace_path': temp_workspace,
            'llm_service': Mock(),
            'memory_manager': Mock(),
            'graph_builder': Mock(),
            'current_graph': Mock()
        })
        
        # Import and render chat page
        from streamlit_ui.pages.chat_page import render
        
        # Should render without errors
        render()
        
        # Verify key functions were called
        mock_st.title.assert_called()
        mock_st.caption.assert_called()
    
    @patch('streamlit_ui.pages.chat_page.st')
    def test_chat_message_display(self, mock_st, mock_streamlit):
        """Test chat message display"""
        from streamlit_ui.components.chat_message import render_message
        
        # Test user message
        user_message = {
            "role": "user",
            "content": "Hello, SafeClaw!",
            "timestamp": datetime.now()
        }
        
        render_message(user_message)
        mock_st.chat_message.assert_called_with("user")
        
        # Test assistant message
        assistant_message = {
            "role": "assistant",
            "content": "Hello! How can I help you?",
            "timestamp": datetime.now(),
            "metadata": {
                "agent": "chat_agent",
                "execution_path": ["chat_agent"]
            }
        }
        
        render_message(assistant_message)
        mock_st.chat_message.assert_called_with("assistant")
    
    @patch('streamlit_ui.pages.chat_page.st')
    def test_chat_input_handling(self, mock_st, mock_streamlit, temp_workspace, sample_config):
        """Test chat input handling"""
        # Setup session state
        st.session_state.update({
            'session_id': 'test_session',
            'messages': [],
            'safe_claw_config': sample_config,
            'workspace_path': temp_workspace,
            'llm_service': Mock(),
            'memory_manager': Mock(),
            'graph_builder': Mock(),
            'current_graph': Mock()
        })
        
        # Mock chat input
        mock_st.chat_input.return_value = "Hello, SafeClaw!"
        
        # Mock graph execution
        mock_graph = Mock()
        mock_graph.invoke.return_value = {
            "response": "Hello! How can I help you?",
            "current_agent": "chat_agent",
            "execution_path": ["chat_agent"]
        }
        st.session_state.current_graph = mock_graph
        
        from streamlit_ui.pages.chat_page import render
        
        render()
        
        # Verify graph was called
        mock_graph.invoke.assert_called()
    
    @patch('streamlit_ui.pages.chat_page.st')
    def test_error_handling_in_chat(self, mock_st, mock_streamlit, temp_workspace, sample_config):
        """Test error handling in chat"""
        # Setup session state with failing graph
        st.session_state.update({
            'session_id': 'test_session',
            'messages': [],
            'safe_claw_config': sample_config,
            'workspace_path': temp_workspace,
            'llm_service': Mock(),
            'memory_manager': Mock(),
            'graph_builder': Mock(),
            'current_graph': Mock()
        })
        
        # Mock chat input and graph error
        mock_st.chat_input.return_value = "Test message"
        st.session_state.current_graph.invoke.side_effect = Exception("Graph error")
        
        from streamlit_ui.pages.chat_page import render
        
        render()
        
        # Should handle error gracefully
        mock_st.error.assert_called()

class TestMemoryPage:
    """Test memory page functionality"""
    
    @patch('streamlit_ui.pages.memory_page.st')
    def test_memory_page_rendering(self, mock_st, mock_streamlit, temp_workspace, sample_config):
        """Test memory page rendering"""
        # Setup session state with mock memory manager
        mock_memory_manager = Mock()
        mock_memory_manager.get_memory_stats.return_value = {
            'active_count': 5,
            'dormant_count': 3,
            'deep_count': 2,
            'forgotten_count': 1
        }
        
        st.session_state.update({
            'memory_manager': mock_memory_manager
        })
        
        from streamlit_ui.pages.memory_page import render
        
        render()
        
        # Verify page elements
        mock_st.title.assert_called()
        mock_st.subheader.assert_called()
        mock_st.metric.assert_called()
    
    @patch('streamlit_ui.pages.memory_page.st')
    def test_memory_search_functionality(self, mock_st, mock_streamlit, temp_workspace, sample_config):
        """Test memory search functionality"""
        # Setup mock memory manager
        mock_memory_manager = Mock()
        mock_memory_manager.get_memory_stats.return_value = {
            'active_count': 5,
            'dormant_count': 3,
            'deep_count': 2,
            'forgotten_count': 1
        }
        
        # Mock search results
        mock_search_results = [
            Mock(memory=Mock(content="Python programming", importance_score=0.8), score=0.9)
        ]
        mock_memory_manager.search_memories.return_value = mock_search_results
        
        st.session_state.update({
            'memory_manager': mock_memory_manager
        })
        
        # Mock search input and button
        mock_st.text_input.return_value = "python"
        mock_st.button.return_value = True
        
        from streamlit_ui.pages.memory_page import render
        
        render()
        
        # Verify search was called
        mock_memory_manager.search_memories.assert_called_with("python", 10)
    
    @patch('streamlit_ui.pages.memory_page.st')
    def test_memory_layer_browsing(self, mock_st, mock_streamlit, temp_workspace, sample_config):
        """Test memory layer browsing"""
        # Setup mock memory manager
        mock_memory_manager = Mock()
        mock_memory_manager.get_memory_stats.return_value = {
            'active_count': 5,
            'dormant_count': 3,
            'deep_count': 2,
            'forgotten_count': 1
        }
        
        # Mock layer memories
        mock_memories = [
            Mock(
                id="mem1",
                content="Test memory",
                importance_score=0.7,
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                access_count=3,
                keywords=["test"]
            )
        ]
        mock_memory_manager.active_layer.get_all_memories.return_value = mock_memories
        
        st.session_state.update({
            'memory_manager': mock_memory_manager
        })
        
        # Mock layer selection and button
        mock_st.selectbox.return_value = "active"
        mock_st.button.return_value = True
        
        from streamlit_ui.pages.memory_page import render
        
        render()
        
        # Verify layer was accessed
        mock_memory_manager.active_layer.get_all_memories.assert_called()

class TestSettingsPage:
    """Test settings page functionality"""
    
    @patch('streamlit_ui.pages.settings_page.st')
    def test_settings_page_rendering(self, mock_st, mock_streamlit, temp_workspace, sample_config):
        """Test settings page rendering"""
        # Setup session state
        st.session_state.update({
            'safe_claw_config': sample_config,
            'workspace_path': temp_workspace,
            'llm_service': Mock(),
            'memory_manager': Mock(),
            'graph_builder': Mock()
        })
        
        from streamlit_ui.pages.settings_page import render
        
        render()
        
        # Verify page elements
        mock_st.title.assert_called()
        mock_st.subheader.assert_called()
        mock_st.expander.assert_called()
    
    @patch('streamlit_ui.pages.settings_page.st')
    def test_llm_configuration_update(self, mock_st, mock_streamlit, temp_workspace, sample_config):
        """Test LLM configuration update"""
        # Setup session state
        st.session_state.update({
            'safe_claw_config': sample_config,
            'workspace_path': temp_workspace,
            'llm_service': Mock(),
            'memory_manager': Mock(),
            'graph_builder': Mock()
        })
        
        # Mock configuration changes
        mock_st.selectbox.return_value = "anthropic"
        mock_st.text_input.return_value = "new_api_key"
        mock_st.button.return_value = True
        
        # Mock service reinitialization
        mock_llm_service = Mock()
        mock_memory_manager = Mock()
        mock_graph_builder = Mock()
        
        with patch('services.llm_gateway.LLMService', return_value=mock_llm_service), \
             patch('core.memory.manager.MemoryManager', return_value=mock_memory_manager), \
             patch('core.graph.builder.SafeClawGraphBuilder', return_value=mock_graph_builder):
            
            from streamlit_ui.pages.settings_page import render
            render()
            
            # Should attempt to save configuration
            mock_st.success.assert_called()
    
    @patch('streamlit_ui.pages.settings_page.st')
    def test_connection_testing(self, mock_st, mock_streamlit, temp_workspace, sample_config):
        """Test LLM connection testing"""
        # Setup session state with mock service
        mock_llm_service = Mock()
        mock_llm_service.invoke.return_value = "Test response"
        
        st.session_state.update({
            'safe_claw_config': sample_config,
            'workspace_path': temp_workspace,
            'llm_service': mock_llm_service,
            'memory_manager': Mock(),
            'graph_builder': Mock()
        })
        
        # Mock test button
        mock_st.button.return_value = True
        
        from streamlit_ui.pages.settings_page import render
        
        render()
        
        # Should test connection
        mock_llm_service.invoke.assert_called()
        mock_st.success.assert_called()

class TestStatsPage:
    """Test statistics page functionality"""
    
    @patch('streamlit_ui.pages.stats_page.st')
    def test_stats_page_rendering(self, mock_st, mock_streamlit, temp_workspace, sample_config):
        """Test statistics page rendering"""
        # Setup session state with mock memory manager
        mock_memory_manager = Mock()
        mock_memory_manager.get_memory_stats.return_value = {
            'active_count': 5,
            'dormant_count': 3,
            'deep_count': 2,
            'forgotten_count': 1
        }
        
        st.session_state.update({
            'memory_manager': mock_memory_manager
        })
        
        from streamlit_ui.pages.stats_page import render
        
        render()
        
        # Verify page elements
        mock_st.title.assert_called()
        mock_st.subheader.assert_called()
        mock_st.metric.assert_called()
    
    @patch('streamlit_ui.pages.stats_page.st')
    @patch('streamlit_ui.pages.stats.pd.DataFrame')
    @patch('streamlit_ui.pages.stats.px.pie')
    def test_memory_distribution_chart(self, mock_pie, mock_dataframe, mock_st, mock_streamlit, temp_workspace, sample_config):
        """Test memory distribution chart"""
        # Setup mock memory manager
        mock_memory_manager = Mock()
        mock_memory_manager.get_memory_stats.return_value = {
            'active_count': 5,
            'dormant_count': 3,
            'deep_count': 2,
            'forgotten_count': 1
        }
        
        st.session_state.update({
            'memory_manager': mock_memory_manager
        })
        
        # Mock chart
        mock_fig = Mock()
        mock_pie.return_value = mock_fig
        
        from streamlit_ui.pages.stats_page import render
        
        render()
        
        # Verify chart creation
        mock_pie.assert_called()
        mock_st.plotly_chart.assert_called()
    
    @patch('streamlit_ui.pages.stats_page.st')
    def test_performance_metrics(self, mock_st, mock_streamlit, temp_workspace, sample_config):
        """Test performance metrics display"""
        # Setup session state with mock data
        st.session_state.update({
            'memory_manager': Mock(),
            'messages': [
                {
                    'role': 'assistant',
                    'timestamp': datetime.now(),
                    'metadata': {
                        'agent': 'chat_agent',
                        'processing_time': 1.5
                    }
                }
            ]
        })
        
        from streamlit_ui.pages.stats_page import render
        
        render()
        
        # Should display metrics
        mock_st.subheader.assert_called()
        mock_st.metric.assert_called()

class TestSessionManager:
    """Test session manager component"""
    
    @patch('streamlit_ui.components.session_manager.st')
    def test_session_state_management(self, mock_st, mock_streamlit, temp_workspace):
        """Test session state management"""
        from streamlit_ui.components.session_manager import get_session_state, update_session_activity
        
        # Initialize session state
        if 'session_id' not in st.session_state:
            st.session_state.session_id = 'test_session'
            st.session_state.messages = []
            st.session_state.session_start = datetime.now()
        
        # Get session state
        state = get_session_state()
        
        assert 'session_id' in state
        assert 'message_count' in state
        assert 'start_time' in state
        
        # Update activity
        update_session_activity()
        
        assert 'last_activity' in st.session_state
    
    @patch('streamlit_ui.components.session_manager.st')
    def test_session_persistence(self, mock_st, mock_streamlit, temp_workspace):
        """Test session persistence"""
        from streamlit_ui.components.session_manager import save_session_to_file, load_session_from_file
        
        # Setup session state
        st.session_state.update({
            'session_id': 'test_session',
            'messages': [
                {'role': 'user', 'content': 'Hello', 'timestamp': datetime.now()}
            ],
            'session_start': datetime.now(),
            'last_activity': datetime.now()
        })
        
        # Save session
        success = save_session_to_file()
        assert success is True
        
        # Clear session state
        st.session_state.clear()
        
        # Load session
        success = load_session_from_file('test_session')
        assert success is True
        assert st.session_state.session_id == 'test_session'
        assert len(st.session_state.messages) == 1

class TestUIIntegration:
    """Test UI integration with backend services"""
    
    @patch('streamlit_ui.app.st')
    def test_app_initialization(self, mock_st, mock_streamlit, temp_workspace, sample_config):
        """Test main app initialization"""
        # Mock all required services
        mock_llm_service = Mock()
        mock_memory_manager = Mock()
        mock_graph_builder = Mock()
        
        with patch('services.llm_gateway.LLMService', return_value=mock_llm_service), \
             patch('core.memory.manager.MemoryManager', return_value=mock_memory_manager), \
             patch('core.graph.builder.SafeClawGraphBuilder', return_value=mock_graph_builder):
            
            from streamlit_ui.app import main
            
            main()
            
            # Verify initialization
            assert 'session_id' in st.session_state
            assert 'messages' in st.session_state
            assert 'safe_claw_config' in st.session_state
            assert 'llm_service' in st.session_state
            assert 'memory_manager' in st.session_state
            assert 'graph_builder' in st.session_state
    
    @patch('streamlit_ui.app.st')
    def test_sidebar_navigation(self, mock_st, mock_streamlit, temp_workspace, sample_config):
        """Test sidebar navigation"""
        # Mock sidebar elements
        mock_st.sidebar.title.return_value = None
        mock_st.sidebar.caption.return_value = None
        mock_st.sidebar.markdown.return_value = None
        mock_st.sidebar.subheader.return_value = None
        mock_st.sidebar.selectbox.return_value = "💬 Chat"
        mock_st.sidebar.button.side_effect = lambda x: None
        
        # Setup session state
        st.session_state.update({
            'session_id': 'test_session',
            'messages': [],
            'safe_claw_config': sample_config,
            'workspace_path': temp_workspace,
            'llm_service': Mock(),
            'memory_manager': Mock(),
            'graph_builder': Mock()
        })
        
        with patch('streamlit_ui.app.load_custom_css'):
            from streamlit_ui.app import main
            
            main()
            
            # Verify sidebar elements
            mock_st.sidebar.title.assert_called()
            mock_st.sidebar.selectbox.assert_called()
    
    @patch('streamlit_ui.app.st')
    def test_error_handling_in_ui(self, mock_st, mock_streamlit, temp_workspace):
        """Test error handling in UI"""
        # Mock failing service initialization
        with patch('services.llm_gateway.LLMService', side_effect=Exception("Service error")):
            
            from streamlit_ui.app import main
            
            main()
            
            # Should handle error gracefully
            mock_st.error.assert_called()

class TestUIComponents:
    """Test individual UI components"""
    
    @patch('streamlit_ui.components.chat_message.st')
    def test_chat_message_component(self, mock_st, mock_streamlit):
        """Test chat message component"""
        from streamlit_ui.components.chat_message import render_message, render_error_message, render_confirmation_prompt
        
        # Test normal message
        message = {
            "role": "user",
            "content": "Hello",
            "timestamp": datetime.now()
        }
        
        render_message(message)
        mock_st.chat_message.assert_called_with("user")
        
        # Test error message
        render_error_message("Error occurred", datetime.now())
        mock_st.chat_message.assert_called_with("assistant", avatar="❌")
        
        # Test confirmation prompt
        def callback(response):
            return response
        
        with patch('streamlit_ui.components.chat_message.st.columns') as mock_columns:
            mock_col1 = Mock()
            mock_col2 = Mock()
            mock_col1.button.return_value = False
            mock_col2.button.return_value = False
            mock_columns.return_value = [mock_col1, mock_col2]
            
            result = render_confirmation_prompt("Are you sure?", callback)
            assert result is None  # No button clicked
    
    @patch('streamlit_ui.components.memory_browser.st')
    def test_memory_browser_component(self, mock_st, mock_streamlit):
        """Test memory browser component"""
        from streamlit_ui.components.memory_browser import render_memory_browser
        
        # Mock memory manager
        mock_memory_manager = Mock()
        mock_memory_manager.get_memory_stats.return_value = {
            'active_count': 5,
            'dormant_count': 3,
            'deep_count': 2,
            'forgotten_count': 1
        }
        
        render_memory_browser(mock_memory_manager)
        
        # Verify browser elements
        mock_st.subheader.assert_called()
        mock_st.metric.assert_called()
    
    @patch('streamlit_ui.components.session_manager.st')
    def test_session_manager_component(self, mock_st, mock_streamlit, temp_workspace):
        """Test session manager component"""
        from streamlit_ui.components.session_manager import SessionManager
        
        manager = SessionManager(temp_workspace)
        
        # Test session creation
        session = manager.create_session()
        
        assert session.id is not None
        assert session.user_id == "default"
        
        # Test session listing
        sessions = manager.list_sessions()
        assert len(sessions) >= 1
        assert session.id in [s.id for s in sessions]
