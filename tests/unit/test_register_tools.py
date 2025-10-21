"""
Unit tests for register_tools.py
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from io import StringIO

# Mock the config loading before importing register_tools
with patch('register_tools.get_letta_config') as mock_config:
    mock_config.return_value = {
        'api_key': 'test-api-key',
        'agent_id': 'test-agent-id',
        'base_url': None
    }
    from register_tools import (
        register_tools_with_agent,
        get_tool_definitions,
        TOOL_CONFIGS,
        main
    )


class TestRegisterTools:
    """Test cases for register_tools module."""
    
    @patch('register_tools.get_letta_config')
    @patch('register_tools.Letta')
    def test_register_tools_with_agent_success(self, mock_letta_class, mock_get_letta_config):
        """Test successful tool registration with agent."""
        # Setup mocks
        mock_get_letta_config.return_value = {
            'api_key': 'test-api-key',
            'agent_id': 'test-agent-id',
            'base_url': None
        }
        
        mock_client = Mock()
        mock_letta_class.return_value = mock_client
        
        # Mock tool creation
        mock_tool = Mock()
        mock_tool.id = 'tool-id'
        mock_tool.name = 'test_tool'
        mock_client.tools.create.return_value = mock_tool
        
        # Mock agent tool attachment
        mock_client.agents.tools.attach.return_value = Mock()
        
        # Test the function
        result = register_tools_with_agent('test-agent-id', 'test-api-key')
        
        # Verify result
        assert result > 0  # Should return number of tools registered
        
        # Verify Letta client was created
        mock_letta_class.assert_called_once_with(token='test-api-key')
        
        # Verify tools were created and attached
        assert mock_client.tools.create.call_count > 0
        assert mock_client.agents.tools.attach.call_count > 0
    
    @patch('register_tools.get_letta_config')
    @patch('register_tools.Letta')
    def test_register_tools_with_agent_with_base_url(self, mock_letta_class, mock_get_letta_config):
        """Test tool registration with custom base URL."""
        # Setup mocks
        mock_get_letta_config.return_value = {
            'api_key': 'test-api-key',
            'agent_id': 'test-agent-id',
            'base_url': 'https://custom.letta.com'
        }
        
        mock_client = Mock()
        mock_letta_class.return_value = mock_client
        
        # Mock tool creation
        mock_tool = Mock()
        mock_tool.id = 'tool-id'
        mock_tool.name = 'test_tool'
        mock_client.tools.create.return_value = mock_tool
        
        # Mock agent tool attachment
        mock_client.agents.tools.attach.return_value = Mock()
        
        # Test the function
        register_tools_with_agent('test-agent-id', 'test-api-key')
        
        # Verify Letta client was created with base URL
        mock_letta_class.assert_called_once_with(
            token='test-api-key',
            base_url='https://custom.letta.com'
        )
    
    @patch('register_tools.get_letta_config')
    @patch('register_tools.Letta')
    def test_register_tools_with_agent_tool_creation_failure(self, mock_letta_class, mock_get_letta_config):
        """Test handling tool creation failure."""
        # Setup mocks
        mock_get_letta_config.return_value = {
            'api_key': 'test-api-key',
            'agent_id': 'test-agent-id',
            'base_url': None
        }
        
        mock_client = Mock()
        mock_letta_class.return_value = mock_client
        
        # Mock tool creation failure
        mock_client.tools.create.side_effect = Exception("Tool creation failed")
        
        # Test the function
        result = register_tools_with_agent('test-agent-id', 'test-api-key')
        
        # Verify result is 0 (no tools registered)
        assert result == 0
    
    @patch('register_tools.get_letta_config')
    @patch('register_tools.Letta')
    def test_register_tools_with_agent_attachment_failure(self, mock_letta_class, mock_get_letta_config):
        """Test handling tool attachment failure."""
        # Setup mocks
        mock_get_letta_config.return_value = {
            'api_key': 'test-api-key',
            'agent_id': 'test-agent-id',
            'base_url': None
        }
        
        mock_client = Mock()
        mock_letta_class.return_value = mock_client
        
        # Mock tool creation success
        mock_tool = Mock()
        mock_tool.id = 'tool-id'
        mock_tool.name = 'test_tool'
        mock_client.tools.create.return_value = mock_tool
        
        # Mock agent tool attachment failure
        mock_client.agents.tools.attach.side_effect = Exception("Attachment failed")
        
        # Test the function
        result = register_tools_with_agent('test-agent-id', 'test-api-key')
        
        # Verify result is 0 (no tools successfully attached)
        assert result == 0
    
    def test_get_tool_definitions(self):
        """Test getting tool definitions."""
        # Test that TOOL_CONFIGS is properly defined
        assert isinstance(TOOL_CONFIGS, list)
        assert len(TOOL_CONFIGS) > 0
        
        # Test that each tool config has required fields
        for tool_config in TOOL_CONFIGS:
            assert 'func' in tool_config
            assert 'args_schema' in tool_config
            assert 'description' in tool_config
            assert 'tags' in tool_config
            
            # Test that func is callable
            assert callable(tool_config['func'])
            
            # Test that args_schema is a class
            assert isinstance(tool_config['args_schema'], type)
            
            # Test that description is a string
            assert isinstance(tool_config['description'], str)
            
            # Test that tags is a list
            assert isinstance(tool_config['tags'], list)
    
    @patch('register_tools.register_tools_with_agent')
    @patch('register_tools.get_letta_config')
    def test_main_function_success(self, mock_get_letta_config, mock_register_tools):
        """Test main function execution."""
        # Setup mocks
        mock_get_letta_config.return_value = {
            'api_key': 'test-api-key',
            'agent_id': 'test-agent-id',
            'base_url': None
        }
        mock_register_tools.return_value = 5
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            # Test main function
            main()
        finally:
            sys.stdout = old_stdout
        
        output = captured_output.getvalue()
        
        # Verify registration was called
        mock_register_tools.assert_called_once_with('test-agent-id', 'test-api-key')
        
        # Verify output contains success message
        assert "Successfully registered" in output
        assert "5" in output  # Number of tools registered
    
    @patch('register_tools.register_tools_with_agent')
    @patch('register_tools.get_letta_config')
    def test_main_function_no_tools_registered(self, mock_get_letta_config, mock_register_tools):
        """Test main function when no tools are registered."""
        # Setup mocks
        mock_get_letta_config.return_value = {
            'api_key': 'test-api-key',
            'agent_id': 'test-agent-id',
            'base_url': None
        }
        mock_register_tools.return_value = 0
        
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            # Test main function
            main()
        finally:
            sys.stdout = old_stdout
        
        output = captured_output.getvalue()
        
        # Verify registration was called
        mock_register_tools.assert_called_once_with('test-agent-id', 'test-api-key')
        
        # Verify output contains no tools message
        assert "No tools were registered" in output
    
    @patch('register_tools.register_tools_with_agent')
    @patch('register_tools.get_letta_config')
    def test_main_function_registration_error(self, mock_get_letta_config, mock_register_tools):
        """Test main function when registration fails."""
        # Setup mocks
        mock_get_letta_config.return_value = {
            'api_key': 'test-api-key',
            'agent_id': 'test-agent-id',
            'base_url': None
        }
        mock_register_tools.side_effect = Exception("Registration failed")
        
        # Capture stderr
        old_stderr = sys.stderr
        sys.stderr = captured_output = StringIO()
        
        try:
            # Test main function
            main()
        except SystemExit:
            pass
        finally:
            sys.stderr = old_stderr
        
        output = captured_output.getvalue()
        
        # Verify registration was called
        mock_register_tools.assert_called_once_with('test-agent-id', 'test-api-key')
        
        # Verify error is handled
        assert "Registration failed" in output
    
    def test_tool_configs_structure(self):
        """Test that tool configurations have proper structure."""
        # Test that we have expected tools
        tool_names = [config['func'].__name__ for config in TOOL_CONFIGS]
        
        # Test for some expected Bluesky tools
        expected_tools = [
            'search_bluesky_posts',
            'create_new_bluesky_post',
            'get_bluesky_feed',
            'add_post_to_bluesky_reply_thread',
            'halt_activity',
            'ignore_notification',
            'create_whitewind_blog_post',
            'annotate_ack',
            'fetch_webpage'
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Expected tool {expected_tool} not found in TOOL_CONFIGS"
    
    def test_tool_configs_tags(self):
        """Test that tool configurations have proper tags."""
        for tool_config in TOOL_CONFIGS:
            tags = tool_config['tags']
            
            # Test that tags is not empty
            assert len(tags) > 0, f"Tool {tool_config['func'].__name__} has no tags"
            
            # Test that tags are strings
            for tag in tags:
                assert isinstance(tag, str), f"Tag {tag} is not a string"
                assert len(tag) > 0, f"Empty tag found for tool {tool_config['func'].__name__}"
    
    def test_tool_configs_descriptions(self):
        """Test that tool configurations have proper descriptions."""
        for tool_config in TOOL_CONFIGS:
            description = tool_config['description']
            
            # Test that description is not empty
            assert len(description) > 0, f"Tool {tool_config['func'].__name__} has no description"
            
            # Test that description is meaningful (at least 10 characters)
            assert len(description) >= 10, f"Tool {tool_config['func'].__name__} has too short description"
    
    @patch('register_tools.get_letta_config')
    def test_get_letta_config_called(self, mock_get_letta_config):
        """Test that get_letta_config is called during module import."""
        # Reset the mock
        mock_get_letta_config.reset_mock()
        
        # Re-import the module to trigger the config call
        import importlib
        import register_tools
        importlib.reload(register_tools)
        
        # Verify get_letta_config was called
        mock_get_letta_config.assert_called()
    
    def test_tool_configs_unique_names(self):
        """Test that tool configurations have unique function names."""
        tool_names = [config['func'].__name__ for config in TOOL_CONFIGS]
        
        # Test that all names are unique
        assert len(tool_names) == len(set(tool_names)), "Duplicate tool names found in TOOL_CONFIGS"
    
    def test_tool_configs_schema_compatibility(self):
        """Test that tool configurations have compatible schemas."""
        for tool_config in TOOL_CONFIGS:
            func = tool_config['func']
            args_schema = tool_config['args_schema']
            
            # Test that args_schema is a Pydantic model
            assert hasattr(args_schema, '__fields__') or hasattr(args_schema, 'model_fields'), \
                f"Tool {func.__name__} args_schema is not a Pydantic model"
    
    @patch('register_tools.Letta')
    def test_register_tools_with_agent_empty_configs(self, mock_letta_class):
        """Test registration with empty tool configs."""
        # Mock empty TOOL_CONFIGS
        with patch('register_tools.TOOL_CONFIGS', []):
            mock_client = Mock()
            mock_letta_class.return_value = mock_client
            
            result = register_tools_with_agent('test-agent-id', 'test-api-key')
            
            # Should return 0 when no tools to register
            assert result == 0
            
            # Should not create any tools
            mock_client.tools.create.assert_not_called()
            mock_client.agents.tools.attach.assert_not_called()
