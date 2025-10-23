from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
import logging

logger = logging.getLogger("void_bot")

class DiscordReplyArgs(BaseModel):
    messages: List[str] = Field(
        ..., 
        description="List of reply messages (each max 2000 characters, max 4 messages total). Single item creates one reply, multiple items create a threaded reply chain."
    )
    
    @field_validator('messages')
    @classmethod
    def validate_messages(cls, v):
        if not v or len(v) == 0:
            raise ValueError("Messages list cannot be empty")
        if len(v) > 4:
            raise ValueError(f"Cannot send more than 4 reply messages (current: {len(v)} messages)")
        for i, message in enumerate(v):
            if len(message) > 2000:
                raise ValueError(f"Message {i+1} cannot be longer than 2000 characters (current: {len(message)} characters)")
        return v

def discord_reply(messages: List[str]) -> str:
    """
    Reply to Discord messages.
    
    Args:
        messages: List of reply messages (each max 2000 characters, max 4 messages total). 
                  Single item creates one reply, multiple items create a threaded reply chain.
        
    Returns:
        Confirmation message with message count
        
    Raises:
        ValueError: If messages list is invalid or messages exceed limits
    """
    if not messages or len(messages) == 0:
        raise ValueError("Messages list cannot be empty")
    if len(messages) > 4:
        raise ValueError(f"Cannot send more than 4 reply messages (current: {len(messages)} messages)")
    
    for i, message in enumerate(messages):
        if len(message) > 2000:
            raise ValueError(f"Message {i+1} cannot be longer than 2000 characters (current: {len(message)} characters)")
    
    if len(messages) == 1:
        return f'Discord reply sent'
    else:
        return f'Discord reply thread with {len(messages)} messages sent'
