import json
import yaml
from typing import Dict, Any, List, Optional
from datetime import datetime

def mention_to_yaml_string(mention: dict) -> str:
    """Convert Discord mention to YAML string for Letta processing"""
    try:
        yaml_data = {
            'platform': 'discord',
            'mention_id': mention['id'],
            'content': mention['content'],
            'author': {
                'id': mention['author']['id'],
                'name': mention['author']['name'],
                'display_name': mention['author']['display_name']
            },
            'channel_id': mention['channel_id'],
            'guild_id': mention.get('guild_id'),
            'created_at': mention['created_at']
        }
        
        return yaml.dump(yaml_data, default_flow_style=False, sort_keys=False)
    except Exception as e:
        return f"Error converting Discord mention to YAML: {e}"

def thread_to_yaml_string(thread_data: dict) -> str:
    """Convert Discord thread/conversation to YAML string"""
    try:
        yaml_data = {
            'platform': 'discord',
            'conversation_id': thread_data.get('conversation_id'),
            'messages': thread_data.get('messages', []),
            'users': thread_data.get('users', {}),
            'channel_id': thread_data.get('channel_id'),
            'guild_id': thread_data.get('guild_id')
        }
        
        return yaml.dump(yaml_data, default_flow_style=False, sort_keys=False)
    except Exception as e:
        return f"Error converting Discord thread to YAML: {e}"

def convert_to_basic_types(data):
    """Convert Discord data to basic Python types for JSON serialization"""
    if isinstance(data, dict):
        return {key: convert_to_basic_types(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_to_basic_types(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    elif hasattr(data, '__dict__'):
        return convert_to_basic_types(data.__dict__)
    else:
        return data

def strip_fields(data, fields_to_strip):
    """Strip specified fields from Discord data"""
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key not in fields_to_strip:
                result[key] = strip_fields(value, fields_to_strip)
        return result
    elif isinstance(data, list):
        return [strip_fields(item, fields_to_strip) for item in data]
    else:
        return data

def flatten_thread_structure(thread_data):
    """Flatten Discord thread structure for easier processing"""
    try:
        flattened = {
            'platform': 'discord',
            'conversation_id': thread_data.get('conversation_id'),
            'messages': [],
            'users': {}
        }
        
        # Extract messages
        messages = thread_data.get('messages', [])
        for message in messages:
            flattened['messages'].append({
                'id': message.get('id'),
                'content': message.get('content'),
                'author_id': message.get('author', {}).get('id'),
                'created_at': message.get('created_at'),
                'channel_id': message.get('channel_id')
            })
            
            # Extract user info
            author = message.get('author', {})
            if author.get('id'):
                flattened['users'][author['id']] = {
                    'id': author['id'],
                    'name': author.get('name'),
                    'display_name': author.get('display_name')
                }
        
        return flattened
    except Exception as e:
        return {'error': f'Error flattening Discord thread: {e}'}

def remove_outside_quotes(text: str) -> str:
    """Remove quotes from the outside of a string if they exist"""
    if not text:
        return text
    
    # Check for single quotes
    if text.startswith("'") and text.endswith("'"):
        return text[1:-1]
    
    # Check for double quotes
    if text.startswith('"') and text.endswith('"'):
        return text[1:-1]
    
    return text

def create_discord_ack(mention_id: str, note: str = "") -> str:
    """Create acknowledgment message for Discord mention"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if note:
        return f"✅ Discord mention {mention_id} acknowledged at {timestamp}\nNote: {note}"
    else:
        return f"✅ Discord mention {mention_id} acknowledged at {timestamp}"

def create_discord_tool_call_record(tool_name: str, args: dict, result: str) -> str:
    """Create tool call record for Discord operations"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return f"""Discord Tool Call Record
Tool: {tool_name}
Timestamp: {timestamp}
Arguments: {json.dumps(args, indent=2)}
Result: {result}"""

def create_discord_reasoning_record(reasoning: str) -> str:
    """Create reasoning record for Discord operations"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return f"""Discord Reasoning Record
Timestamp: {timestamp}
Reasoning: {reasoning}"""

# Constants for Discord operations
DISCORD_STRIP_FIELDS = [
    'avatar', 'avatar_url', 'banner', 'banner_url', 'accent_color',
    'public_flags', 'system', 'bot', 'verified', 'mfa_enabled',
    'premium_type', 'premium_since', 'flags', 'permissions'
]

DISCORD_MAX_MESSAGE_LENGTH = 2000
DISCORD_MAX_EMBED_LENGTH = 6000
DISCORD_RATE_LIMIT_COOLDOWN = 5  # seconds
DISCORD_MAX_RESPONSES_PER_MINUTE = 10
DISCORD_CONTEXT_MESSAGE_LIMIT = 10
