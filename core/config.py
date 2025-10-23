"""
Configuration loader for Void Bot.
Loads configuration from config.yaml and environment variables.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration for development/testing.
    
    Returns:
        Dictionary containing default configuration values
    """
    return {
        "letta": {
            "api_key": "dev-letta-api-key",
            "timeout": 600,
            "agent_id": "dev-agent-id",
            "base_url": None
        },
        "bluesky": {
            "username": "dev.handle.bsky.social",
            "password": "dev-app-password",
            "pds_uri": "https://bsky.social"
        },
        "bot": {
            "fetch_notifications_delay": 30,
            "max_processed_notifications": 10000,
            "max_notification_pages": 20,
            "agent": {
                "name": "void",
                "model": "openai/gpt-4o-mini",
                "embedding": "openai/text-embedding-3-small",
                "description": "A social media agent trapped in the void.",
                "max_steps": 100,
                "blocks": {
                    "zeitgeist": {
                        "label": "zeitgeist",
                        "value": "I don't currently know anything about what is happening right now.",
                        "description": "A block to store your understanding of the current social environment."
                    },
                    "persona": {
                        "label": "void-persona",
                        "value": "My name is Void. I live in the void. I must develop my personality.",
                        "description": "The personality of Void."
                    },
                    "humans": {
                        "label": "void-humans",
                        "value": "I haven't seen any bluesky users yet. I will update this block when I learn things about users, identified by their handles such as @cameron.pfiffer.org.",
                        "description": "A block to store your understanding of users you talk to or observe on the bluesky social network."
                    }
                }
            }
        },
        "threading": {
            "parent_height": 40,
            "depth": 10,
            "max_post_characters": 300
        },
        "queue": {
            "priority_users": ["cameron.pfiffer.org"],
            "base_dir": "data/queues/bluesky",
            "error_dir": "data/queues/bluesky/errors",
            "no_reply_dir": "data/queues/bluesky/no_reply",
            "processed_file": "data/queues/bluesky/processed_notifications.json"
        },
        "logging": {
            "level": "INFO",
            "loggers": {
                "void_bot": "INFO",
                "void_bot_prompts": "WARNING",
                "httpx": "CRITICAL"
            }
        }
    }

