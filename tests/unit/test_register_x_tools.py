"""
Comprehensive unit tests for register_x_tools.py - X tool registration module.

This module tests:
1. X tool registration functionality
2. Tool configuration and validation
3. Error handling and recovery
4. Tool listing and management
5. Integration with Letta client
6. Tool attachment and detachment
"""

import pytest
from unittest.mock import patch, MagicMock
from typing import List

# Import the module under test
import register_x_tools
from register_x_tools import (
    register_x_tools,
    list_available_x_tools,
    X_TOOL_CONFIGS
)


class TestXToolRegistration:
    """Test X tool registration functionality."""
    
    @patch('register_x_tools.get_x_letta_config')
    @patch('register_x_tools.Letta')
    def test_register_x_tools_success(self, mock_letta_class, mock_get_config):
        """Test successful X tool registration."""
        # Setup mocks
        mock_config = {
            'api_key': 'test_letta_key',
            'agent_id': 'test_agent_id',
            'timeout': 30
        }
        mock_get_config.return_value = mock_config
        
        mock_client = MagicMock()
        mock_letta_class.return_value = mock_client
        
        mock_agent = MagicMock()
        mock_agent.id = 'test_agent_id'
        mock_agent.name = 'Test Agent'
        mock_client.agents.retrieve.return_value = mock_agent
        
        mock_tool = MagicMock()
        mock_tool.id = 'test_tool_id'
        mock_tool.name = 'test_tool'
        mock_client.tools.upsert_from_function.return_value = mock_tool
        
        mock_current_tools = [MagicMock(name='existing_tool')]
        mock_client.agents.tools.list.return_value = mock_current_tools
        
        # Test registration
        register_x_tools()
        
        # Verify client initialization
        mock_letta_class.assert_called_once_with(token='test_letta_key', timeout=30)
        mock_client.agents.retrieve.assert_called_once_with(agent_id='test_agent_id')
        
        # Verify tool registration attempts
        assert mock_client.tools.upsert_from_function.call_count > 0
        assert mock_client.agents.tools.attach.call_count > 0
    
    @patch('register_x_tools.get_x_letta_config')
    @patch('register_x_tools.Letta')
    def test_register_x_tools_with_custom_agent_id(self, mock_letta_class, mock_get_config):
        """Test X tool registration with custom agent ID."""
        mock_config = {
            'api_key': 'test_letta_key',
            'agent_id': 'default_agent_id',
            'timeout': 30
        }
        mock_get_config.return_value = mock_config
        
        mock_client = MagicMock()
        mock_letta_class.return_value = mock_client
        
        mock_agent = MagicMock()
        mock_agent.id = 'custom_agent_id'
        mock_agent.name = 'Custom Agent'
        mock_client.agents.retrieve.return_value = mock_agent
        
        mock_tool = MagicMock()
        mock_tool.id = 'test_tool_id'
        mock_tool.name = 'test_tool'
        mock_client.tools.upsert_from_function.return_value = mock_tool
        
        mock_current_tools = []
        mock_client.agents.tools.list.return_value = mock_current_tools
        
        # Test registration with custom agent ID
        register_x_tools(agent_id='custom_agent_id')
        
        # Verify custom agent ID was used
        mock_client.agents.retrieve.assert_called_once_with(agent_id='custom_agent_id')
    
    @patch('register_x_tools.get_x_letta_config')
    @patch('register_x_tools.Letta')
    def test_register_x_tools_with_specific_tools(self, mock_letta_class, mock_get_config):
        """Test X tool registration with specific tools only."""
        mock_config = {
            'api_key': 'test_letta_key',
            'agent_id': 'test_agent_id',
            'timeout': 30
        }
        mock_get_config.return_value = mock_config
        
        mock_client = MagicMock()
        mock_letta_class.return_value = mock_client
        
        mock_agent = MagicMock()
        mock_agent.id = 'test_agent_id'
        mock_agent.name = 'Test Agent'
        mock_client.agents.retrieve.return_value = mock_agent
        
        mock_tool = MagicMock()
        mock_tool.id = 'test_tool_id'
        mock_tool.name = 'halt_activity'
        mock_client.tools.upsert_from_function.return_value = mock_tool
        
        mock_current_tools = []
        mock_client.agents.tools.list.return_value = mock_current_tools
        
        # Test registration with specific tools
        register_x_tools(tools=['halt_activity', 'ignore_notification'])
        
        # Verify only specific tools were registered
        assert mock_client.tools.upsert_from_function.call_count == 2
    
    @patch('register_x_tools.get_x_letta_config')
    @patch('register_x_tools.Letta')
    def test_register_x_tools_agent_not_found(self, mock_letta_class, mock_get_config):
        """Test X tool registration with non-existent agent."""
        mock_config = {
            'api_key': 'test_letta_key',
            'agent_id': 'nonexistent_agent_id',
            'timeout': 30
        }
        mock_get_config.return_value = mock_config
        
        mock_client = MagicMock()
        mock_letta_class.return_value = mock_client
        mock_client.agents.retrieve.side_effect = Exception("Agent not found")
        
        # Test registration with non-existent agent
        register_x_tools()
        
        # Verify error handling
        mock_client.agents.retrieve.assert_called_once_with(agent_id='nonexistent_agent_id')
    
    @patch('register_x_tools.get_x_letta_config')
    @patch('register_x_tools.Letta')
    def test_register_x_tools_tool_already_attached(self, mock_letta_class, mock_get_config):
        """Test X tool registration with already attached tools."""
        mock_config = {
            'api_key': 'test_letta_key',
            'agent_id': 'test_agent_id',
            'timeout': 30
        }
        mock_get_config.return_value = mock_config
        
        mock_client = MagicMock()
        mock_letta_class.return_value = mock_client
        
        mock_agent = MagicMock()
        mock_agent.id = 'test_agent_id'
        mock_agent.name = 'Test Agent'
        mock_client.agents.retrieve.return_value = mock_agent
        
        mock_tool = MagicMock()
        mock_tool.id = 'test_tool_id'
        mock_tool.name = 'halt_activity'
        mock_client.tools.upsert_from_function.return_value = mock_tool
        
        # Mock that tool is already attached
        mock_current_tools = [MagicMock(name='halt_activity')]
        mock_client.agents.tools.list.return_value = mock_current_tools
        
        # Test registration
        register_x_tools()
        
        # Verify tool was not attached again
        mock_client.agents.tools.attach.assert_not_called()
    
    @patch('register_x_tools.get_x_letta_config')
    @patch('register_x_tools.Letta')
    def test_register_x_tools_tool_registration_error(self, mock_letta_class, mock_get_config):
        """Test X tool registration with tool registration error."""
        mock_config = {
            'api_key': 'test_letta_key',
            'agent_id': 'test_agent_id',
            'timeout': 30
        }
        mock_get_config.return_value = mock_config
        
        mock_client = MagicMock()
        mock_letta_class.return_value = mock_client
        
        mock_agent = MagicMock()
        mock_agent.id = 'test_agent_id'
        mock_agent.name = 'Test Agent'
        mock_client.agents.retrieve.return_value = mock_agent
        
        # Mock tool registration error
        mock_client.tools.upsert_from_function.side_effect = Exception("Tool registration failed")
        
        # Test registration
        register_x_tools()
        
        # Verify error handling
        mock_client.tools.upsert_from_function.assert_called()
    
    @patch('register_x_tools.get_x_letta_config')
    def test_register_x_tools_config_error(self, mock_get_config):
        """Test X tool registration with configuration error."""
        mock_get_config.side_effect = Exception("Config error")
        
        # Test registration
        register_x_tools()
        
        # Verify error handling
        mock_get_config.assert_called_once()


