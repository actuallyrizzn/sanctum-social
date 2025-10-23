from pydantic import BaseModel, Field, field_validator
from typing import Optional
import logging

logger = logging.getLogger("void_bot")

class DiscordFeedArgs(BaseModel):
    channel_id: str = Field(
        ..., 
        description="Discord channel ID to get feed from"
    )
    max_posts: int = Field(
        default=10,
        description="Maximum number of posts to retrieve (max 100)"
    )
    
    @field_validator('max_posts')
    @classmethod
    def validate_max_posts(cls, v):
        if v > 100:
            raise ValueError("max_posts cannot exceed 100")
        if v < 1:
            raise ValueError("max_posts must be at least 1")
        return v

def get_discord_feed(channel_id: str, max_posts: int = 10) -> str:
    """
    Get Discord channel feed.
    
    Args:
        channel_id: Discord channel ID to get feed from
        max_posts: Maximum number of posts to retrieve (max 100)
        
    Returns:
        Feed summary
        
    Raises:
        ValueError: If parameters are invalid
    """
    if not channel_id or len(channel_id.strip()) == 0:
        raise ValueError("Channel ID cannot be empty")
    
    if max_posts > 100:
        raise ValueError("max_posts cannot exceed 100")
    if max_posts < 1:
        raise ValueError("max_posts must be at least 1")
    
    return f'Retrieved Discord feed from channel {channel_id} - {max_posts} messages'
