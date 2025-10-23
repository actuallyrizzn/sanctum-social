"""
Base platform interface for social media platforms.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BasePlatform(ABC):
    """Base class for all platform implementations."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize platform with configuration."""
        self.config = config
        self.enabled = config.get('enabled', True)
        self.name = config.get('name', 'unknown')
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the platform. Returns True if successful."""
        pass
    
    @abstractmethod
    def run(self) -> None:
        """Run the platform's main loop."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop the platform gracefully."""
        pass
    
    def is_enabled(self) -> bool:
        """Check if platform is enabled."""
        return self.enabled
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