class TestXToolConfiguration:
    """Test X tool configuration and validation."""
    
    def test_x_tool_configs_structure(self):
        """Test X tool configurations have proper structure."""
        assert isinstance(X_TOOL_CONFIGS, list)
        assert len(X_TOOL_CONFIGS) > 0
        
        for tool_config in X_TOOL_CONFIGS:
            assert 'func' in tool_config
            assert 'args_schema' in tool_config
            assert 'description' in tool_config
            assert 'tags' in tool_config
            
            # Verify required fields are not None
            assert tool_config['func'] is not None
            assert tool_config['args_schema'] is not None
            assert tool_config['description'] is not None
            assert isinstance(tool_config['tags'], list)
    
    def test_x_tool_configs_have_valid_functions(self):
        """Test X tool configurations have valid functions."""
        for tool_config in X_TOOL_CONFIGS:
            func = tool_config['func']
            assert hasattr(func, '__name__')
            assert hasattr(func, '__call__')
    
    def test_x_tool_configs_have_valid_schemas(self):
        """Test X tool configurations have valid argument schemas."""
        for tool_config in X_TOOL_CONFIGS:
            schema = tool_config['args_schema']
            assert hasattr(schema, '__name__')
            # Verify it's a Pydantic model or similar
            assert hasattr(schema, '__fields__') or hasattr(schema, 'model_fields')
    
    def test_x_tool_configs_have_descriptions(self):
        """Test X tool configurations have non-empty descriptions."""
        for tool_config in X_TOOL_CONFIGS:
            description = tool_config['description']
            assert isinstance(description, str)
            assert len(description.strip()) > 0
    
    def test_x_tool_configs_have_tags(self):
        """Test X tool configurations have non-empty tags."""
        for tool_config in X_TOOL_CONFIGS:
            tags = tool_config['tags']
            assert isinstance(tags, list)
            assert len(tags) > 0
            for tag in tags:
                assert isinstance(tag, str)
                assert len(tag.strip()) > 0


