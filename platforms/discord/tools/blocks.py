from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
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

class DiscordIgnoreArgs(BaseModel):
    user_ids: List[str] = Field(
        ..., 
        description="List of Discord user IDs to ignore"
    )
    reason: Optional[str] = Field(
        default="",
        description="Reason for ignoring the user"
    )
    
    @field_validator('user_ids')
    @classmethod
    def validate_user_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError("User IDs list cannot be empty")
        return v

def ignore_discord_users(user_ids: List[str], reason: str = "") -> str:
    """
    Ignore Discord users (software-based, not Discord blocks).
    
    Args:
        user_ids: List of Discord user IDs to ignore
        reason: Reason for ignoring the user
        
    Returns:
        Confirmation message with ignored user count
        
    Raises:
        ValueError: If user IDs list is invalid
    """
    if not user_ids or len(user_ids) == 0:
        raise ValueError("User IDs list cannot be empty")
    
    reason_text = f" (Reason: {reason})" if reason else ""
    return f'Ignored {len(user_ids)} Discord users{reason_text}'

def unignore_discord_users(user_ids: List[str]) -> str:
    """
    Remove Discord users from ignore list.
    
    Args:
        user_ids: List of Discord user IDs to unignore
        
    Returns:
        Confirmation message with unignored user count
        
    Raises:
        ValueError: If user IDs list is invalid
    """
    if not user_ids or len(user_ids) == 0:
        raise ValueError("User IDs list cannot be empty")
    
    return f'Removed {len(user_ids)} Discord users from ignore list'
