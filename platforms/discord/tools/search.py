from pydantic import BaseModel, Field, field_validator
from typing import Optional
import logging

# Lazy logger initialization
def get_logger():
    """Get logger with configurable name, falling back to default if config not available."""
    try:
        from core.config import get_config, get_logger_names_config
        config = get_config()
        logger_names = get_logger_names_config(config._config)
        main_logger_name = logger_names.get("main", "agent_bot")
        return logging.getLogger(main_logger_name)
    except Exception:
        # Fallback to default logger name if config not available
        return logging.getLogger("agent_bot")

logger = get_logger()

class DiscordSearchArgs(BaseModel):
    query: str = Field(
        ..., 
        description="Search query for Discord messages"
    )
    max_results: int = Field(
        default=10,
        description="Maximum number of results to return (max 100)"
    )
    channel_id: Optional[str] = Field(
        default=None,
        description="Specific channel ID to search in (optional)"
    )
    
    @field_validator('max_results')
    @classmethod
    def validate_max_results(cls, v):
        if v > 100:
            raise ValueError("max_results cannot exceed 100")
        if v < 1:
            raise ValueError("max_results must be at least 1")
        return v

def search_discord_messages(query: str, max_results: int = 10, channel_id: Optional[str] = None) -> str:
    """
    Search Discord messages.
    
    Args:
        query: Search query for Discord messages
        max_results: Maximum number of results to return (max 100)
        channel_id: Specific channel ID to search in (optional)
        
    Returns:
        Search results summary
        
    Raises:
        ValueError: If parameters are invalid
    """
    if not query or len(query.strip()) == 0:
        raise ValueError("Search query cannot be empty")
    
    if max_results > 100:
        raise ValueError("max_results cannot exceed 100")
    if max_results < 1:
        raise ValueError("max_results must be at least 1")
    
    scope = f"in channel {channel_id}" if channel_id else "across all channels"
    return f'Discord search for "{query}" {scope} - returning up to {max_results} results'