class TestXToolListing:
    """Test X tool listing functionality."""
    
    @patch('register_x_tools.console')
    def test_list_available_x_tools_success(self, mock_console):
        """Test successful X tool listing."""
        # Test listing
        list_available_x_tools()
        
        # Verify console was used
        mock_console.print.assert_called_once()
    
    def test_list_available_x_tools_structure(self):
        """Test X tool listing structure."""
        # This test verifies the function can be called without errors
        # The actual output is tested through console mocking
        try:
            list_available_x_tools()
        except Exception as e:
            pytest.fail(f"list_available_x_tools() raised an exception: {e}")


class TestXToolErrorHandling:
    """Test X tool error handling and edge cases."""
    
    @patch('register_x_tools.get_x_letta_config')
    @patch('register_x_tools.Letta')
    def test_register_x_tools_client_initialization_error(self, mock_letta_class, mock_get_config):
        """Test X tool registration with client initialization error."""
        mock_config = {
            'api_key': 'test_letta_key',
            'agent_id': 'test_agent_id',
            'timeout': 30
        }
        mock_get_config.return_value = mock_config
        mock_letta_class.side_effect = Exception("Client initialization failed")
        
        # Test registration
        register_x_tools()
        
        # Verify error handling
        mock_letta_class.assert_called_once()
    
    @patch('register_x_tools.get_x_letta_config')
    @patch('register_x_tools.Letta')
    def test_register_x_tools_tool_attachment_error(self, mock_letta_class, mock_get_config):
        """Test X tool registration with tool attachment error."""
        mock_config = {
            'api_key': 'test_letta_key',
            'agent_id': 'test_agent_id',
            'timeout': 30
        }
        mock_get_config.return_value = mock_config
        
        mock_client = MagicMock()
        mock_letta_class.return_value = mock_client
        
        mock_agent = MagicMock()
        mock_agent.id = 'test_agent_id'
        mock_agent.name = 'Test Agent'
        mock_client.agents.retrieve.return_value = mock_agent
        
        mock_tool = MagicMock()
        mock_tool.id = 'test_tool_id'
        mock_tool.name = 'test_tool'
        mock_client.tools.upsert_from_function.return_value = mock_tool
        
        mock_current_tools = []
        mock_client.agents.tools.list.return_value = mock_current_tools
        
        # Mock tool attachment error
        mock_client.agents.tools.attach.side_effect = Exception("Tool attachment failed")
        
        # Test registration
        register_x_tools()
        
        # Verify error handling
        mock_client.agents.tools.attach.assert_called()
    
    def test_register_x_tools_with_invalid_tool_names(self):
        """Test X tool registration with invalid tool names."""
        with patch('register_x_tools.get_x_letta_config') as mock_get_config:
            with patch('register_x_tools.Letta') as mock_letta_class:
                mock_config = {
                    'api_key': 'test_letta_key',
                    'agent_id': 'test_agent_id',
                    'timeout': 30
                }
                mock_get_config.return_value = mock_config
                
                mock_client = MagicMock()
                mock_letta_class.return_value = mock_client
                
                mock_agent = MagicMock()
                mock_agent.id = 'test_agent_id'
                mock_agent.name = 'Test Agent'
                mock_client.agents.retrieve.return_value = mock_agent
                
                # Test registration with invalid tool names
                register_x_tools(tools=['nonexistent_tool1', 'nonexistent_tool2'])
                
                # Verify no tools were registered
                mock_client.tools.upsert_from_function.assert_not_called()
    
    def test_register_x_tools_with_mixed_valid_invalid_tools(self):
        """Test X tool registration with mix of valid and invalid tool names."""
        with patch('register_x_tools.get_x_letta_config') as mock_get_config:
            with patch('register_x_tools.Letta') as mock_letta_class:
                mock_config = {
                    'api_key': 'test_letta_key',
                    'agent_id': 'test_agent_id',
                    'timeout': 30
                }
                mock_get_config.return_value = mock_config
                
                mock_client = MagicMock()
                mock_letta_class.return_value = mock_client
                
                mock_agent = MagicMock()
                mock_agent.id = 'test_agent_id'
                mock_agent.name = 'Test Agent'
                mock_client.agents.retrieve.return_value = mock_agent
                
                mock_tool = MagicMock()
                mock_tool.id = 'test_tool_id'
                mock_tool.name = 'halt_activity'
                mock_client.tools.upsert_from_function.return_value = mock_tool
                
                mock_current_tools = []
                mock_client.agents.tools.list.return_value = mock_current_tools
                
                # Test registration with mix of valid and invalid tools
                register_x_tools(tools=['halt_activity', 'nonexistent_tool'])
                
                # Verify only valid tools were registered
                mock_client.tools.upsert_from_function.assert_called_once()


