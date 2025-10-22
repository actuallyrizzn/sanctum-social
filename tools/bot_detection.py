"""
Bot detection tools for checking known_bots memory block.
"""
import os
import random
import logging
from typing import List, Tuple, Optional
from pydantic import BaseModel, Field
from letta_client import Letta

logger = logging.getLogger(__name__)


class CheckKnownBotsArgs(BaseModel):
    """Arguments for checking if users are in the known_bots list."""
    handles: List[str] = Field(..., description="List of user handles to check against known_bots")


def normalize_handle(handle: str) -> str:
    """
    Normalize handle for consistent comparison.
    
    Args:
        handle: Handle to normalize
        
    Returns:
        Normalized handle (lowercase, @ stripped, whitespace trimmed)
    """
    # First strip whitespace, then remove @ symbol, then strip again
    return handle.strip().lstrip('@').strip().lower()


def parse_bot_handles(content: str) -> List[str]:
    """
    Parse bot handles from various formats in the known_bots block content.
    
    Args:
        content: Content of the known_bots memory block
        
    Returns:
        List of normalized bot handles
    """
    handles = []
    for line in content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            handle = None
            
            # Handle multiple formats:
            # - @handle.bsky.social
            # - @handle.bsky.social: description
            # - handle.bsky.social
            # - handle.bsky.social: description
            if line.startswith('- @'):
                handle = line[3:].split(':')[0].strip()
            elif line.startswith('-'):
                handle = line[1:].split(':')[0].strip()
            elif line.startswith('@'):
                handle = line[1:].split(':')[0].strip()
            else:
                # Handle lines without prefix
                handle = line.split(':')[0].strip()
            
            if handle:
                handles.append(normalize_handle(handle))
    
    return handles


def check_known_bots(handles: List[str], agent_state: "AgentState") -> str:
    """
    Check if any of the provided handles are in the known_bots memory block.
    
    Args:
        handles: List of user handles to check (e.g., ['horsedisc.bsky.social', 'user.bsky.social'])
        agent_state: The agent state object containing agent information
        
    Returns:
        JSON string with bot detection results
    """
    import json
    
    try:
        # Create Letta client inline (for cloud execution)
        client = Letta(token=os.environ["LETTA_API_KEY"])
        
        # Get all blocks attached to the agent to check if known_bots is mounted
        attached_blocks = client.agents.blocks.list(agent_id=str(agent_state.id))
        attached_labels = {block.label for block in attached_blocks}
        
        if "known_bots" not in attached_labels:
            return json.dumps({
                "error": "known_bots memory block is not mounted to this agent",
                "bot_detected": False,
                "detected_bots": []
            })
        
        # Retrieve known_bots block content using agent-specific retrieval
        try:
            known_bots_block = client.agents.blocks.retrieve(
                agent_id=str(agent_state.id), 
                block_label="known_bots"
            )
        except Exception as e:
            return json.dumps({
                "error": f"Error retrieving known_bots block: {str(e)}",
                "bot_detected": False,
                "detected_bots": []
            })
        known_bots_content = known_bots_block.value
        
        # Parse known bots from content using improved parsing logic
        known_bot_handles = parse_bot_handles(known_bots_content)
        
        # Normalize input handles for consistent comparison
        normalized_input_handles = [normalize_handle(h) for h in handles]
        
        # Check for matches (case-insensitive)
        detected_bots = []
        for i, normalized_handle in enumerate(normalized_input_handles):
            if normalized_handle in known_bot_handles:
                # Return the original handle format for user reference
                detected_bots.append(handles[i])
        
        bot_detected = len(detected_bots) > 0
        
        return json.dumps({
            "bot_detected": bot_detected,
            "detected_bots": detected_bots,
            "total_known_bots": len(known_bot_handles),
            "checked_handles": handles,  # Return original handles for reference
            "normalized_checked_handles": normalized_input_handles,
            "normalized_known_bots": known_bot_handles
        })
        
    except Exception as e:
        logger.error(f"Error checking known_bots: {str(e)}")
        return json.dumps({
            "error": f"Error checking known_bots: {str(e)}",
            "bot_detected": False,
            "detected_bots": []
        })


def should_respond_to_bot_thread() -> bool:
    """
    Determine if we should respond to a bot thread (10% chance).
    
    Returns:
        True if we should respond, False if we should skip
    """
    return random.random() < 0.1


def extract_handles_from_thread(thread_data: dict) -> List[str]:
    """
    Extract all unique handles from a thread structure.
    
    Args:
        thread_data: Thread data dictionary from Bluesky API
        
    Returns:
        List of unique handles found in the thread
    """
    handles = set()
    
    def extract_from_post(post):
        """Recursively extract handles from a post and its replies."""
        if isinstance(post, dict):
            # Get author handle
            if 'post' in post and 'author' in post['post']:
                handle = post['post']['author'].get('handle')
                if handle:
                    handles.add(handle)
            elif 'author' in post:
                handle = post['author'].get('handle')
                if handle:
                    handles.add(handle)
            
            # Check replies
            if 'replies' in post:
                for reply in post['replies']:
                    extract_from_post(reply)
            
            # Check parent
            if 'parent' in post:
                extract_from_post(post['parent'])
    
    # Start extraction from thread root
    if 'thread' in thread_data:
        extract_from_post(thread_data['thread'])
    else:
        extract_from_post(thread_data)
    
    return list(handles)


# Tool configuration for registration
TOOL_CONFIG = {
    "type": "function",
    "function": {
        "name": "check_known_bots",
        "description": "Check if any of the provided handles are in the known_bots memory block",
        "parameters": CheckKnownBotsArgs.model_json_schema(),
    },
}