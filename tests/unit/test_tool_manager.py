"""
Unit tests for tool_manager.py
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from tool_manager import (
    ensure_platform_tools, 
    get_attached_tools,
    BLUESKY_TOOLS, 
    X_TOOLS, 
    COMMON_TOOLS
)


class TestToolManager:
    """Test cases for tool_manager module."""
    
    @patch('tool_manager.get_letta_config')
    @patch('tool_manager.get_agent_config')
    @patch('tool_manager.Letta')
    def test_ensure_platform_tools_bluesky(self, mock_letta_class, mock_get_agent_config, mock_get_letta_config):
        """Test ensuring Bluesky platform tools."""
        # Setup mocks
        mock_get_letta_config.return_value = {
            'api_key': 'test-api-key',
            'agent_id': 'test-agent-id',
            'base_url': None
        }
        mock_get_agent_config.return_value = {
            'id': 'test-agent-id',
            'name': 'test-agent'
        }
        
        mock_client = Mock()
        mock_letta_class.return_value = mock_client
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.id = 'test-agent-id'
        mock_agent.name = 'test-agent'
        mock_client.agents.retrieve.return_value = mock_agent
        
        # Mock current tools (mix of platforms)
        mock_current_tools = [
            Mock(name='search_bluesky_posts', id='tool1'),
            Mock(name='add_post_to_x_thread', id='tool2'),  # Should be detached
            Mock(name='halt_activity', id='tool3'),  # Common tool, should stay
            Mock(name='create_new_bluesky_post', id='tool4'),
        ]
        mock_client.agents.tools.list.return_value = mock_current_tools
        
        # Test the function
        ensure_platform_tools('bluesky')
        
        # Verify agent was retrieved
        mock_client.agents.retrieve.assert_called_once_with(agent_id='test-agent-id')
        
        # Verify tools were listed
        mock_client.agents.tools.list.assert_called_once_with(agent_id='test-agent-id')
        
        # Verify X tool was detached
        mock_client.agents.tools.detach.assert_called_once_with(
            agent_id='test-agent-id',
            tool_id='tool2'
        )
    
    @patch('tool_manager.get_letta_config')
    @patch('tool_manager.get_agent_config')
    @patch('tool_manager.Letta')
    def test_ensure_platform_tools_x(self, mock_letta_class, mock_get_agent_config, mock_get_letta_config):
        """Test ensuring X platform tools."""
        # Setup mocks
        mock_get_letta_config.return_value = {
            'api_key': 'test-api-key',
            'agent_id': 'test-agent-id',
            'base_url': None
        }
        mock_get_agent_config.return_value = {
            'id': 'test-agent-id',
            'name': 'test-agent'
        }
        
        mock_client = Mock()
        mock_letta_class.return_value = mock_client
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.id = 'test-agent-id'
        mock_agent.name = 'test-agent'
        mock_client.agents.retrieve.return_value = mock_agent
        
        # Mock current tools (mix of platforms)
        mock_current_tools = [
            Mock(name='search_bluesky_posts', id='tool1'),  # Should be detached
            Mock(name='add_post_to_x_thread', id='tool2'),
            Mock(name='halt_activity', id='tool3'),  # Common tool, should stay
            Mock(name='search_x_posts', id='tool4'),
        ]
        mock_client.agents.tools.list.return_value = mock_current_tools
        
        # Test the function
        ensure_platform_tools('x')
        
        # Verify agent was retrieved
        mock_client.agents.retrieve.assert_called_once_with(agent_id='test-agent-id')
        
        # Verify tools were listed
        mock_client.agents.tools.list.assert_called_once_with(agent_id='test-agent-id')
        
        # Verify Bluesky tool was detached
        mock_client.agents.tools.detach.assert_called_once_with(
            agent_id='test-agent-id',
            tool_id='tool1'
        )
    
    def test_ensure_platform_tools_invalid_platform(self):
        """Test ensuring tools with invalid platform."""
        with pytest.raises(ValueError, match="Platform must be 'bluesky' or 'x'"):
            ensure_platform_tools('invalid_platform')
    
    @patch('tool_manager.get_letta_config')
    @patch('tool_manager.get_agent_config')
    @patch('tool_manager.Letta')
    def test_ensure_platform_tools_with_custom_params(self, mock_letta_class, mock_get_agent_config, mock_get_letta_config):
        """Test ensuring tools with custom agent_id and api_key."""
        # Setup mocks
        mock_get_letta_config.return_value = {
            'api_key': 'config-api-key',
            'agent_id': 'config-agent-id',
            'base_url': None
        }
        mock_get_agent_config.return_value = {
            'id': 'config-agent-id',
            'name': 'config-agent'
        }
        
        mock_client = Mock()
        mock_letta_class.return_value = mock_client
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.id = 'custom-agent-id'
        mock_agent.name = 'custom-agent'
        mock_client.agents.retrieve.return_value = mock_agent
        
        # Mock current tools
        mock_current_tools = []
        mock_client.agents.tools.list.return_value = mock_current_tools
        
        # Test with custom parameters
        ensure_platform_tools('bluesky', agent_id='custom-agent-id', api_key='custom-api-key')
        
        # Verify Letta client was created with custom API key
        mock_letta_class.assert_called_once_with(token='custom-api-key')
        
        # Verify agent was retrieved with custom ID
        mock_client.agents.retrieve.assert_called_once_with(agent_id='custom-agent-id')
    
    @patch('tool_manager.get_letta_config')
    @patch('tool_manager.get_agent_config')
    @patch('tool_manager.Letta')
    def test_ensure_platform_tools_with_base_url(self, mock_letta_class, mock_get_agent_config, mock_get_letta_config):
        """Test ensuring tools with custom base_url."""
        # Setup mocks
        mock_get_letta_config.return_value = {
            'api_key': 'test-api-key',
            'agent_id': 'test-agent-id',
            'base_url': 'https://custom.letta.com'
        }
        mock_get_agent_config.return_value = {
            'id': 'test-agent-id',
            'name': 'test-agent'
        }
        
        mock_client = Mock()
        mock_letta_class.return_value = mock_client
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.id = 'test-agent-id'
        mock_agent.name = 'test-agent'
        mock_client.agents.retrieve.return_value = mock_agent
        
        # Mock current tools
        mock_current_tools = []
        mock_client.agents.tools.list.return_value = mock_current_tools
        
        # Test the function
        ensure_platform_tools('bluesky')
        
        # Verify Letta client was created with base_url
        mock_letta_class.assert_called_once_with(
            token='test-api-key',
            base_url='https://custom.letta.com'
        )
    
    @patch('tool_manager.get_letta_config')
    @patch('tool_manager.get_agent_config')
    @patch('tool_manager.Letta')
    def test_ensure_platform_tools_agent_not_found(self, mock_letta_class, mock_get_agent_config, mock_get_letta_config):
        """Test handling when agent is not found."""
        # Setup mocks
        mock_get_letta_config.return_value = {
            'api_key': 'test-api-key',
            'agent_id': 'nonexistent-agent-id',
            'base_url': None
        }
        mock_get_agent_config.return_value = {
            'id': 'nonexistent-agent-id',
            'name': 'nonexistent-agent'
        }
        
        mock_client = Mock()
        mock_letta_class.return_value = mock_client
        
        # Mock agent retrieval failure
        mock_client.agents.retrieve.side_effect = Exception("Agent not found")
        
        # Test the function (should not raise exception)
        ensure_platform_tools('bluesky')
        
        # Verify agent retrieval was attempted
        mock_client.agents.retrieve.assert_called_once_with(agent_id='nonexistent-agent-id')
        
        # Verify no other operations were performed
        mock_client.agents.tools.list.assert_not_called()
    
    @patch('tool_manager.get_letta_config')
    @patch('tool_manager.get_agent_config')
    @patch('tool_manager.Letta')
    def test_ensure_platform_tools_detach_failure(self, mock_letta_class, mock_get_agent_config, mock_get_letta_config):
        """Test handling when tool detachment fails."""
        # Setup mocks
        mock_get_letta_config.return_value = {
            'api_key': 'test-api-key',
            'agent_id': 'test-agent-id',
            'base_url': None
        }
        mock_get_agent_config.return_value = {
            'id': 'test-agent-id',
            'name': 'test-agent'
        }
        
        mock_client = Mock()
        mock_letta_class.return_value = mock_client
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.id = 'test-agent-id'
        mock_agent.name = 'test-agent'
        mock_client.agents.retrieve.return_value = mock_agent
        
        # Mock current tools with X tool that should be detached
        mock_current_tools = [
            Mock(name='add_post_to_x_thread', id='tool1'),
        ]
        mock_client.agents.tools.list.return_value = mock_current_tools
        
        # Mock detachment failure
        mock_client.agents.tools.detach.side_effect = Exception("Detach failed")
        
        # Test the function (should not raise exception)
        ensure_platform_tools('bluesky')
        
        # Verify detachment was attempted
        mock_client.agents.tools.detach.assert_called_once_with(
            agent_id='test-agent-id',
            tool_id='tool1'
        )
    
    @patch('tool_manager.get_letta_config')
    @patch('tool_manager.get_agent_config')
    @patch('tool_manager.Letta')
    def test_get_attached_tools_success(self, mock_letta_class, mock_get_agent_config, mock_get_letta_config):
        """Test getting attached tools successfully."""
        # Setup mocks
        mock_get_letta_config.return_value = {
            'api_key': 'test-api-key',
            'agent_id': 'test-agent-id',
            'base_url': None
        }
        mock_get_agent_config.return_value = {
            'id': 'test-agent-id',
            'name': 'test-agent'
        }
        
        mock_client = Mock()
        mock_letta_class.return_value = mock_client
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.id = 'test-agent-id'
        mock_agent.name = 'test-agent'
        mock_client.agents.retrieve.return_value = mock_agent
        
        # Mock current tools
        mock_current_tools = [
            Mock(name='search_bluesky_posts'),
            Mock(name='halt_activity'),
            Mock(name='add_post_to_x_thread'),
        ]
        mock_client.agents.tools.list.return_value = mock_current_tools
        
        # Test the function
        result = get_attached_tools()
        
        # Verify result
        expected_tools = {'search_bluesky_posts', 'halt_activity', 'add_post_to_x_thread'}
        assert result == expected_tools
        
        # Verify calls
        mock_client.agents.retrieve.assert_called_once_with(agent_id='test-agent-id')
        mock_client.agents.tools.list.assert_called_once_with(agent_id='test-agent-id')
    
    @patch('tool_manager.get_letta_config')
    @patch('tool_manager.get_agent_config')
    @patch('tool_manager.Letta')
    def test_get_attached_tools_with_custom_params(self, mock_letta_class, mock_get_agent_config, mock_get_letta_config):
        """Test getting attached tools with custom parameters."""
        # Setup mocks
        mock_get_letta_config.return_value = {
            'api_key': 'config-api-key',
            'agent_id': 'config-agent-id',
            'base_url': None
        }
        mock_get_agent_config.return_value = {
            'id': 'config-agent-id',
            'name': 'config-agent'
        }
        
        mock_client = Mock()
        mock_letta_class.return_value = mock_client
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.id = 'custom-agent-id'
        mock_agent.name = 'custom-agent'
        mock_client.agents.retrieve.return_value = mock_agent
        
        # Mock current tools
        mock_current_tools = []
        mock_client.agents.tools.list.return_value = mock_current_tools
        
        # Test with custom parameters
        result = get_attached_tools(agent_id='custom-agent-id', api_key='custom-api-key')
        
        # Verify result
        assert result == set()
        
        # Verify Letta client was created with custom API key
        mock_letta_class.assert_called_once_with(token='custom-api-key')
        
        # Verify agent was retrieved with custom ID
        mock_client.agents.retrieve.assert_called_once_with(agent_id='custom-agent-id')
    
    @patch('tool_manager.get_letta_config')
    @patch('tool_manager.get_agent_config')
    @patch('tool_manager.Letta')
    def test_get_attached_tools_error(self, mock_letta_class, mock_get_agent_config, mock_get_letta_config):
        """Test handling errors when getting attached tools."""
        # Setup mocks
        mock_get_letta_config.return_value = {
            'api_key': 'test-api-key',
            'agent_id': 'test-agent-id',
            'base_url': None
        }
        mock_get_agent_config.return_value = {
            'id': 'test-agent-id',
            'name': 'test-agent'
        }
        
        mock_client = Mock()
        mock_letta_class.return_value = mock_client
        
        # Mock error
        mock_client.agents.retrieve.side_effect = Exception("API error")
        
        # Test the function
        result = get_attached_tools()
        
        # Verify result is empty set on error
        assert result == set()
    
    def test_tool_sets_definition(self):
        """Test that tool sets are properly defined."""
        # Test Bluesky tools
        assert 'search_bluesky_posts' in BLUESKY_TOOLS
        assert 'create_new_bluesky_post' in BLUESKY_TOOLS
        assert 'add_post_to_bluesky_reply_thread' in BLUESKY_TOOLS
        
        # Test X tools
        assert 'add_post_to_x_thread' in X_TOOLS
        assert 'search_x_posts' in X_TOOLS
        
        # Test common tools
        assert 'halt_activity' in COMMON_TOOLS
        assert 'ignore_notification' in COMMON_TOOLS
        
        # Test no overlap between platform-specific tools
        assert BLUESKY_TOOLS.isdisjoint(X_TOOLS)
        
        # Test common tools are separate
        assert COMMON_TOOLS.isdisjoint(BLUESKY_TOOLS)
        assert COMMON_TOOLS.isdisjoint(X_TOOLS)
    
    @patch('tool_manager.get_letta_config')
    @patch('tool_manager.get_agent_config')
    @patch('tool_manager.Letta')
    def test_ensure_platform_tools_missing_tools_logging(self, mock_letta_class, mock_get_agent_config, mock_get_letta_config, caplog):
        """Test logging when required tools are missing."""
        # Setup mocks
        mock_get_letta_config.return_value = {
            'api_key': 'test-api-key',
            'agent_id': 'test-agent-id',
            'base_url': None
        }
        mock_get_agent_config.return_value = {
            'id': 'test-agent-id',
            'name': 'test-agent'
        }
        
        mock_client = Mock()
        mock_letta_class.return_value = mock_client
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.id = 'test-agent-id'
        mock_agent.name = 'test-agent'
        mock_client.agents.retrieve.return_value = mock_agent
        
        # Mock current tools with only common tools (missing Bluesky tools)
        mock_current_tools = [
            Mock(name='halt_activity'),
        ]
        mock_client.agents.tools.list.return_value = mock_current_tools
        
        # Test the function
        with caplog.at_level('INFO'):
            ensure_platform_tools('bluesky')
        
        # Verify logging about missing tools
        assert "Missing" in caplog.text
        assert "bluesky tools" in caplog.text.lower()
        assert "register_tools.py" in caplog.text
    
    @patch('tool_manager.get_letta_config')
    @patch('tool_manager.get_agent_config')
    @patch('tool_manager.Letta')
    def test_ensure_platform_tools_all_tools_present_logging(self, mock_letta_class, mock_get_agent_config, mock_get_letta_config, caplog):
        """Test logging when all required tools are present."""
        # Setup mocks
        mock_get_letta_config.return_value = {
            'api_key': 'test-api-key',
            'agent_id': 'test-agent-id',
            'base_url': None
        }
        mock_get_agent_config.return_value = {
            'id': 'test-agent-id',
            'name': 'test-agent'
        }
        
        mock_client = Mock()
        mock_letta_class.return_value = mock_client
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.id = 'test-agent-id'
        mock_agent.name = 'test-agent'
        mock_client.agents.retrieve.return_value = mock_agent
        
        # Mock current tools with all Bluesky tools present
        mock_current_tools = [
            Mock(name='search_bluesky_posts'),
            Mock(name='create_new_bluesky_post'),
            Mock(name='halt_activity'),  # Common tool
        ]
        mock_client.agents.tools.list.return_value = mock_current_tools
        
        # Test the function
        with caplog.at_level('INFO'):
            ensure_platform_tools('bluesky')
        
        # Verify logging about all tools present
        assert "All required bluesky tools are already attached" in caplog.text


class TestToolManagerCLI:
    """Test cases for tool_manager CLI functionality."""
    
    @patch('tool_manager.get_attached_tools')
    def test_cli_list_tools(self, mock_get_attached_tools):
        """Test CLI list functionality."""
        # Mock attached tools
        mock_get_attached_tools.return_value = {
            'search_bluesky_posts',
            'add_post_to_x_thread',
            'halt_activity'
        }
        
        # Test CLI list command
        import sys
        from io import StringIO
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            # Simulate CLI call
            import tool_manager
            sys.argv = ['tool_manager.py', '--list']
            tool_manager.main()
        except SystemExit:
            pass
        finally:
            sys.stdout = old_stdout
        
        output = captured_output.getvalue()
        
        # Verify output contains tool names
        assert 'search_bluesky_posts' in output
        assert 'add_post_to_x_thread' in output
        assert 'halt_activity' in output
        
        # Verify platform indicators
        assert '[Bluesky]' in output
        assert '[X]' in output
        assert '[Common]' in output
    
    @patch('tool_manager.ensure_platform_tools')
    def test_cli_ensure_bluesky_tools(self, mock_ensure_platform_tools):
        """Test CLI ensure Bluesky tools functionality."""
        import sys
        
        try:
            # Simulate CLI call
            import tool_manager
            sys.argv = ['tool_manager.py', 'bluesky']
            tool_manager.main()
        except SystemExit:
            pass
        
        # Verify function was called
        mock_ensure_platform_tools.assert_called_once_with('bluesky', None)
    
    @patch('tool_manager.ensure_platform_tools')
    def test_cli_ensure_x_tools_with_agent_id(self, mock_ensure_platform_tools):
        """Test CLI ensure X tools with custom agent ID."""
        import sys
        
        try:
            # Simulate CLI call
            import tool_manager
            sys.argv = ['tool_manager.py', 'x', '--agent-id', 'custom-agent-id']
            tool_manager.main()
        except SystemExit:
            pass
        
        # Verify function was called with custom agent ID
        mock_ensure_platform_tools.assert_called_once_with('x', 'custom-agent-id')
    
    def test_cli_no_platform_error(self):
        """Test CLI error when no platform is specified."""
        import sys
        from io import StringIO
        
        # Capture stderr
        old_stderr = sys.stderr
        sys.stderr = captured_output = StringIO()
        
        try:
            # Simulate CLI call without platform
            import tool_manager
            sys.argv = ['tool_manager.py']
            tool_manager.main()
        except SystemExit:
            pass
        finally:
            sys.stderr = old_stderr
        
        output = captured_output.getvalue()
        
        # Verify error message
        assert "platform is required" in output
