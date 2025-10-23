from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
import logging

logger = logging.getLogger("void_bot")

class DiscordPostArgs(BaseModel):
    text: List[str] = Field(
        ..., 
        description="List of texts to create Discord messages (each max 2000 characters). Single item creates one message, multiple items create a thread."
    )
    
    @field_validator('text')
    @classmethod
    def validate_text_list(cls, v):
        if not v or len(v) == 0:
            raise ValueError("Text list cannot be empty")
        for i, text in enumerate(v):
            if len(text) > 2000:
                raise ValueError(f"Message {i+1} cannot be longer than 2000 characters (current: {len(text)} characters)")
        return v

def create_new_discord_post(text: List[str]) -> str:
    """
    Create new Discord messages in a channel.
    
    Args:
        text: List of texts to create Discord messages (each max 2000 characters). 
              Single item creates one message, multiple items create a thread.
        
    Returns:
        Confirmation message with message count
        
    Raises:
        ValueError: If text list is invalid or messages exceed limits
    """
    if not text or len(text) == 0:
        raise ValueError("Text list cannot be empty")
    
    for i, message_text in enumerate(text):
        if len(message_text) > 2000:
            raise ValueError(f"Message {i+1} cannot be longer than 2000 characters (current: {len(message_text)} characters)")
    
    if len(text) == 1:
        return f'Discord message sent'
    else:
        return f'Discord thread with {len(text)} messages sent'