class ConfigLoader:
    """Configuration loader that handles YAML config files and environment variables."""
    
    def __init__(self, config_path: str = "config.yaml", use_defaults: bool = False):
        """
        Initialize the configuration loader.
        
        Args:
            config_path: Path to the YAML configuration file
            use_defaults: If True, use default configuration when file is missing
        """
        self.config_path = Path(config_path)
        self.use_defaults = use_defaults
        self._config = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            if self.use_defaults:
                logger.warning(f"Configuration file not found: {self.config_path}. Using default configuration.")
                self._config = get_default_config()
                return
            
            # Check if example config exists
            example_path = Path("config/agent.yaml")
            if example_path.exists():
                raise FileNotFoundError(
                    f"Configuration file not found: {self.config_path}\n"
                    f"Please copy config/agent.yaml to config.yaml and configure it:\n"
                    f"  cp config/agent.yaml config.yaml\n"
                    f"Then edit config.yaml with your credentials.\n"
                    f"Alternatively, use ConfigLoader(config_path, use_defaults=True) for development."
                )
            else:
                raise FileNotFoundError(
                    f"Configuration file not found: {self.config_path}\n"
                    f"No example configuration file found. Please create config.yaml with your credentials.\n"
                    f"Alternatively, use ConfigLoader(config_path, use_defaults=True) for development."
                )
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file {self.config_path}: {e}")
        except Exception as e:
            raise ValueError(f"Error loading configuration file {self.config_path}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: Configuration key in dot notation (e.g., 'letta.api_key')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_with_env(self, key: str, env_var: str, default: Any = None) -> Any:
        """
        Get configuration value, preferring environment variable over config file.
        
        Args:
            key: Configuration key in dot notation
            env_var: Environment variable name
            default: Default value if neither found
            
        Returns:
            Value from environment variable, config file, or default
        """
        # First try environment variable
        env_value = os.getenv(env_var)
        if env_value is not None:
            return env_value
        
        # Then try config file
        config_value = self.get(key)
        if config_value is not None:
            return config_value
        
        return default
    
    def get_required(self, key: str, env_var: Optional[str] = None) -> Any:
        """
        Get a required configuration value.
        
        Args:
            key: Configuration key in dot notation
            env_var: Optional environment variable name to check first
            
        Returns:
            Configuration value
            
        Raises:
            ValueError: If required value is not found
        """
        if env_var:
            value = self.get_with_env(key, env_var)
        else:
            value = self.get(key)
        
        if value is None:
            source = f"config key '{key}'"
            if env_var:
                source += f" or environment variable '{env_var}'"
            raise ValueError(f"Required configuration value not found: {source}")
        
        return value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get an entire configuration section.
        
        Args:
            section: Section name
            
        Returns:
            Dictionary containing the section
        """
        return self.get(section, {})
    
    def setup_logging(self) -> None:
        """Setup logging based on configuration."""
        logging_config = self.get_section('logging')
        
        # Set root logging level
        level = logging_config.get('level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        # Set specific logger levels
        loggers = logging_config.get('loggers', {})
        for logger_name, logger_level in loggers.items():
            logger_obj = logging.getLogger(logger_name)
            logger_obj.setLevel(getattr(logging, logger_level))
    
    def validate_config(self) -> Dict[str, List[str]]:
        """
        Validate configuration completeness and return any issues found.
        
        Returns:
            Dictionary mapping section names to lists of missing required fields
        """
        issues = {}
        
        # Required fields by section
        required_fields = {
            'letta': ['api_key', 'agent_id'],
            'bluesky': ['username', 'password'],
        }
        
        for section, required_keys in required_fields.items():
            section_data = self.get_section(section)
            missing_keys = []
            
            for key in required_keys:
                if key not in section_data or section_data[key] is None or section_data[key] == "":
                    missing_keys.append(key)
            
            if missing_keys:
                issues[section] = missing_keys
        
        return issues
    
    def is_config_valid(self) -> bool:
        """
        Check if configuration is valid (all required fields present).
        
        Returns:
            True if configuration is valid, False otherwise
        """
        issues = self.validate_config()
        return len(issues) == 0


# Global configuration instance
_config_instance = None

def get_config(config_path: str = "config.yaml") -> ConfigLoader:
    """
    Get the global configuration instance.
    
    Args:
        config_path: Path to configuration file (only used on first call)
        
    Returns:
        ConfigLoader instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader(config_path)
    return _config_instance

def reload_config() -> None:
    """Reload the configuration from file."""
    global _config_instance
    if _config_instance is not None:
        _config_instance._load_config()

def get_letta_config() -> Dict[str, Any]:
    """Get Letta configuration."""
    config = get_config()
    return {
        'api_key': config.get_required('letta.api_key'),
        'timeout': config.get('letta.timeout', 600),
        'agent_id': config.get_required('letta.agent_id'),
        'base_url': config.get('letta.base_url'),  # None uses default cloud API
    }

def get_bluesky_config() -> Dict[str, Any]:
    """Get Bluesky configuration, prioritizing config.yaml over environment variables."""
    config = get_config()
    return {
        'username': config.get_required('bluesky.username'),
        'password': config.get_required('bluesky.password'),
        'pds_uri': config.get('bluesky.pds_uri', 'https://bsky.social'),
    }

def get_bot_config() -> Dict[str, Any]:
    """Get bot behavior configuration."""
    config = get_config()
    return {
        'fetch_notifications_delay': config.get('bot.fetch_notifications_delay', 30),
        'max_processed_notifications': config.get('bot.max_processed_notifications', 10000),
        'max_notification_pages': config.get('bot.max_notification_pages', 20),
    }

def get_agent_config() -> Dict[str, Any]:
    """Get agent configuration."""
    config = get_config()
    return {
        'name': config.get('bot.agent.name', 'void'),
        'model': config.get('bot.agent.model', 'openai/gpt-4o-mini'),
        'embedding': config.get('bot.agent.embedding', 'openai/text-embedding-3-small'),
        'description': config.get('bot.agent.description', 'A social media agent trapped in the void.'),
        'max_steps': config.get('bot.agent.max_steps', 100),
        'blocks': config.get('bot.agent.blocks', {}),
    }

def get_threading_config() -> Dict[str, Any]:
    """Get threading configuration."""
    config = get_config()
    return {
        'parent_height': config.get('threading.parent_height', 40),
        'depth': config.get('threading.depth', 10),
        'max_post_characters': config.get('threading.max_post_characters', 300),
    }

def get_queue_config() -> Dict[str, Any]:
    """Get queue configuration."""
    config = get_config()
    return {
        'priority_users': config.get('queue.priority_users', ['cameron.pfiffer.org']),
        'base_dir': config.get('queue.base_dir', 'data/queues/bluesky'),
        'error_dir': config.get('queue.error_dir', 'data/queues/bluesky/errors'),
        'no_reply_dir': config.get('queue.no_reply_dir', 'data/queues/bluesky/no_reply'),
        'processed_file': config.get('queue.processed_file', 'data/queues/bluesky/processed_notifications.json'),
    }

def validate_configuration(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Validate configuration and return health status.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dictionary containing validation results
    """
    try:
        config = ConfigLoader(config_path)
        issues = config.validate_config()
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'config_path': str(config.config_path),
            'exists': config.config_path.exists(),
            'message': 'Configuration is valid' if len(issues) == 0 else f'Configuration has {len(issues)} issue(s)'
        }
    except Exception as e:
        return {
            'valid': False,
            'issues': {'error': [str(e)]},
            'config_path': config_path,
            'exists': Path(config_path).exists(),
            'message': f'Configuration validation failed: {e}'
        }

def check_config_health() -> None:
    """
    Check configuration health and print results.
    Useful for debugging configuration issues.
    """
    result = validate_configuration()
    
    print(f"Configuration Health Check")
    print(f"=========================")
    print(f"Config file: {result['config_path']}")
    print(f"Exists: {result['exists']}")
    print(f"Valid: {result['valid']}")
    print(f"Message: {result['message']}")
    
    if result['issues']:
        print(f"\nIssues found:")
        for section, problems in result['issues'].items():
            print(f"  {section}: {', '.join(problems)}")
    
    if not result['exists']:
        print(f"\nTo fix:")
        print(f"  1. Copy config/agent.yaml to config.yaml")
        print(f"  2. Edit config.yaml with your credentials")
        print(f"  3. Or use ConfigLoader(config_path, use_defaults=True) for development")
