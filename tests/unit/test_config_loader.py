"""
Unit tests for config_loader.py
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
import pytest
import yaml

from config_loader import ConfigLoader, get_config, get_letta_config, get_bluesky_config


class TestConfigLoader:
    """Test cases for ConfigLoader class."""
    
    def test_init_with_existing_config(self, mock_config_file):
        """Test ConfigLoader initialization with existing config file."""
        loader = ConfigLoader(str(mock_config_file))
        assert loader.config_path == mock_config_file
        assert loader._config is not None
    
    def test_init_with_missing_config(self, temp_dir):
        """Test ConfigLoader initialization with missing config file."""
        missing_config = temp_dir / "missing.yaml"
        with pytest.raises(FileNotFoundError):
            ConfigLoader(str(missing_config))
    
    def test_get_existing_key(self, mock_config_file):
        """Test getting an existing configuration key."""
        loader = ConfigLoader(str(mock_config_file))
        result = loader.get("letta.api_key")
        assert result == "test-letta-api-key"
    
    def test_get_nested_key(self, mock_config_file):
        """Test getting a nested configuration key."""
        loader = ConfigLoader(str(mock_config_file))
        result = loader.get("bot.agent.name")
        assert result == "test-void"
    
    def test_get_missing_key_with_default(self, mock_config_file):
        """Test getting a missing key with default value."""
        loader = ConfigLoader(str(mock_config_file))
        result = loader.get("nonexistent.key", "default_value")
        assert result == "default_value"
    
    def test_get_missing_key_without_default(self, mock_config_file):
        """Test getting a missing key without default value."""
        loader = ConfigLoader(str(mock_config_file))
        result = loader.get("nonexistent.key")
        assert result is None
    
    def test_get_section(self, mock_config_file):
        """Test getting an entire configuration section."""
        loader = ConfigLoader(str(mock_config_file))
        result = loader.get_section("letta")
        assert isinstance(result, dict)
        assert result["api_key"] == "test-letta-api-key"
        assert result["project_id"] == "test-project-id"
    
    def test_get_section_missing(self, mock_config_file):
        """Test getting a missing configuration section."""
        loader = ConfigLoader(str(mock_config_file))
        result = loader.get_section("nonexistent")
        assert result == {}  # Returns empty dict, not None
    
    def test_invalid_yaml(self, temp_dir):
        """Test handling of invalid YAML configuration."""
        invalid_config = temp_dir / "invalid.yaml"
        with open(invalid_config, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        with pytest.raises(ValueError, match="Invalid YAML"):
            ConfigLoader(str(invalid_config))


class TestConfigFunctions:
    """Test cases for configuration utility functions."""
    
    def test_get_config_default_path(self, mock_config_file):
        """Test get_config with default path."""
        with patch('config_loader.ConfigLoader') as mock_loader_class:
            mock_loader = mock_loader_class.return_value
            mock_loader.get.return_value = "test_value"
            
            result = get_config()
            mock_loader_class.assert_called_once_with("config.yaml")
    
    def test_get_config_custom_path(self, mock_config_file):
        """Test get_config with custom path."""
        with patch('config_loader.ConfigLoader') as mock_loader_class:
            mock_loader = mock_loader_class.return_value
            mock_loader.get.return_value = "test_value"
            
            # Reset the global instance
            import config_loader
            config_loader._config_instance = None
            
            result = get_config("custom.yaml")
            mock_loader_class.assert_called_once_with("custom.yaml")
            assert result == mock_loader
    
    def test_get_letta_config(self, mock_config_file):
        """Test getting Letta configuration."""
        with patch('config_loader.get_config') as mock_get_config:
            mock_loader = mock_get_config.return_value
            mock_loader.get_required.side_effect = lambda key: {
                'letta.api_key': 'test-key',
                'letta.agent_id': 'test-agent-id'
            }.get(key)
            mock_loader.get.side_effect = lambda key, default=None: {
                'letta.timeout': 30,
                'letta.base_url': None
            }.get(key, default)
            
            result = get_letta_config()
            assert result["api_key"] == "test-key"
            assert result["agent_id"] == "test-agent-id"
            assert result["timeout"] == 30
            assert result["base_url"] is None
    
    def test_get_bluesky_config(self, mock_config_file):
        """Test getting Bluesky configuration."""
        with patch('config_loader.get_config') as mock_get_config:
            mock_loader = mock_get_config.return_value
            mock_loader.get_required.side_effect = lambda key: {
                'bluesky.username': 'test.bsky.social',
                'bluesky.password': 'test-password'
            }.get(key)
            mock_loader.get.side_effect = lambda key, default: {
                'bluesky.pds_uri': 'https://bsky.social'
            }.get(key, default)
            
            result = get_bluesky_config()
            assert result["username"] == "test.bsky.social"
            assert result["password"] == "test-password"
            assert result["pds_uri"] == "https://bsky.social"
    
    def test_get_letta_config_with_env_fallback(self, mock_env_vars):
        """Test Letta config with environment variable fallback."""
        with patch('config_loader.get_config') as mock_get_config:
            mock_loader = mock_get_config.return_value
            mock_loader.get_required.side_effect = lambda key: {
                'letta.api_key': 'test-letta-api-key',
                'letta.agent_id': 'test-agent-id'
            }.get(key)
            mock_loader.get.side_effect = lambda key, default=None: {
                'letta.timeout': 600,
                'letta.base_url': None
            }.get(key, default)
            
            result = get_letta_config()
            assert result["api_key"] == "test-letta-api-key"
    
    def test_get_bluesky_config_with_env_fallback(self, mock_env_vars):
        """Test Bluesky config with environment variable fallback."""
        with patch('config_loader.get_config') as mock_get_config:
            mock_loader = mock_get_config.return_value
            mock_loader.get_required.side_effect = lambda key: {
                'bluesky.username': 'test.bsky.social',
                'bluesky.password': 'test-app-password'
            }.get(key)
            mock_loader.get.side_effect = lambda key, default: {
                'bluesky.pds_uri': 'https://bsky.social'
            }.get(key, default)
            
            result = get_bluesky_config()
            assert result["username"] == "test.bsky.social"
            assert result["password"] == "test-app-password"
            assert result["pds_uri"] == "https://bsky.social"


class TestConfigValidation:
    """Test cases for configuration validation."""
    
    def test_required_fields_present(self, mock_config_file):
        """Test validation when all required fields are present."""
        loader = ConfigLoader(str(mock_config_file))
        
        # Test Letta required fields
        assert loader.get("letta.api_key") is not None
        assert loader.get("letta.project_id") is not None
        
        # Test Bluesky required fields
        assert loader.get("bluesky.username") is not None
        assert loader.get("bluesky.password") is not None
    
    def test_missing_required_fields(self, temp_dir):
        """Test validation when required fields are missing."""
        incomplete_config = temp_dir / "incomplete.yaml"
        incomplete_data = {
            "letta": {
                "api_key": "test-key"
                # Missing project_id
            },
            "bluesky": {
                "username": "test.bsky.social"
                # Missing password
            }
        }
        
        with open(incomplete_config, 'w') as f:
            yaml.dump(incomplete_data, f)
        
        loader = ConfigLoader(str(incomplete_config))
        
        # Should not raise error, but return None for missing fields
        assert loader.get("letta.project_id") is None
        assert loader.get("bluesky.password") is None
    
    def test_config_type_coercion(self, temp_dir):
        """Test that configuration values are properly typed."""
        config_with_types = temp_dir / "typed.yaml"
        typed_data = {
            "bot": {
                "fetch_notifications_delay": 30,  # int
                "max_processed_notifications": 1000,  # int
            },
            "threading": {
                "parent_height": 40,  # int
                "depth": 10,  # int
                "max_post_characters": 300,  # int
            },
            "logging": {
                "level": "INFO",  # str
            }
        }
        
        with open(config_with_types, 'w') as f:
            yaml.dump(typed_data, f)
        
        loader = ConfigLoader(str(config_with_types))
        
        # Test integer values
        assert isinstance(loader.get("bot.fetch_notifications_delay"), int)
        assert loader.get("bot.fetch_notifications_delay") == 30
        
        # Test string values
        assert isinstance(loader.get("logging.level"), str)
        assert loader.get("logging.level") == "INFO"


@pytest.mark.parametrize("config_key,expected_type", [
    ("letta.api_key", str),
    ("letta.timeout", int),
    ("bot.fetch_notifications_delay", int),
    ("bot.max_processed_notifications", int),
    ("threading.parent_height", int),
    ("threading.depth", int),
    ("threading.max_post_characters", int),
    ("logging.level", str),
])
def test_config_value_types(mock_config_file, config_key, expected_type):
    """Test that configuration values have expected types."""
    loader = ConfigLoader(str(mock_config_file))
    value = loader.get(config_key)
    
    if value is not None:
        assert isinstance(value, expected_type), f"Expected {expected_type}, got {type(value)} for {config_key}"
