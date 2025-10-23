"""
Unit tests for config_loader.py
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
import pytest
import yaml

from core.config import ConfigLoader, get_config, get_letta_config, get_bluesky_config, get_default_config, validate_configuration, check_config_health


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
        result = loader.get("agent.name")
        assert result == "test-agent"
    
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
        with patch('core.config.ConfigLoader') as mock_loader_class:
            mock_loader = mock_loader_class.return_value
            mock_loader.get.return_value = "test_value"
            
            result = get_config()
            mock_loader_class.assert_called_once_with("config.yaml")
    
    def test_get_config_custom_path(self, mock_config_file):
        """Test get_config with custom path."""
        with patch('core.config.ConfigLoader') as mock_loader_class:
            mock_loader = mock_loader_class.return_value
            mock_loader.get.return_value = "test_value"
            
            # Reset the global instance
            import core.config
            core.config._config_instance = None
            
            result = get_config("custom.yaml")
            mock_loader_class.assert_called_once_with("custom.yaml")
            assert result == mock_loader
    
    def test_get_letta_config(self, mock_config_file):
        """Test getting Letta configuration."""
        with patch('core.config.get_config') as mock_get_config:
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
        with patch('core.config.get_config') as mock_get_config:
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
        with patch('core.config.get_config') as mock_get_config:
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
        with patch('core.config.get_config') as mock_get_config:
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


class TestDefaultConfig:
    """Test cases for default configuration functionality."""
    
    def test_get_default_config(self):
        """Test that default configuration is properly structured."""
        default_config = get_default_config()
        
        # Check required sections exist
        assert 'agent' in default_config
        assert 'letta' in default_config
        assert 'platforms' in default_config
        assert 'bot' in default_config
        assert 'threading' in default_config
        assert 'queue' in default_config
        assert 'logging' in default_config
        
        # Check required fields in letta section
        assert 'api_key' in default_config['letta']
        assert 'agent_id' in default_config['letta']
        assert 'timeout' in default_config['letta']
        
        # Check required fields in platforms.bluesky section
        assert 'bluesky' in default_config['platforms']
        assert 'username' in default_config['platforms']['bluesky']
        assert 'password' in default_config['platforms']['bluesky']
        assert 'pds_uri' in default_config['platforms']['bluesky']
        
        # Check agent memory blocks
        assert 'memory_blocks' in default_config['agent']
        assert 'zeitgeist' in default_config['agent']['memory_blocks']
        assert 'persona' in default_config['agent']['memory_blocks']
        assert 'humans' in default_config['agent']['memory_blocks']


class TestConfigLoaderWithDefaults:
    """Test cases for ConfigLoader with use_defaults=True."""
    
    def test_init_with_defaults_missing_file(self, temp_dir):
        """Test ConfigLoader initialization with defaults when file is missing."""
        missing_config = temp_dir / "missing.yaml"
        
        with patch('core.config.logger') as mock_logger:
            loader = ConfigLoader(str(missing_config), use_defaults=True)
            
            # Should use default config
            assert loader._config is not None
            assert loader._config['letta']['api_key'] == 'dev-letta-api-key'
            assert loader._config['platforms']['bluesky']['username'] == 'dev.handle.bsky.social'
            
            # Should log warning
            mock_logger.warning.assert_called_once()
    
    def test_init_with_defaults_existing_file(self, mock_config_file):
        """Test ConfigLoader initialization with defaults when file exists."""
        loader = ConfigLoader(str(mock_config_file), use_defaults=True)
        
        # Should use file config, not defaults
        assert loader._config is not None
        assert loader._config['letta']['api_key'] == 'test-letta-api-key'  # From file
        assert loader._config['platforms']['bluesky']['username'] == 'test.bsky.social'  # From file


class TestConfigValidation:
    """Test cases for configuration validation functionality."""
    
    def test_validate_config_valid(self, mock_config_file):
        """Test validation with valid configuration."""
        loader = ConfigLoader(str(mock_config_file))
        issues = loader.validate_config()
        
        # Should have no issues
        assert len(issues) == 0
    
    def test_validate_config_missing_fields(self, temp_dir):
        """Test validation with missing required fields."""
        incomplete_config = temp_dir / "incomplete.yaml"
        incomplete_data = {
            "letta": {
                "api_key": "test-key"
                # Missing agent_id
            },
            "bluesky": {
                "username": "test.bsky.social"
                # Missing password
            }
        }
        
        with open(incomplete_config, 'w') as f:
            yaml.dump(incomplete_data, f)
        
        loader = ConfigLoader(str(incomplete_config))
        issues = loader.validate_config()
        
        # Should have issues
        assert len(issues) == 2
        assert 'letta' in issues
        assert 'agent_id' in issues['letta']
        assert 'platforms.bluesky' in issues
        assert 'password' in issues['platforms.bluesky']
    
    def test_is_config_valid_true(self, mock_config_file):
        """Test is_config_valid returns True for valid config."""
        loader = ConfigLoader(str(mock_config_file))
        assert loader.is_config_valid() is True
    
    def test_is_config_valid_false(self, temp_dir):
        """Test is_config_valid returns False for invalid config."""
        incomplete_config = temp_dir / "incomplete.yaml"
        incomplete_data = {
            "letta": {
                "api_key": "test-key"
                # Missing agent_id
            }
        }
        
        with open(incomplete_config, 'w') as f:
            yaml.dump(incomplete_data, f)
        
        loader = ConfigLoader(str(incomplete_config))
        assert loader.is_config_valid() is False


class TestValidationFunctions:
    """Test cases for validation utility functions."""
    
    def test_validate_configuration_valid(self, mock_config_file):
        """Test validate_configuration with valid config."""
        result = validate_configuration(str(mock_config_file))
        
        assert result['valid'] is True
        assert len(result['issues']) == 0
        assert result['exists'] is True
        assert 'valid' in result['message']
    
    def test_validate_configuration_invalid(self, temp_dir):
        """Test validate_configuration with invalid config."""
        incomplete_config = temp_dir / "incomplete.yaml"
        incomplete_data = {
            "letta": {
                "api_key": "test-key"
                # Missing agent_id
            }
        }
        
        with open(incomplete_config, 'w') as f:
            yaml.dump(incomplete_data, f)
        
        result = validate_configuration(str(incomplete_config))
        
        assert result['valid'] is False
        assert len(result['issues']) > 0
        assert result['exists'] is True
        assert 'issue' in result['message']
    
    def test_validate_configuration_missing_file(self, temp_dir):
        """Test validate_configuration with missing file."""
        missing_config = temp_dir / "missing.yaml"
        result = validate_configuration(str(missing_config))
        
        assert result['valid'] is False
        assert result['exists'] is False
        assert 'error' in result['issues']
    
    def test_check_config_health(self, mock_config_file, capsys):
        """Test check_config_health function."""
        check_config_health()
        
        captured = capsys.readouterr()
        assert "Configuration Health Check" in captured.out
        assert "Config file:" in captured.out
        assert "Exists:" in captured.out
        assert "Valid:" in captured.out
