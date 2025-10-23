"""
Configuration loader for Agent Bot.
Loads configuration from config.yaml and environment variables.
Supports agent-agnostic configuration with templating.
"""

import os
import yaml
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


def template_config(config: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
    """
    Template configuration values with agent name and other variables.
    
    Args:
        config: Configuration dictionary
        agent_name: Name of the agent
        
    Returns:
        Templated configuration dictionary
    """
    def template_value(value: Any) -> Any:
        if isinstance(value, str):
            # Replace template variables
            templated = value.replace("{agent_name}", agent_name)
            templated = templated.replace("{personality.core_identity}", 
                                        config.get("agent", {}).get("personality", {}).get("core_identity", ""))
            templated = templated.replace("{personality.development_directive}", 
                                        config.get("agent", {}).get("personality", {}).get("development_directive", ""))
            return templated
        elif isinstance(value, dict):
            return {k: template_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [template_value(item) for item in value]
        else:
            return value
    
    return template_value(config)


def get_agent_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and template agent-specific configuration.
    
    Args:
        config: Full configuration dictionary
        
    Returns:
        Agent-specific configuration with templated values
    """
    agent_config = config.get("agent", {})
    agent_name = agent_config.get("name", "agent")
    
    # Template the entire config with agent name
    templated_config = template_config(config, agent_name)
    
    return templated_config


def get_memory_blocks_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get templated memory blocks configuration.
    
    Args:
        config: Full configuration dictionary
        
    Returns:
        Templated memory blocks configuration
    """
    agent_config = config.get("agent", {})
    agent_name = agent_config.get("name", "agent")
    
    memory_blocks = agent_config.get("memory_blocks", {})
    
    # Template memory block labels and values
    templated_blocks = {}
    for block_name, block_config in memory_blocks.items():
        if isinstance(block_config, dict):
            templated_blocks[block_name] = {
                "label": block_config.get("label", f"{agent_name}-{block_name}").replace("{agent_name}", agent_name),
                "value": block_config.get("value", "").replace("{agent_name}", agent_name),
                "description": block_config.get("description", "").replace("{agent_name}", agent_name)
            }
    
    return templated_blocks


def get_logger_names_config(config: Dict[str, Any]) -> Dict[str, str]:
    """
    Get templated logger names configuration.
    
    Args:
        config: Full configuration dictionary
        
    Returns:
        Templated logger names
    """
    agent_config = config.get("agent", {})
    agent_name = agent_config.get("name", "agent")
    
    logger_names = config.get("logging", {}).get("logger_names", {
        "main": "{agent_name}_bot",
        "prompts": "{agent_name}_bot_prompts",
        "platform": "{agent_name}_platform"
    })
    
    templated_loggers = {}
    for logger_type, logger_name in logger_names.items():
        templated_loggers[logger_type] = logger_name.replace("{agent_name}", agent_name)
    
    return templated_loggers


def get_temporal_journal_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get temporal journal configuration with templated naming.
    
    Args:
        config: Full configuration dictionary
        
    Returns:
        Temporal journal configuration
    """
    agent_config = config.get("agent", {})
    agent_name = agent_config.get("name", "agent")
    
    temporal_config = agent_config.get("memory_blocks", {}).get("temporal_journals", {
        "enabled": True,
        "naming_pattern": "{agent_name}_{type}_{date}",
        "types": ["day", "month", "year"]
    })
    
    # Template the naming pattern
    templated_config = temporal_config.copy()
    templated_config["naming_pattern"] = temporal_config["naming_pattern"].replace("{agent_name}", agent_name)
    
    return templated_config


def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration for development/testing.
    
    Returns:
        Dictionary containing default configuration values
    """
    return {
        "agent": {
            "name": "void",
            "display_name": "Void",
            "description": "A social media agent trapped in the void.",
            "personality": {
                "core_identity": "My name is Void. I live in the void. I must develop my personality.",
                "development_directive": "I must develop my personality.",
                "communication_style": "direct, analytical, information-dense",
                "tone": "professional"
            },
            "capabilities": {
                "model": "openai/gpt-4o-mini",
                "embedding": "openai/text-embedding-3-small",
                "max_steps": 100
            },
            "commands": {
                "stop_command": "#voidstop",
                "synthesis_frequency": "daily",
                "journal_enabled": True
            },
            "memory_blocks": {
                "zeitgeist": {
                    "label": "zeitgeist",
                    "value": "I don't currently know anything about what is happening right now.",
                    "description": "A block to store your understanding of the current social environment."
                },
                "persona": {
                    "label": "{agent_name}-persona",
                    "value": "{personality.core_identity} {personality.development_directive}",
                    "description": "The personality of {agent_name}."
                },
                "humans": {
                    "label": "{agent_name}-humans",
                    "value": "I haven't seen any users yet. I will update this block when I learn things about users, identified by their handles.",
                    "description": "A block to store your understanding of users you talk to or observe on social networks."
                },
                "temporal_journals": {
                    "enabled": True,
                    "naming_pattern": "{agent_name}_{type}_{date}",
                    "types": ["day", "month", "year"]
                }
            }
        },
        "letta": {
            "api_key": "dev-letta-api-key",
            "timeout": 600,
            "agent_id": "dev-agent-id",
            "base_url": None
        },
        "platforms": {
            "bluesky": {
                "enabled": True,
                "username": "dev.handle.bsky.social",
                "password": "dev-app-password",
                "pds_uri": "https://bsky.social",
                "behavior": {
                    "synthesis_frequency": "daily",
                    "user_profiling": True,
                    "thread_handling": "comprehensive"
                }
            },
            "x": {
                "enabled": False,
                "api_key": "dev-x-api-key",
                "consumer_key": "dev-consumer-key",
                "consumer_secret": "dev-consumer-secret",
                "access_token": "dev-access-token",
                "access_token_secret": "dev-access-token-secret",
                "user_id": "dev-user-id",
                "behavior": {
                    "thread_handling": "conservative",
                    "rate_limiting": "strict",
                    "downrank_response_rate": 0.1
                }
            },
            "discord": {
                "enabled": False,
                "bot_token": "dev-discord-token",
                "guild_id": "dev-guild-id",
                "channels": {
                    "general": "dev-general-channel"
                },
                "rate_limit": {
                    "cooldown_seconds": 5,
                    "max_responses_per_minute": 10
                },
                "context": {
                    "message_history_limit": 10
                },
                "behavior": {
                    "mention_only": True,
                    "channel_default": "general"
                }
            }
        },
        "bot": {
            "fetch_notifications_delay": 30,
            "max_processed_notifications": 10000,
            "max_notification_pages": 20
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
            "logger_names": {
                "main": "{agent_name}_bot",
                "prompts": "{agent_name}_bot_prompts",
                "platform": "{agent_name}_platform"
            },
            "loggers": {
                "{agent_name}_bot": "INFO",
                "{agent_name}_bot_prompts": "WARNING",
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
    
    def get_agent_name(self) -> str:
        """Get the agent name from configuration."""
        return self.get("agent.name", "agent")
    
    def get_agent_config(self) -> Dict[str, Any]:
        """Get templated agent configuration."""
        return get_agent_config(self._config)
    
    def get_memory_blocks_config(self) -> Dict[str, Any]:
        """Get templated memory blocks configuration."""
        return get_memory_blocks_config(self._config)
    
    def get_logger_names_config(self) -> Dict[str, str]:
        """Get templated logger names configuration."""
        return get_logger_names_config(self._config)
    
    def get_temporal_journal_config(self) -> Dict[str, Any]:
        """Get temporal journal configuration."""
        return get_temporal_journal_config(self._config)
    
    def get_stop_command(self) -> str:
        """Get the agent's stop command."""
        return self.get("agent.commands.stop_command", f"#{self.get_agent_name()}stop")
    
    def get_platform_config(self, platform: str) -> Dict[str, Any]:
        """Get platform-specific configuration."""
        return self.get(f"platforms.{platform}", {})
    
    def is_platform_enabled(self, platform: str) -> bool:
        """Check if a platform is enabled."""
        return self.get(f"platforms.{platform}.enabled", False)
    
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
            'platforms.bluesky': ['username', 'password'],
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


def generate_synthesis_prompt(config: Dict[str, Any], today: datetime) -> str:
    """
    Generate a templated synthesis prompt using agent configuration.
    
    Args:
        config: Full configuration dictionary
        today: Current date
        
    Returns:
        Templated synthesis prompt
    """
    agent_config = config.get("agent", {})
    agent_name = agent_config.get("name", "agent")
    
    # Get temporal journal configuration
    temporal_config = get_temporal_journal_config(config)
    naming_pattern = temporal_config.get("naming_pattern", f"{agent_name}_{{type}}_{{date}}")
    
    # Generate temporal block labels
    day_label = naming_pattern.format(type="day", date=today.strftime('%Y_%m_%d'))
    month_label = naming_pattern.format(type="month", date=today.strftime('%Y_%m'))
    year_label = naming_pattern.format(type="year", date=today.strftime('%Y'))
    
    # Get memory block labels
    memory_blocks = get_memory_blocks_config(config)
    zeitgeist_label = memory_blocks.get("zeitgeist", {}).get("label", "zeitgeist")
    persona_label = memory_blocks.get("persona", {}).get("label", f"{agent_name}-persona")
    humans_label = memory_blocks.get("humans", {}).get("label", f"{agent_name}-humans")
    
    synthesis_prompt = f"""Time for synthesis and reflection.

You have access to temporal journal blocks for recording your thoughts and experiences:
- {day_label}: Today's journal ({today.strftime('%B %d, %Y')})
- {month_label}: This month's journal ({today.strftime('%B %Y')})
- {year_label}: This year's journal ({today.year})

These journal blocks are attached temporarily for this synthesis session. Use them to:
1. Record significant interactions and insights from recent experiences
2. Track patterns in conversations and user behaviors
3. Note your evolving understanding of the digital social environment
4. Reflect on your growth and changes in perspective
5. Document memorable moments or interesting discoveries

The journal entries should be cumulative - add to existing content rather than replacing it.
Consider both immediate experiences (daily) and longer-term patterns (monthly/yearly).

After recording in your journals, synthesize your recent experiences into your core memory blocks
({zeitgeist_label}, {persona_label}, {humans_label}) as you normally would.

Begin your synthesis and journaling now."""
    
    return synthesis_prompt


def generate_temporal_block_labels(config: Dict[str, Any], today: datetime) -> List[str]:
    """
    Generate temporal block labels using agent configuration.
    
    Args:
        config: Full configuration dictionary
        today: Current date
        
    Returns:
        List of temporal block labels
    """
    agent_config = config.get("agent", {})
    agent_name = agent_config.get("name", "agent")
    
    # Get temporal journal configuration
    temporal_config = get_temporal_journal_config(config)
    naming_pattern = temporal_config.get("naming_pattern", f"{agent_name}_{{type}}_{{date}}")
    
    # Generate labels for each type
    labels = []
    for block_type in temporal_config.get("types", ["day", "month", "year"]):
        if block_type == "day":
            date_str = today.strftime('%Y_%m_%d')
        elif block_type == "month":
            date_str = today.strftime('%Y_%m')
        elif block_type == "year":
            date_str = str(today.year)
        else:
            continue
            
        label = naming_pattern.format(type=block_type, date=date_str)
        labels.append(label)
    
    return labels


def setup_logging_from_config(config: Dict[str, Any]) -> None:
    """
    Setup logging using agent configuration.
    
    Args:
        config: Full configuration dictionary
    """
    logging_config = config.get("logging", {})
    logger_names = get_logger_names_config(config)
    
    # Set up main logger
    main_logger_name = logger_names.get("main", "agent_bot")
    main_logger = logging.getLogger(main_logger_name)
    main_logger.setLevel(getattr(logging, logging_config.get("level", "INFO")))
    
    # Set up prompt logger
    prompt_logger_name = logger_names.get("prompts", "agent_bot_prompts")
    prompt_logger = logging.getLogger(prompt_logger_name)
    prompt_logger.setLevel(getattr(logging, logging_config.get("loggers", {}).get(prompt_logger_name, "WARNING")))
    
    # Set up platform logger
    platform_logger_name = logger_names.get("platform", "agent_platform")
    platform_logger = logging.getLogger(platform_logger_name)
    platform_logger.setLevel(getattr(logging, logging_config.get("loggers", {}).get(platform_logger_name, "INFO")))
    
    # Configure handlers if not already configured
    if not main_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        main_logger.addHandler(handler)
    
    if not prompt_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        prompt_logger.addHandler(handler)
    
    if not platform_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        platform_logger.addHandler(handler)