class TestXToolIntegration:
    """Test X tool integration scenarios."""
    
    @patch('register_x_tools.get_x_letta_config')
    @patch('register_x_tools.Letta')
    def test_x_tool_registration_integration_workflow(self, mock_letta_class, mock_get_config):
        """Test complete X tool registration integration workflow."""
        # Setup mocks
        mock_config = {
            'api_key': 'test_letta_key',
            'agent_id': 'test_agent_id',
            'timeout': 30,
            'base_url': 'https://api.letta.ai'
        }
        mock_get_config.return_value = mock_config
        
        mock_client = MagicMock()
        mock_letta_class.return_value = mock_client
        
        mock_agent = MagicMock()
        mock_agent.id = 'test_agent_id'
        mock_agent.name = 'Test Agent'
        mock_client.agents.retrieve.return_value = mock_agent
        
        mock_tool = MagicMock()
        mock_tool.id = 'test_tool_id'
        mock_tool.name = 'halt_activity'
        mock_client.tools.upsert_from_function.return_value = mock_tool
        
        mock_current_tools = []
        mock_client.agents.tools.list.return_value = mock_current_tools
        
        # Test complete workflow
        register_x_tools()
        
        # Verify complete workflow
        mock_letta_class.assert_called_once_with(
            token='test_letta_key',
            timeout=30,
            base_url='https://api.letta.ai'
        )
        mock_client.agents.retrieve.assert_called_once_with(agent_id='test_agent_id')
        assert mock_client.tools.upsert_from_function.call_count > 0
        assert mock_client.agents.tools.attach.call_count > 0
    
    def test_x_tool_configuration_integration(self):
        """Test X tool configuration integration."""
        # Verify all tool configurations are properly structured
        for tool_config in X_TOOL_CONFIGS:
            # Test function can be called (basic validation)
            func = tool_config['func']
            assert callable(func)
            
            # Test schema can be instantiated (basic validation)
            schema = tool_config['args_schema']
            assert hasattr(schema, '__name__')
            
            # Test description is meaningful
            description = tool_config['description']
            assert len(description) > 10  # Reasonable minimum length
            
            # Test tags are relevant
            tags = tool_config['tags']
            assert len(tags) >= 1  # At least one tag
    
    def test_x_tool_registration_with_base_url(self):
        """Test X tool registration with base_url configuration."""
        with patch('register_x_tools.get_x_letta_config') as mock_get_config:
            with patch('register_x_tools.Letta') as mock_letta_class:
                mock_config = {
                    'api_key': 'test_letta_key',
                    'agent_id': 'test_agent_id',
                    'timeout': 30,
                    'base_url': 'https://custom.letta.ai'
                }
                mock_get_config.return_value = mock_config
                
                mock_client = MagicMock()
                mock_letta_class.return_value = mock_client
                
                mock_agent = MagicMock()
                mock_agent.id = 'test_agent_id'
                mock_agent.name = 'Test Agent'
                mock_client.agents.retrieve.return_value = mock_agent
                
                # Test registration
                register_x_tools()
                
                # Verify base_url was passed to client
                mock_letta_class.assert_called_once_with(
                    token='test_letta_key',
                    timeout=30,
                    base_url='https://custom.letta.ai'
                )
    
    def test_x_tool_registration_without_base_url(self):
        """Test X tool registration without base_url configuration."""
        with patch('register_x_tools.get_x_letta_config') as mock_get_config:
            with patch('register_x_tools.Letta') as mock_letta_class:
                mock_config = {
                    'api_key': 'test_letta_key',
                    'agent_id': 'test_agent_id',
                    'timeout': 30
                }
                mock_get_config.return_value = mock_config
                
                mock_client = MagicMock()
                mock_letta_class.return_value = mock_client
                
                mock_agent = MagicMock()
                mock_agent.id = 'test_agent_id'
                mock_agent.name = 'Test Agent'
                mock_client.agents.retrieve.return_value = mock_agent
                
                # Test registration
                register_x_tools()
                
                # Verify base_url was not passed to client
                mock_letta_class.assert_called_once_with(
                    token='test_letta_key',
                    timeout=30
                )
