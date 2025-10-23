# Rich imports removed - using simple text formatting
from time import sleep
from letta_client import Letta
from .utils import thread_to_yaml_string
import os
import logging
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import time
import argparse

from utils.utils import (
    upsert_block,
    upsert_agent
)
from core.config import get_letta_config, get_config, generate_synthesis_prompt, generate_temporal_block_labels, setup_logging_from_config, get_logger_names_config

from . import utils as bsky_utils
from .tools.blocks import attach_user_blocks, detach_user_blocks
from datetime import date
from utils.notification_db import NotificationDB

def extract_handles_from_data(data):
    """Recursively extract all unique handles from nested data structure."""
    handles = set()
    
    def _extract_recursive(obj):
        if isinstance(obj, dict):
            # Check if this dict has a 'handle' key
            if 'handle' in obj:
                handles.add(obj['handle'])
            # Recursively check all values
            for value in obj.values():
                _extract_recursive(value)
        elif isinstance(obj, list):
            # Recursively check all list items
            for item in obj:
                _extract_recursive(item)
    
    _extract_recursive(data)
    return list(handles)

# Initialize logging early to prevent NoneType errors
import logging

# Get logger names from configuration
config = get_config()
logger_names = get_logger_names_config(config._config)
main_logger_name = logger_names.get("main", "agent_bot")
prompt_logger_name = logger_names.get("prompts", "agent_bot_prompts")

logger = logging.getLogger(main_logger_name)
logger.setLevel(logging.INFO)

# Create a simple handler if none exists
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

prompt_logger = logging.getLogger(prompt_logger_name)
prompt_logger.setLevel(logging.WARNING)
# Simple text formatting (Rich no longer used)
SHOW_REASONING = False
last_archival_query = "archival memory search"

def log_with_panel(message, title=None, border_color="white"):
    """Log a message with Unicode box-drawing characters"""
    if title:
        # Map old color names to appropriate symbols
        symbol_map = {
            "blue": "⚙",      # Tool calls
            "green": "✓",     # Success/completion
            "yellow": "◆",    # Reasoning
            "red": "✗",       # Errors
            "white": "▶",     # Default/mentions
            "cyan": "✎",      # Posts
        }
        symbol = symbol_map.get(border_color, "▶")
        
        print(f"\n{symbol} {title}")
        print(f"  {'─' * len(title)}")
        # Indent message lines
        for line in message.split('\n'):
            print(f"  {line}")
    else:
        print(message)


# Configuration will be loaded when needed in functions

# Notification check delay
FETCH_NOTIFICATIONS_DELAY_SEC = 10  # Check every 10 seconds for faster response

# Check for new notifications every N queue items
CHECK_NEW_NOTIFICATIONS_EVERY_N_ITEMS = 2  # Check more frequently during processing

# Queue directory
QUEUE_DIR = Path("data/queues/bluesky")
QUEUE_DIR.mkdir(exist_ok=True, parents=True)
QUEUE_ERROR_DIR = Path("data/queues/bluesky/errors")
QUEUE_ERROR_DIR.mkdir(exist_ok=True, parents=True)
QUEUE_NO_REPLY_DIR = Path("data/queues/bluesky/no_reply")
QUEUE_NO_REPLY_DIR.mkdir(exist_ok=True, parents=True)
PROCESSED_NOTIFICATIONS_FILE = Path("data/queues/bluesky/processed_notifications.json")

# Maximum number of processed notifications to track
MAX_PROCESSED_NOTIFICATIONS = 10000

# Message tracking counters
message_counters = defaultdict(int)
start_time = time.time()

# Testing mode flag
TESTING_MODE = False

# Skip git operations flag
SKIP_GIT = False

# Synthesis message tracking
last_synthesis_time = time.time()

# Database for notification tracking
NOTIFICATION_DB = None

def export_agent_state(client, agent, skip_git=False):
    """Export agent state to data/agent/archive/ (timestamped) and data/agent/ (current)."""
    try:
        # Confirm export with user unless git is being skipped
        if not skip_git:
            response = input("Export agent state to files and stage with git? (y/n): ").lower().strip()
            if response not in ['y', 'yes']:
                logger.info("Agent export cancelled by user.")
                return
        else:
            logger.info("Exporting agent state (git staging disabled)")
        
        # Create directories if they don't exist
        os.makedirs("data/agent/archive", exist_ok=True)
        os.makedirs("data/agent", exist_ok=True)
        
        # Export agent data
        logger.info(f"Exporting agent {agent.id}. This takes some time...")
        agent_data = client.agents.export_file(agent_id=agent.id)
        
        # Save timestamped archive copy
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_file = os.path.join("data/agent/archive", f"void_{timestamp}.af")
        with open(archive_file, 'w', encoding='utf-8') as f:
            json.dump(agent_data, f, indent=2, ensure_ascii=False)
        
        # Save current agent state
        current_file = os.path.join("data/agent", "current.af")
        with open(current_file, 'w', encoding='utf-8') as f:
            json.dump(agent_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Agent exported to {archive_file} and {current_file}")
        
        # Git add only the current agent file (archive is ignored) unless skip_git is True
        if not skip_git:
            try:
                subprocess.run(["git", "add", current_file], check=True, capture_output=True)
                logger.info("Added current agent file to git staging")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to git add agent file: {e}")
        
    except Exception as e:
        logger.error(f"Failed to export agent: {e}")

def initialize_agent():
    logger.info("Starting agent initialization...")

    # Load configuration when needed
    letta_config = get_letta_config()
    
    # Create client with configuration
    client_params = {
        'token': letta_config['api_key'],
        'timeout': letta_config['timeout']
    }
    if letta_config.get('base_url'):
        client_params['base_url'] = letta_config['base_url']
    client = Letta(**client_params)

    # Get the configured void agent by ID
    logger.info("Loading void agent from config...")
    agent_id = letta_config['agent_id']
    
    try:
        agent = client.agents.retrieve(agent_id=agent_id)
        logger.info(f"Successfully loaded agent: {agent.name} ({agent_id})")
    except Exception as e:
        logger.error(f"Failed to load agent {agent_id}: {e}")
        logger.error("Please ensure the agent_id in config.yaml is correct")
        raise e
    
    # Export agent state
    logger.info("Exporting agent state...")
    export_agent_state(client, agent, skip_git=SKIP_GIT)
    
    # Log agent details
    logger.info(f"Agent details - ID: {agent.id}")
    logger.info(f"Agent name: {agent.name}")
    if hasattr(agent, 'llm_config'):
        logger.info(f"Agent model: {agent.llm_config.model}")
    if hasattr(agent, 'project_id') and agent.project_id:
        logger.info(f"Agent project_id: {agent.project_id}")
    if hasattr(agent, 'tools'):
        logger.info(f"Agent has {len(agent.tools)} tools")
        for tool in agent.tools[:3]:  # Show first 3 tools
            logger.info(f"  - Tool: {tool.name} (type: {tool.tool_type})")

    return agent


def process_mention(agent, atproto_client, notification_data, queue_filepath=None, testing_mode=False):
    """Process a mention and generate a reply using the Letta agent.
    
    Args:
        agent: The Letta agent instance
        atproto_client: The AT Protocol client
        notification_data: The notification data dictionary
        queue_filepath: Optional Path object to the queue file (for cleanup on halt)
    
    Returns:
        True: Successfully processed, remove from queue
        False: Failed but retryable, keep in queue
        None: Failed with non-retryable error, move to errors directory
        "no_reply": No reply was generated, move to no_reply directory
    """
    import uuid
    
    # Generate correlation ID for tracking this notification through the pipeline
    correlation_id = str(uuid.uuid4())[:8]
    
    try:
        logger.info(f"[{correlation_id}] Starting process_mention", extra={
            'correlation_id': correlation_id,
            'notification_type': type(notification_data).__name__
        })
        
        # Handle both dict and object inputs for backwards compatibility
        if isinstance(notification_data, dict):
            uri = notification_data['uri']
            mention_text = notification_data.get('record', {}).get('text', '')
            author_handle = notification_data['author']['handle']
            author_name = notification_data['author'].get('display_name') or author_handle
        else:
            # Legacy object access
            uri = notification_data.uri
            mention_text = notification_data.record.text if hasattr(notification_data.record, 'text') else ""
            author_handle = notification_data.author.handle
            author_name = notification_data.author.display_name or author_handle
        
        logger.info(f"[{correlation_id}] Processing mention from @{author_handle}", extra={
            'correlation_id': correlation_id,
            'author_handle': author_handle,
            'author_name': author_name,
            'mention_uri': uri,
            'mention_text_length': len(mention_text),
            'mention_preview': mention_text[:100] if mention_text else ''
        })

        # Retrieve the entire thread associated with the mention
        try:
            thread = atproto_client.app.bsky.feed.get_post_thread({
                'uri': uri,
                'parent_height': 40,
                'depth': 10
            })
        except Exception as e:
            error_str = str(e)
            # Check if this is a NotFound error
            if 'NotFound' in error_str or 'Post not found' in error_str:
                logger.warning(f"Post not found for URI {uri}, removing from queue")
                return True  # Return True to remove from queue
            else:
                # Re-raise other errors
                logger.error(f"Error fetching thread: {e}")
                raise

        # Get thread context as YAML string
        logger.debug("Converting thread to YAML string")
        try:
            thread_context = thread_to_yaml_string(thread)
            logger.debug(f"Thread context generated, length: {len(thread_context)} characters")
            
            # Check if stop command appears anywhere in the thread
            config = get_config()
            stop_command = config.get_stop_command()
            if stop_command in thread_context.lower():
                logger.info(f"Found {stop_command} in thread context, skipping this mention")
                return True  # Return True to remove from queue
            
            # Also check the mention text directly
            if stop_command in mention_text.lower():
                logger.info(f"Found {stop_command} in mention text, skipping this mention")
                return True  # Return True to remove from queue
            
            # Create a more informative preview by extracting meaningful content
            lines = thread_context.split('\n')
            meaningful_lines = []
            
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue
                    
                # Look for lines with actual content (not just structure)
                if any(keyword in line for keyword in ['text:', 'handle:', 'display_name:', 'created_at:', 'reply_count:', 'like_count:']):
                    meaningful_lines.append(line)
                    if len(meaningful_lines) >= 5:
                        break
            
            if meaningful_lines:
                preview = '\n'.join(meaningful_lines)
                logger.debug(f"Thread content preview:\n{preview}")
            else:
                # If no content fields found, just show it's a thread structure
                logger.debug(f"Thread structure generated ({len(thread_context)} chars)")
        except Exception as yaml_error:
            import traceback
            logger.error(f"Error converting thread to YAML: {yaml_error}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            logger.error(f"Thread type: {type(thread)}")
            if hasattr(thread, '__dict__'):
                logger.error(f"Thread attributes: {thread.__dict__}")
            # Try to continue with a simple context
            thread_context = f"Error processing thread context: {str(yaml_error)}"

        # Create a prompt for the Letta agent with thread context
        prompt = f"""You received a mention on Bluesky from @{author_handle} ({author_name or author_handle}).

MOST RECENT POST (the mention you're responding to):
"{mention_text}"

FULL THREAD CONTEXT:
```yaml
{thread_context}
```

The YAML above shows the complete conversation thread. The most recent post is the one mentioned above that you should respond to, but use the full thread context to understand the conversation flow.

To reply, use the add_post_to_bluesky_reply_thread tool:
- Each call creates one post (max 300 characters)
- For most responses, a single call is sufficient
- Only use multiple calls for threaded replies when:
  * The topic requires extended explanation that cannot fit in 300 characters
  * You're explicitly asked for a detailed/long response
  * The conversation naturally benefits from a structured multi-part answer
- Avoid unnecessary threads - be concise when possible"""

        # Extract all handles from notification and thread data
        all_handles = set()
        all_handles.update(extract_handles_from_data(notification_data))
        all_handles.update(extract_handles_from_data(thread.model_dump()))
        unique_handles = list(all_handles)
        
        logger.debug(f"Found {len(unique_handles)} unique handles in thread: {unique_handles}")
        
        # Check if any handles are in known_bots list
        from tools.bot_detection import check_known_bots, should_respond_to_bot_thread, CheckKnownBotsArgs
        import json
        
        try:
            # Check for known bots in thread
            bot_check_result = check_known_bots(unique_handles, agent)
            bot_check_data = json.loads(bot_check_result)
            
            # TEMPORARILY DISABLED: Bot detection causing issues with normal users
            # TODO: Re-enable after debugging why normal users are being flagged as bots
            if False:  # bot_check_data.get("bot_detected", False):
                detected_bots = bot_check_data.get("detected_bots", [])
                logger.info(f"Bot detected in thread: {detected_bots}")
                
                # Decide whether to respond (10% chance)
                if not should_respond_to_bot_thread():
                    logger.info(f"Skipping bot thread (90% skip rate). Detected bots: {detected_bots}")
                    # Return False to keep in queue for potential later processing
                    return False
                else:
                    logger.info(f"Responding to bot thread (10% response rate). Detected bots: {detected_bots}")
            else:
                logger.debug("Bot detection disabled - processing all notifications")
                
        except Exception as bot_check_error:
            logger.warning(f"Error checking for bots: {bot_check_error}")
            # Continue processing if bot check fails
        
        # Attach user blocks before agent call
        attached_handles = []
        if unique_handles:
            try:
                logger.debug(f"Attaching user blocks for handles: {unique_handles}")
                attach_result = attach_user_blocks(unique_handles, agent)
                attached_handles = unique_handles  # Track successfully attached handles
                logger.debug(f"Attach result: {attach_result}")
            except Exception as attach_error:
                logger.warning(f"Failed to attach user blocks: {attach_error}")
                # Continue without user blocks rather than failing completely

        # Get response from Letta agent
        # Format with Unicode characters
        title = f"MENTION FROM @{author_handle}"
        print(f"\n▶ {title}")
        print(f"  {'═' * len(title)}")
        # Indent the mention text
        for line in mention_text.split('\n'):
            print(f"  {line}")
        
        # Log prompt details to separate logger
        prompt_logger.debug(f"Full prompt being sent:\n{prompt}")
        
        # Log concise prompt info to main logger
        thread_handles_count = len(unique_handles)
        prompt_char_count = len(prompt)
        logger.debug(f"Sending to LLM: @{author_handle} mention | msg: \"{mention_text[:50]}...\" | context: {len(thread_context)} chars, {thread_handles_count} users | prompt: {prompt_char_count} chars")

        try:
            # Load configuration and create client when needed
            letta_config = get_letta_config()
            client_params = {
                'token': letta_config['api_key'],
                'timeout': letta_config['timeout']
            }
            if letta_config.get('base_url'):
                client_params['base_url'] = letta_config['base_url']
            client = Letta(**client_params)
            
            # Use streaming to avoid 524 timeout errors
            message_stream = client.agents.messages.create_stream(
                agent_id=agent.id,
                messages=[{"role": "user", "content": prompt}],
                stream_tokens=False,  # Step streaming only (faster than token streaming)
                max_steps=100
            )
            
            # Collect the streaming response
            all_messages = []
            for chunk in message_stream:
                # Log condensed chunk info
                if hasattr(chunk, 'message_type'):
                    if chunk.message_type == 'reasoning_message':
                        # Show full reasoning without truncation
                        if SHOW_REASONING:
                            # Format with Unicode characters
                            print("\n◆ Reasoning")
                            print("  ─────────")
                            # Indent reasoning lines
                            for line in chunk.reasoning.split('\n'):
                                print(f"  {line}")
                        else:
                            # Default log format (only when --reasoning is used due to log level)
                            # Format with Unicode characters
                            print("\n◆ Reasoning")
                            print("  ─────────")
                            # Indent reasoning lines
                            for line in chunk.reasoning.split('\n'):
                                print(f"  {line}")
                        
                        # Create ATProto record for reasoning (unless in testing mode)
                        if not testing_mode and hasattr(chunk, 'reasoning'):
                            try:
                                bsky_utils.create_reasoning_record(atproto_client, chunk.reasoning)
                            except Exception as e:
                                logger.debug(f"Failed to create reasoning record: {e}")
                    elif chunk.message_type == 'tool_call_message':
                        # Parse tool arguments for better display
                        tool_name = chunk.tool_call.name
                        
                        # Create ATProto record for tool call (unless in testing mode)
                        if not testing_mode:
                            try:
                                tool_call_id = chunk.tool_call.tool_call_id if hasattr(chunk.tool_call, 'tool_call_id') else None
                                bsky_utils.create_tool_call_record(
                                    atproto_client, 
                                    tool_name, 
                                    chunk.tool_call.arguments,
                                    tool_call_id
                                )
                            except Exception as e:
                                logger.debug(f"Failed to create tool call record: {e}")
                        
                        try:
                            args = json.loads(chunk.tool_call.arguments)
                            # Format based on tool type
                            if tool_name in ['add_post_to_bluesky_reply_thread', 'bluesky_reply']:
                                # Extract the text being posted
                                text = args.get('text', '')
                                if text:
                                    # Format with Unicode characters
                                    print("\n✎ Bluesky Post")
                                    print("  ────────────")
                                    # Indent post text
                                    for line in text.split('\n'):
                                        print(f"  {line}")
                                else:
                                    log_with_panel(chunk.tool_call.arguments[:150] + "...", f"Tool call: {tool_name}", "blue")
                            elif tool_name == 'archival_memory_search':
                                query = args.get('query', 'unknown')
                                global last_archival_query
                                last_archival_query = query
                                log_with_panel(f"query: \"{query}\"", f"Tool call: {tool_name}", "blue")
                            elif tool_name == 'archival_memory_insert':
                                content = args.get('content', '')
                                # Show the full content being inserted
                                log_with_panel(content, f"Tool call: {tool_name}", "blue")
                            elif tool_name == 'update_block':
                                label = args.get('label', 'unknown')
                                value_preview = str(args.get('value', ''))[:50] + "..." if len(str(args.get('value', ''))) > 50 else str(args.get('value', ''))
                                log_with_panel(f"{label}: \"{value_preview}\"", f"Tool call: {tool_name}", "blue")
                            else:
                                # Generic display for other tools
                                args_str = ', '.join(f"{k}={v}" for k, v in args.items() if k != 'request_heartbeat')
                                if len(args_str) > 150:
                                    args_str = args_str[:150] + "..."
                                log_with_panel(args_str, f"Tool call: {tool_name}", "blue")
                        except:
                            # Fallback to original format if parsing fails
                            log_with_panel(chunk.tool_call.arguments[:150] + "...", f"Tool call: {tool_name}", "blue")
                    elif chunk.message_type == 'tool_return_message':
                        # Enhanced tool result logging
                        tool_name = chunk.name
                        status = chunk.status
                        
                        if status == 'success':
                            # Try to show meaningful result info based on tool type
                            if hasattr(chunk, 'tool_return') and chunk.tool_return:
                                result_str = str(chunk.tool_return)
                                if tool_name == 'archival_memory_search':
                                    
                                    try:
                                        # Handle both string and list formats
                                        if isinstance(chunk.tool_return, str):
                                            # The string format is: "([{...}, {...}], count)"
                                            # We need to extract just the list part
                                            if chunk.tool_return.strip():
                                                # Find the list part between the first [ and last ]
                                                start_idx = chunk.tool_return.find('[')
                                                end_idx = chunk.tool_return.rfind(']')
                                                if start_idx != -1 and end_idx != -1:
                                                    list_str = chunk.tool_return[start_idx:end_idx+1]
                                                    # Use ast.literal_eval since this is Python literal syntax, not JSON
                                                    import ast
                                                    results = ast.literal_eval(list_str)
                                                else:
                                                    logger.warning("Could not find list in archival_memory_search result")
                                                    results = []
                                            else:
                                                logger.warning("Empty string returned from archival_memory_search")
                                                results = []
                                        else:
                                            # If it's already a list, use directly
                                            results = chunk.tool_return
                                        
                                        log_with_panel(f"Found {len(results)} memory entries", f"Tool result: {tool_name} ✓", "green")
                                        
                                        # Use the captured search query from the tool call
                                        search_query = last_archival_query
                                        
                                        # Combine all results into a single text block
                                        content_text = ""
                                        for i, entry in enumerate(results, 1):
                                            timestamp = entry.get('timestamp', 'N/A')
                                            content = entry.get('content', '')
                                            content_text += f"[{i}/{len(results)}] {timestamp}\n{content}\n\n"
                                        
                                        # Format with Unicode characters
                                        title = f"{search_query} ({len(results)} results)"
                                        print(f"\n⚙ {title}")
                                        print(f"  {'─' * len(title)}")
                                        # Indent content text
                                        for line in content_text.strip().split('\n'):
                                            print(f"  {line}")
                                        
                                    except Exception as e:
                                        logger.error(f"Error formatting archival memory results: {e}")
                                        log_with_panel(result_str[:100] + "...", f"Tool result: {tool_name} ✓", "green")
                                elif tool_name == 'add_post_to_bluesky_reply_thread':
                                    # Just show success for bluesky posts, the text was already shown in tool call
                                    log_with_panel("Post queued successfully", f"Bluesky Post ✓", "green")
                                elif tool_name == 'archival_memory_insert':
                                    # Skip archival memory insert results (always returns None)
                                    pass
                                elif tool_name == 'update_block':
                                    log_with_panel("Memory block updated", f"Tool result: {tool_name} ✓", "green")
                                else:
                                    # Generic success with preview
                                    preview = result_str[:100] + "..." if len(result_str) > 100 else result_str
                                    log_with_panel(preview, f"Tool result: {tool_name} ✓", "green")
                            else:
                                log_with_panel("Success", f"Tool result: {tool_name} ✓", "green")
                        elif status == 'error':
                            # Show error details
                            if tool_name == 'add_post_to_bluesky_reply_thread':
                                error_str = str(chunk.tool_return) if hasattr(chunk, 'tool_return') and chunk.tool_return else "Error occurred"
                                log_with_panel(error_str, f"Bluesky Post ✗", "red")
                            elif tool_name == 'archival_memory_insert':
                                # Skip archival memory insert errors too
                                pass
                            else:
                                error_preview = ""
                                if hasattr(chunk, 'tool_return') and chunk.tool_return:
                                    error_str = str(chunk.tool_return)
                                    error_preview = error_str[:100] + "..." if len(error_str) > 100 else error_str
                                    log_with_panel(f"Error: {error_preview}", f"Tool result: {tool_name} ✗", "red")
                                else:
                                    log_with_panel("Error occurred", f"Tool result: {tool_name} ✗", "red")
                        else:
                            logger.info(f"Tool result: {tool_name} - {status}")
                    elif chunk.message_type == 'assistant_message':
                        # Format with Unicode characters
                        print("\n▶ Assistant Response")
                        print("  ──────────────────")
                        # Indent response text
                        for line in chunk.content.split('\n'):
                            print(f"  {line}")
                    else:
                        # Filter out verbose message types
                        if chunk.message_type not in ['usage_statistics', 'stop_reason']:
                            logger.info(f"{chunk.message_type}: {str(chunk)[:150]}...")
                else:
                    logger.info(f"📦 Stream status: {chunk}")
                
                # Log full chunk for debugging
                logger.debug(f"Full streaming chunk: {chunk}")
                all_messages.append(chunk)
                if str(chunk) == 'done':
                    break
            
            # Convert streaming response to standard format for compatibility
            message_response = type('StreamingResponse', (), {
                'messages': [msg for msg in all_messages if hasattr(msg, 'message_type')]
            })()
        except Exception as api_error:
            import traceback
            error_str = str(api_error)
            logger.error(f"Letta API error: {api_error}")
            logger.error(f"Error type: {type(api_error).__name__}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            logger.error(f"Mention text was: {mention_text}")
            logger.error(f"Author: @{author_handle}")
            logger.error(f"URI: {uri}")
            
            
            # Try to extract more info from different error types
            if hasattr(api_error, 'response'):
                logger.error(f"Error response object exists")
                if hasattr(api_error.response, 'text'):
                    logger.error(f"Response text: {api_error.response.text}")
                if hasattr(api_error.response, 'json') and callable(api_error.response.json):
                    try:
                        logger.error(f"Response JSON: {api_error.response.json()}")
                    except:
                        pass
            
            # Check for specific error types
            if hasattr(api_error, 'status_code'):
                logger.error(f"API Status code: {api_error.status_code}")
                if hasattr(api_error, 'body'):
                    logger.error(f"API Response body: {api_error.body}")
                if hasattr(api_error, 'headers'):
                    logger.error(f"API Response headers: {api_error.headers}")
                
                if api_error.status_code == 413:
                    logger.error("413 Payload Too Large - moving to errors directory")
                    return None  # Move to errors directory - payload is too large to ever succeed
                elif api_error.status_code == 524:
                    logger.error("524 error - timeout from Cloudflare, will retry later")
                    return False  # Keep in queue for retry
            
            # Check if error indicates we should remove from queue
            if 'status_code: 413' in error_str or 'Payload Too Large' in error_str:
                logger.warning("Payload too large error, moving to errors directory")
                return None  # Move to errors directory - cannot be fixed by retry
            elif 'status_code: 524' in error_str:
                logger.warning("524 timeout error, keeping in queue for retry")
                return False  # Keep in queue for retry
            
            raise

        # Log successful response
        logger.debug("Successfully received response from Letta API")
        logger.debug(f"Number of messages in response: {len(message_response.messages) if hasattr(message_response, 'messages') else 'N/A'}")

        # Extract successful add_post_to_bluesky_reply_thread tool calls from the agent's response
        reply_candidates = []
        tool_call_results = {}  # Map tool_call_id to status
        ack_note = None  # Track any note from annotate_ack tool
        
        logger.debug(f"Processing {len(message_response.messages)} response messages...")
        
        # First pass: collect tool return statuses
        ignored_notification = False
        ignore_reason = ""
        ignore_category = ""
        
        for message in message_response.messages:
            if hasattr(message, 'tool_call_id') and hasattr(message, 'status') and hasattr(message, 'name'):
                if message.name == 'add_post_to_bluesky_reply_thread':
                    tool_call_results[message.tool_call_id] = message.status
                    logger.debug(f"Tool result: {message.tool_call_id} -> {message.status}")
                elif message.name == 'ignore_notification':
                    # Check if the tool was successful
                    if hasattr(message, 'tool_return') and message.status == 'success':
                        # Parse the return value to extract category and reason
                        result_str = str(message.tool_return)
                        if 'IGNORED_NOTIFICATION::' in result_str:
                            parts = result_str.split('::')
                            if len(parts) >= 3:
                                ignore_category = parts[1]
                                ignore_reason = parts[2]
                                ignored_notification = True
                                logger.info(f"🚫 Notification ignored - Category: {ignore_category}, Reason: {ignore_reason}")
                elif message.name == 'bluesky_reply':
                    logger.error("DEPRECATED TOOL DETECTED: bluesky_reply is no longer supported!")
                    logger.error("Please use add_post_to_bluesky_reply_thread instead.")
                    logger.error("Update the agent's tools using register_tools.py")
                    # Export agent state before terminating
                    export_agent_state(CLIENT, agent, skip_git=SKIP_GIT)
                    logger.info("=== BOT TERMINATED DUE TO DEPRECATED TOOL USE ===")
                    exit(1)
        
        # Second pass: process messages and check for successful tool calls
        for i, message in enumerate(message_response.messages, 1):
            # Log concise message info instead of full object
            msg_type = getattr(message, 'message_type', 'unknown')
            if hasattr(message, 'reasoning') and message.reasoning:
                logger.debug(f"  {i}. {msg_type}: {message.reasoning[:100]}...")
            elif hasattr(message, 'tool_call') and message.tool_call:
                tool_name = message.tool_call.name
                logger.debug(f"  {i}. {msg_type}: {tool_name}")
            elif hasattr(message, 'tool_return'):
                tool_name = getattr(message, 'name', 'unknown_tool')
                return_preview = str(message.tool_return)[:100] if message.tool_return else "None"
                status = getattr(message, 'status', 'unknown')
                logger.debug(f"  {i}. {msg_type}: {tool_name} -> {return_preview}... (status: {status})")
            elif hasattr(message, 'text'):
                logger.debug(f"  {i}. {msg_type}: {message.text[:100]}...")
            else:
                logger.debug(f"  {i}. {msg_type}: <no content>")

            # Check for halt_activity tool call
            if hasattr(message, 'tool_call') and message.tool_call:
                if message.tool_call.name == 'halt_activity':
                    logger.info("🛑 HALT_ACTIVITY TOOL CALLED - TERMINATING BOT")
                    try:
                        args = json.loads(message.tool_call.arguments)
                        reason = args.get('reason', 'Agent requested halt')
                        logger.info(f"Halt reason: {reason}")
                    except:
                        logger.info("Halt reason: <unable to parse>")
                    
                    # Delete the queue file before terminating
                    if queue_filepath and queue_filepath.exists():
                        queue_filepath.unlink()
                        logger.info(f"Deleted queue file: {queue_filepath.name}")
                        
                        # Also mark as processed to avoid reprocessing
                        if NOTIFICATION_DB:
                            NOTIFICATION_DB.mark_processed(notification_data.get('uri', ''), status='processed')
                        else:
                            processed_uris = load_processed_notifications()
                            processed_uris.add(notification_data.get('uri', ''))
                            save_processed_notifications(processed_uris)
                    
                    # Export agent state before terminating
                    export_agent_state(CLIENT, agent, skip_git=SKIP_GIT)
                    
                    # Exit the program
                    logger.info("=== BOT TERMINATED BY AGENT ===")
                    exit(0)
            
            # Check for deprecated bluesky_reply tool
            if hasattr(message, 'tool_call') and message.tool_call:
                if message.tool_call.name == 'bluesky_reply':
                    logger.error("DEPRECATED TOOL DETECTED: bluesky_reply is no longer supported!")
                    logger.error("Please use add_post_to_bluesky_reply_thread instead.")
                    logger.error("Update the agent's tools using register_tools.py")
                    # Export agent state before terminating
                    export_agent_state(CLIENT, agent, skip_git=SKIP_GIT)
                    logger.info("=== BOT TERMINATED DUE TO DEPRECATED TOOL USE ===")
                    exit(1)
                
                # Collect annotate_ack tool calls
                elif message.tool_call.name == 'annotate_ack':
                    try:
                        args = json.loads(message.tool_call.arguments)
                        note = args.get('note', '')
                        if note:
                            ack_note = note
                            logger.debug(f"Found annotate_ack with note: {note[:50]}...")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse annotate_ack arguments: {e}")
                
                # Collect add_post_to_bluesky_reply_thread tool calls - only if they were successful
                elif message.tool_call.name == 'add_post_to_bluesky_reply_thread':
                    tool_call_id = message.tool_call.tool_call_id
                    tool_status = tool_call_results.get(tool_call_id, 'unknown')
                    
                    if tool_status == 'success':
                        try:
                            args = json.loads(message.tool_call.arguments)
                            reply_text = args.get('text', '')
                            reply_lang = args.get('lang', 'en-US')
                            
                            if reply_text:  # Only add if there's actual content
                                reply_candidates.append((reply_text, reply_lang))
                                logger.debug(f"Found successful add_post_to_bluesky_reply_thread candidate: {reply_text[:50]}... (lang: {reply_lang})")
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse tool call arguments: {e}")
                    elif tool_status == 'error':
                        logger.debug(f"Skipping failed add_post_to_bluesky_reply_thread tool call (status: error)")
                    else:
                        logger.warning(f"⚠️ Skipping add_post_to_bluesky_reply_thread tool call with unknown status: {tool_status}")

        # Check for conflicting tool calls
        if reply_candidates and ignored_notification:
            logger.error(f"⚠️ CONFLICT: Agent called both add_post_to_bluesky_reply_thread and ignore_notification!")
            logger.error(f"Reply candidates: {len(reply_candidates)}, Ignore reason: {ignore_reason}")
            logger.warning("Item will be left in queue for manual review")
            # Return False to keep in queue
            return False
        
        if reply_candidates:
            # Aggregate reply posts into a thread
            reply_messages = []
            reply_langs = []
            for text, lang in reply_candidates:
                reply_messages.append(text)
                reply_langs.append(lang)
            
            # Use the first language for the entire thread (could be enhanced later)
            reply_lang = reply_langs[0] if reply_langs else 'en-US'
            
            logger.debug(f"Found {len(reply_candidates)} add_post_to_bluesky_reply_thread calls, building thread")
            
            # Display the generated reply thread
            if len(reply_messages) == 1:
                content = reply_messages[0]
                title = f"Reply to @{author_handle}"
            else:
                content = "\n\n".join([f"{j}. {msg}" for j, msg in enumerate(reply_messages, 1)])
                title = f"Reply Thread to @{author_handle} ({len(reply_messages)} messages)"
            
            # Format with Unicode characters
            print(f"\n✎ {title}")
            print(f"  {'─' * len(title)}")
            # Indent content lines
            for line in content.split('\n'):
                print(f"  {line}")

            # Send the reply(s) with language (unless in testing mode)
            if testing_mode:
                logger.info("TESTING MODE: Skipping actual Bluesky post")
                response = True  # Simulate success
            else:
                if len(reply_messages) == 1:
                    # Single reply - use existing function
                    cleaned_text = bsky_utils.remove_outside_quotes(reply_messages[0])
                    logger.info(f"Sending single reply: {cleaned_text[:50]}... (lang: {reply_lang})")
                    response = bsky_utils.reply_to_notification(
                        client=atproto_client,
                        notification=notification_data,
                        reply_text=cleaned_text,
                        lang=reply_lang,
                        correlation_id=correlation_id
                    )
                else:
                    # Multiple replies - use new threaded function
                    cleaned_messages = [bsky_utils.remove_outside_quotes(msg) for msg in reply_messages]
                    logger.info(f"Sending threaded reply with {len(cleaned_messages)} messages (lang: {reply_lang})")
                    response = bsky_utils.reply_with_thread_to_notification(
                        client=atproto_client,
                        notification=notification_data,
                        reply_messages=cleaned_messages,
                        lang=reply_lang,
                        correlation_id=correlation_id
                    )

            if response:
                logger.info(f"[{correlation_id}] Successfully replied to @{author_handle}", extra={
                    'correlation_id': correlation_id,
                    'author_handle': author_handle,
                    'reply_count': len(reply_messages)
                })
                
                # Acknowledge the post we're replying to with stream.thought.ack
                try:
                    post_uri = notification_data.get('uri')
                    post_cid = notification_data.get('cid')
                    
                    if post_uri and post_cid:
                        ack_result = bsky_utils.acknowledge_post(
                            client=atproto_client,
                            post_uri=post_uri,
                            post_cid=post_cid,
                            note=ack_note
                        )
                        if ack_result:
                            if ack_note:
                                logger.info(f"Successfully acknowledged post from @{author_handle} with stream.thought.ack (note: \"{ack_note[:50]}...\")")
                            else:
                                logger.info(f"Successfully acknowledged post from @{author_handle} with stream.thought.ack")
                        else:
                            logger.warning(f"Failed to acknowledge post from @{author_handle}")
                    else:
                        logger.warning(f"Missing URI or CID for acknowledging post from @{author_handle}")
                except Exception as e:
                    logger.error(f"Error acknowledging post from @{author_handle}: {e}")
                    # Don't fail the entire operation if acknowledgment fails
                
                return True
            else:
                logger.error(f"Failed to send reply to @{author_handle}")
                return False
        else:
            # Check if notification was explicitly ignored
            if ignored_notification:
                logger.info(f"[{correlation_id}] Notification from @{author_handle} was explicitly ignored (category: {ignore_category})", extra={
                    'correlation_id': correlation_id,
                    'author_handle': author_handle,
                    'ignore_category': ignore_category
                })
                return "ignored"
            else:
                logger.warning(f"[{correlation_id}] No reply generated for mention from @{author_handle}, moving to no_reply folder", extra={
                    'correlation_id': correlation_id,
                    'author_handle': author_handle
                })
                return "no_reply"

    except Exception as e:
        logger.error(f"[{correlation_id}] Error processing mention: {e}", extra={
            'correlation_id': correlation_id,
            'error': str(e),
            'error_type': type(e).__name__,
            'author_handle': author_handle if 'author_handle' in locals() else 'unknown'
        })
        return False
    finally:
        # Detach user blocks after agent response (success or failure)
        if 'attached_handles' in locals() and attached_handles:
            try:
                logger.info(f"Detaching user blocks for handles: {attached_handles}")
                detach_result = detach_user_blocks(attached_handles, agent)
                logger.debug(f"Detach result: {detach_result}")
            except Exception as detach_error:
                logger.warning(f"Failed to detach user blocks: {detach_error}")


def notification_to_dict(notification):
    """Convert a notification object to a dictionary for JSON serialization."""
    return {
        'uri': notification.uri,
        'cid': notification.cid,
        'reason': notification.reason,
        'is_read': notification.is_read,
        'indexed_at': notification.indexed_at,
        'author': {
            'handle': notification.author.handle,
            'display_name': notification.author.display_name,
            'did': notification.author.did
        },
        'record': {
            'text': getattr(notification.record, 'text', '') if hasattr(notification, 'record') else ''
        }
    }


def load_processed_notifications():
    """Load the set of processed notification URIs from database."""
    global NOTIFICATION_DB
    if NOTIFICATION_DB:
        return NOTIFICATION_DB.get_processed_uris(limit=MAX_PROCESSED_NOTIFICATIONS)
    return set()


def save_processed_notifications(processed_set):
    """Save the set of processed notification URIs to database."""
    # This is now handled by marking individual notifications in the DB
    # Keeping function for compatibility but it doesn't need to do anything
    pass


def save_notification_to_queue(notification, is_priority=None):
    """Save a notification to the queue directory with priority-based filename."""
    try:
        global NOTIFICATION_DB
        
        # Handle both notification objects and dicts
        if isinstance(notification, dict):
            notif_dict = notification
            notification_uri = notification.get('uri')
        else:
            notif_dict = notification_to_dict(notification)
            notification_uri = notification.uri
        
        # Check if already processed (using database if available)
        if NOTIFICATION_DB:
            if NOTIFICATION_DB.is_processed(notification_uri):
                logger.debug(f"Notification already processed (DB): {notification_uri}")
                return False
            # Add to database - if this fails, don't queue the notification
            if not NOTIFICATION_DB.add_notification(notif_dict):
                logger.warning(f"Failed to add notification to database, skipping: {notification_uri}")
                return False
        else:
            # Fall back to old JSON method
            processed_uris = load_processed_notifications()
            if notification_uri in processed_uris:
                logger.debug(f"Notification already processed: {notification_uri}")
                return False

        # Create JSON string
        notif_json = json.dumps(notif_dict, sort_keys=True)

        # Generate hash for filename (to avoid duplicates)
        notif_hash = hashlib.sha256(notif_json.encode()).hexdigest()[:16]

        # Determine priority based on author handle or explicit priority
        if is_priority is not None:
            priority_prefix = "0_" if is_priority else "1_"
        else:
            if isinstance(notification, dict):
                author_handle = notification.get('author', {}).get('handle', '')
            else:
                author_handle = getattr(notification.author, 'handle', '') if hasattr(notification, 'author') else ''
            # Prioritize cameron.pfiffer.org responses
            priority_prefix = "0_" if author_handle == "cameron.pfiffer.org" else "1_"

        # Create filename with priority, timestamp and hash
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        reason = notif_dict.get('reason', 'unknown')
        filename = f"{priority_prefix}{timestamp}_{reason}_{notif_hash}.json"
        filepath = QUEUE_DIR / filename

        # Check if this notification URI is already in the queue
        for existing_file in QUEUE_DIR.glob("*.json"):
            if existing_file.name == "processed_notifications.json":
                continue
            try:
                with open(existing_file, 'r') as f:
                    existing_data = json.load(f)
                    if existing_data.get('uri') == notification_uri:
                        logger.debug(f"Notification already queued (URI: {notification_uri})")
                        return False
            except:
                continue

        # Write to file
        with open(filepath, 'w') as f:
            json.dump(notif_dict, f, indent=2)

        priority_label = "HIGH PRIORITY" if priority_prefix == "0_" else "normal"
        logger.info(f"Queued notification ({priority_label}): {filename}")
        return True

    except Exception as e:
        logger.error(f"Error saving notification to queue: {e}")
        return False


def load_and_process_queued_notifications(agent, atproto_client, testing_mode=False):
    """Load and process all notifications from the queue in priority order."""
    try:
        # Get all JSON files in queue directory (excluding processed_notifications.json)
        # Files are sorted by name, which puts priority files first (0_ prefix before 1_ prefix)
        all_queue_files = sorted([f for f in QUEUE_DIR.glob("*.json") if f.name != "processed_notifications.json"])

        # Filter out and delete like notifications immediately
        queue_files = []
        likes_deleted = 0
        
        for filepath in all_queue_files:
            try:
                with open(filepath, 'r') as f:
                    notif_data = json.load(f)
                
                # If it's a like, delete it immediately and don't process
                if notif_data.get('reason') == 'like':
                    filepath.unlink()
                    likes_deleted += 1
                    logger.debug(f"Deleted like notification: {filepath.name}")
                else:
                    queue_files.append(filepath)
            except Exception as e:
                logger.warning(f"Error checking notification file {filepath.name}: {e}")
                queue_files.append(filepath)  # Keep it in case it's valid
        
        if likes_deleted > 0:
            logger.info(f"Deleted {likes_deleted} like notifications from queue")

        if not queue_files:
            return

        logger.info(f"Processing {len(queue_files)} queued notifications")
        
        # Log current statistics
        elapsed_time = time.time() - start_time
        total_messages = sum(message_counters.values())
        messages_per_minute = (total_messages / elapsed_time * 60) if elapsed_time > 0 else 0
        
        logger.info(f"Session stats: {total_messages} total messages ({message_counters['mentions']} mentions, {message_counters['replies']} replies, {message_counters['follows']} follows) | {messages_per_minute:.1f} msg/min")

        for i, filepath in enumerate(queue_files, 1):
            # Determine if this is a priority notification
            is_priority = filepath.name.startswith("0_")
            
            # Check for new notifications periodically during queue processing
            # Also check immediately after processing each priority item
            should_check_notifications = (i % CHECK_NEW_NOTIFICATIONS_EVERY_N_ITEMS == 0 and i > 1)
            
            # If we just processed a priority item, immediately check for new priority notifications
            if is_priority and i > 1:
                should_check_notifications = True
            
            if should_check_notifications:
                logger.info(f"🔄 Checking for new notifications (processed {i-1}/{len(queue_files)} queue items)")
                try:
                    # Fetch and queue new notifications without processing them
                    new_count = fetch_and_queue_new_notifications(atproto_client)
                    
                    if new_count > 0:
                        logger.info(f"Added {new_count} new notifications to queue")
                        # Reload the queue files to include the new items
                        updated_queue_files = sorted([f for f in QUEUE_DIR.glob("*.json") if f.name != "processed_notifications.json"])
                        queue_files = updated_queue_files
                        logger.info(f"Queue updated: now {len(queue_files)} total items")
                except Exception as e:
                    logger.error(f"Error checking for new notifications: {e}")
            
            priority_label = " [PRIORITY]" if is_priority else ""
            logger.info(f"Processing queue file {i}/{len(queue_files)}{priority_label}: {filepath.name}")
            try:
                # Load notification data
                with open(filepath, 'r') as f:
                    notif_data = json.load(f)

                # Process based on type using dict data directly
                success = False
                if notif_data['reason'] == "mention":
                    success = process_mention(agent, atproto_client, notif_data, queue_filepath=filepath, testing_mode=testing_mode)
                    if success:
                        message_counters['mentions'] += 1
                elif notif_data['reason'] == "reply":
                    success = process_mention(agent, atproto_client, notif_data, queue_filepath=filepath, testing_mode=testing_mode)
                    if success:
                        message_counters['replies'] += 1
                elif notif_data['reason'] == "follow":
                    author_handle = notif_data['author']['handle']
                    author_display_name = notif_data['author'].get('display_name', 'no display name')
                    follow_update = f"@{author_handle} ({author_display_name}) started following you."
                    follow_message = f"Update: {follow_update}"
                    logger.info(f"Notifying agent about new follower: @{author_handle} | prompt: {len(follow_message)} chars")
                    
                    # Load configuration and create client when needed
                    letta_config = get_letta_config()
                    client_params = {
                        'token': letta_config['api_key'],
                        'timeout': letta_config['timeout']
                    }
                    if letta_config.get('base_url'):
                        client_params['base_url'] = letta_config['base_url']
                    client = Letta(**client_params)
                    
                    client.agents.messages.create(
                        agent_id = agent.id,
                        messages = [{"role":"user", "content": follow_message}]
                    )
                    success = True  # Follow updates are always successful
                    if success:
                        message_counters['follows'] += 1
                elif notif_data['reason'] == "repost":
                    # Skip reposts silently
                    success = True  # Skip reposts but mark as successful to remove from queue
                    if success:
                        message_counters['reposts_skipped'] += 1
                elif notif_data['reason'] == "like":
                    # Skip likes silently
                    success = True  # Skip likes but mark as successful to remove from queue
                    if success:
                        message_counters.setdefault('likes_skipped', 0)
                        message_counters['likes_skipped'] += 1
                else:
                    logger.warning(f"Unknown notification type: {notif_data['reason']}")
                    success = True  # Remove unknown types from queue

                # Handle file based on processing result
                if success:
                    if testing_mode:
                        logger.info(f"TESTING MODE: Keeping queue file: {filepath.name}")
                    else:
                        filepath.unlink()
                        logger.info(f"Successfully processed and removed: {filepath.name}")
                        
                        # Mark as processed to avoid reprocessing
                        if NOTIFICATION_DB:
                            NOTIFICATION_DB.mark_processed(notif_data['uri'], status='processed')
                        else:
                            processed_uris = load_processed_notifications()
                            processed_uris.add(notif_data['uri'])
                            save_processed_notifications(processed_uris)
                    
                elif success is None:  # Special case for moving to error directory
                    error_path = QUEUE_ERROR_DIR / filepath.name
                    filepath.rename(error_path)
                    logger.warning(f"Moved {filepath.name} to errors directory")
                    
                    # Also mark as processed to avoid retrying
                    if NOTIFICATION_DB:
                        NOTIFICATION_DB.mark_processed(notif_data['uri'], status='error')
                    else:
                        processed_uris = load_processed_notifications()
                        processed_uris.add(notif_data['uri'])
                        save_processed_notifications(processed_uris)
                    
                elif success == "no_reply":  # Special case for moving to no_reply directory
                    no_reply_path = QUEUE_NO_REPLY_DIR / filepath.name
                    filepath.rename(no_reply_path)
                    logger.info(f"Moved {filepath.name} to no_reply directory")
                    
                    # Also mark as processed to avoid retrying
                    if NOTIFICATION_DB:
                        NOTIFICATION_DB.mark_processed(notif_data['uri'], status='error')
                    else:
                        processed_uris = load_processed_notifications()
                        processed_uris.add(notif_data['uri'])
                        save_processed_notifications(processed_uris)
                    
                elif success == "ignored":  # Special case for explicitly ignored notifications
                    # For ignored notifications, we just delete them (not move to no_reply)
                    filepath.unlink()
                    logger.info(f"🚫 Deleted ignored notification: {filepath.name}")
                    
                    # Also mark as processed to avoid retrying
                    if NOTIFICATION_DB:
                        NOTIFICATION_DB.mark_processed(notif_data['uri'], status='error')
                    else:
                        processed_uris = load_processed_notifications()
                        processed_uris.add(notif_data['uri'])
                        save_processed_notifications(processed_uris)
                    
                else:
                    logger.warning(f"⚠️  Failed to process {filepath.name}, keeping in queue for retry")

            except Exception as e:
                logger.error(f"💥 Error processing queued notification {filepath.name}: {e}")
                # Keep the file for retry later

    except Exception as e:
        logger.error(f"Error loading queued notifications: {e}")


def fetch_and_queue_new_notifications(atproto_client):
    """Fetch new notifications and queue them without processing."""
    try:
        global NOTIFICATION_DB
        
        # Get current time for marking notifications as seen
        logger.debug("Getting current time for notification marking...")
        last_seen_at = atproto_client.get_current_time_iso()
        
        # Get timestamp of last processed notification for filtering
        last_processed_time = None
        if NOTIFICATION_DB:
            last_processed_time = NOTIFICATION_DB.get_latest_processed_time()
            if last_processed_time:
                logger.debug(f"Last processed notification was at: {last_processed_time}")

        # Fetch ALL notifications using pagination
        all_notifications = []
        cursor = None
        page_count = 0
        max_pages = 20  # Safety limit to prevent infinite loops
        
        while page_count < max_pages:
            try:
                # Fetch notifications page
                if cursor:
                    notifications_response = atproto_client.app.bsky.notification.list_notifications(
                        params={'cursor': cursor, 'limit': 100}
                    )
                else:
                    notifications_response = atproto_client.app.bsky.notification.list_notifications(
                        params={'limit': 100}
                    )
                
                page_count += 1
                page_notifications = notifications_response.notifications
                
                if not page_notifications:
                    break
                
                all_notifications.extend(page_notifications)
                
                # Check if there are more pages
                cursor = getattr(notifications_response, 'cursor', None)
                if not cursor:
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching notifications page {page_count}: {e}")
                break
        
        # Now process all fetched notifications
        new_count = 0
        if all_notifications:
            logger.info(f"📥 Fetched {len(all_notifications)} total notifications from API")
            
            # Mark as seen first
            try:
                atproto_client.app.bsky.notification.update_seen(
                    data={'seenAt': last_seen_at}
                )
                logger.debug(f"Marked {len(all_notifications)} notifications as seen at {last_seen_at}")
            except Exception as e:
                logger.error(f"Error marking notifications as seen: {e}")
            
            # Debug counters
            skipped_read = 0
            skipped_likes = 0
            skipped_processed = 0
            skipped_old_timestamp = 0
            processed_uris = load_processed_notifications()
            
            # Queue all new notifications (except likes)
            for notif in all_notifications:
                # Skip if older than last processed (when we have timestamp filtering)
                if last_processed_time and hasattr(notif, 'indexed_at'):
                    if notif.indexed_at <= last_processed_time:
                        skipped_old_timestamp += 1
                        logger.debug(f"Skipping old notification (indexed_at {notif.indexed_at} <= {last_processed_time})")
                        continue
                
                # Debug: Log is_read status but DON'T skip based on it
                if hasattr(notif, 'is_read') and notif.is_read:
                    skipped_read += 1
                    logger.debug(f"Notification has is_read=True (but processing anyway): {notif.uri if hasattr(notif, 'uri') else 'unknown'}")
                
                # Skip likes
                if hasattr(notif, 'reason') and notif.reason == 'like':
                    skipped_likes += 1
                    continue
                    
                notif_dict = notif.model_dump() if hasattr(notif, 'model_dump') else notif
                
                # Skip likes in dict form too
                if notif_dict.get('reason') == 'like':
                    continue
                
                # Check if already processed
                notif_uri = notif_dict.get('uri', '')
                if notif_uri in processed_uris:
                    skipped_processed += 1
                    logger.debug(f"Skipping already processed: {notif_uri}")
                    continue
                
                # Check if it's a priority notification
                is_priority = False
                
                # Priority for cameron.pfiffer.org notifications
                author_handle = notif_dict.get('author', {}).get('handle', '')
                if author_handle == "cameron.pfiffer.org":
                    is_priority = True
                
                # Also check for priority keywords in mentions
                if notif_dict.get('reason') == 'mention':
                    # Get the mention text to check for priority keywords
                    record = notif_dict.get('record', {})
                    text = record.get('text', '')
                    if any(keyword in text.lower() for keyword in ['urgent', 'priority', 'important', 'emergency']):
                        is_priority = True
                
                if save_notification_to_queue(notif_dict, is_priority=is_priority):
                    new_count += 1
                    logger.debug(f"Queued notification from @{author_handle}: {notif_dict.get('reason', 'unknown')}")
            
            # Log summary of filtering
            logger.info(f"📊 Notification processing summary:")
            logger.info(f"  • Total fetched: {len(all_notifications)}")
            logger.info(f"  • Had is_read=True: {skipped_read} (not skipped)")
            logger.info(f"  • Skipped (likes): {skipped_likes}")
            logger.info(f"  • Skipped (old timestamp): {skipped_old_timestamp}")
            logger.info(f"  • Skipped (already processed): {skipped_processed}")
            logger.info(f"  • Queued for processing: {new_count}")
        else:
            logger.debug("No new notifications to queue")
            
        return new_count
            
    except Exception as e:
        logger.error(f"Error fetching and queueing notifications: {e}")
        return 0


def process_notifications(agent, atproto_client, testing_mode=False):
    """Fetch new notifications, queue them, and process the queue."""
    try:
        # Fetch and queue new notifications
        new_count = fetch_and_queue_new_notifications(atproto_client)
        
        if new_count > 0:
            logger.info(f"Found {new_count} new notifications to process")

        # Now process the entire queue (old + new notifications)
        load_and_process_queued_notifications(agent, atproto_client, testing_mode)

    except Exception as e:
        logger.error(f"Error processing notifications: {e}")


def send_synthesis_message(client: Letta, agent_id: str, atproto_client=None) -> None:
    """
    Send a synthesis message to the agent every 10 minutes.
    This prompts the agent to synthesize its recent experiences.
    
    Args:
        client: Letta client
        agent_id: Agent ID to send synthesis to
        atproto_client: Optional AT Protocol client for posting synthesis results
    """
    # Track attached temporal blocks for cleanup
    attached_temporal_labels = []
    
    try:
        logger.info("🧠 Preparing synthesis with temporal journal blocks")
        
        # Attach temporal blocks before synthesis
        success, attached_temporal_labels = attach_temporal_blocks(client, agent_id)
        if not success:
            logger.warning("Failed to attach some temporal blocks, continuing with synthesis anyway")
        
        # Create enhanced synthesis prompt using configuration
        today = date.today()
        config = get_config()
        synthesis_prompt = generate_synthesis_prompt(config._config, today)
        
        logger.info("🧠 Sending enhanced synthesis prompt to agent")
        
        # Send synthesis message with streaming to show tool use
        message_stream = client.agents.messages.create_stream(
            agent_id=agent_id,
            messages=[{"role": "user", "content": synthesis_prompt}],
            stream_tokens=False,
            max_steps=100
        )
        
        # Track synthesis content for potential posting
        synthesis_posts = []
        ack_note = None
        
        # Process the streaming response
        for chunk in message_stream:
            if hasattr(chunk, 'message_type'):
                if chunk.message_type == 'reasoning_message':
                    if SHOW_REASONING:
                        print("\n◆ Reasoning")
                        print("  ─────────")
                        for line in chunk.reasoning.split('\n'):
                            print(f"  {line}")
                    
                    # Create ATProto record for reasoning (if we have atproto client)
                    if atproto_client and hasattr(chunk, 'reasoning'):
                        try:
                            bsky_utils.create_reasoning_record(atproto_client, chunk.reasoning)
                        except Exception as e:
                            logger.debug(f"Failed to create reasoning record during synthesis: {e}")
                elif chunk.message_type == 'tool_call_message':
                    tool_name = chunk.tool_call.name
                    
                    # Create ATProto record for tool call (if we have atproto client)
                    if atproto_client:
                        try:
                            tool_call_id = chunk.tool_call.tool_call_id if hasattr(chunk.tool_call, 'tool_call_id') else None
                            bsky_utils.create_tool_call_record(
                                atproto_client,
                                tool_name,
                                chunk.tool_call.arguments,
                                tool_call_id
                            )
                        except Exception as e:
                            logger.debug(f"Failed to create tool call record during synthesis: {e}")
                    try:
                        args = json.loads(chunk.tool_call.arguments)
                        if tool_name == 'archival_memory_search':
                            query = args.get('query', 'unknown')
                            log_with_panel(f"query: \"{query}\"", f"Tool call: {tool_name}", "blue")
                        elif tool_name == 'archival_memory_insert':
                            content = args.get('content', '')
                            log_with_panel(content[:200] + "..." if len(content) > 200 else content, f"Tool call: {tool_name}", "blue")
                        elif tool_name == 'update_block':
                            label = args.get('label', 'unknown')
                            value_preview = str(args.get('value', ''))[:100] + "..." if len(str(args.get('value', ''))) > 100 else str(args.get('value', ''))
                            log_with_panel(f"{label}: \"{value_preview}\"", f"Tool call: {tool_name}", "blue")
                        elif tool_name == 'annotate_ack':
                            note = args.get('note', '')
                            if note:
                                ack_note = note
                                log_with_panel(f"note: \"{note[:100]}...\"" if len(note) > 100 else f"note: \"{note}\"", f"Tool call: {tool_name}", "blue")
                        elif tool_name == 'add_post_to_bluesky_reply_thread':
                            text = args.get('text', '')
                            synthesis_posts.append(text)
                            log_with_panel(f"text: \"{text[:100]}...\"" if len(text) > 100 else f"text: \"{text}\"", f"Tool call: {tool_name}", "blue")
                        else:
                            args_str = ', '.join(f"{k}={v}" for k, v in args.items() if k != 'request_heartbeat')
                            if len(args_str) > 150:
                                args_str = args_str[:150] + "..."
                            log_with_panel(args_str, f"Tool call: {tool_name}", "blue")
                    except:
                        log_with_panel(chunk.tool_call.arguments[:150] + "...", f"Tool call: {tool_name}", "blue")
                elif chunk.message_type == 'tool_return_message':
                    if chunk.status == 'success':
                        log_with_panel("Success", f"Tool result: {chunk.name} ✓", "green")
                    else:
                        log_with_panel("Error", f"Tool result: {chunk.name} ✗", "red")
                elif chunk.message_type == 'assistant_message':
                    print("\n▶ Synthesis Response")
                    print("  ──────────────────")
                    for line in chunk.content.split('\n'):
                        print(f"  {line}")
            
            if str(chunk) == 'done':
                break
        
        logger.info("🧠 Synthesis message processed successfully")
        
        # Handle synthesis acknowledgments if we have an atproto client
        if atproto_client and ack_note:
            try:
                result = bsky_utils.create_synthesis_ack(atproto_client, ack_note)
                if result:
                    logger.info(f"✓ Created synthesis acknowledgment: {ack_note[:50]}...")
                else:
                    logger.warning("Failed to create synthesis acknowledgment")
            except Exception as e:
                logger.error(f"Error creating synthesis acknowledgment: {e}")
        
        # Handle synthesis posts if any were generated
        if atproto_client and synthesis_posts:
            try:
                for post_text in synthesis_posts:
                    cleaned_text = bsky_utils.remove_outside_quotes(post_text)
                    response = bsky_utils.send_post(atproto_client, cleaned_text)
                    if response:
                        logger.info(f"✓ Posted synthesis content: {cleaned_text[:50]}...")
                    else:
                        logger.warning(f"Failed to post synthesis content: {cleaned_text[:50]}...")
            except Exception as e:
                logger.error(f"Error posting synthesis content: {e}")
        
    except Exception as e:
        logger.error(f"Error sending synthesis message: {e}")
    finally:
        # Always detach temporal blocks after synthesis
        if attached_temporal_labels:
            logger.info("🧠 Detaching temporal journal blocks after synthesis")
            detach_success = detach_temporal_blocks(client, agent_id, attached_temporal_labels)
            if not detach_success:
                logger.warning("Some temporal blocks may not have been detached properly")


def periodic_user_block_cleanup(client: Letta, agent_id: str) -> None:
    """
    Detach all user blocks from the agent to prevent memory bloat.
    This should be called periodically to ensure clean state.
    """
    try:
        # Get all blocks attached to the agent
        attached_blocks = client.agents.blocks.list(agent_id=agent_id)
        
        user_blocks_to_detach = []
        for block in attached_blocks:
            if hasattr(block, 'label') and block.label.startswith('user_'):
                user_blocks_to_detach.append({
                    'label': block.label,
                    'id': block.id
                })
        
        if not user_blocks_to_detach:
            logger.debug("No user blocks found to detach during periodic cleanup")
            return
            
        # Detach each user block
        detached_count = 0
        for block_info in user_blocks_to_detach:
            try:
                client.agents.blocks.detach(
                    agent_id=agent_id,
                    block_id=str(block_info['id'])
                )
                detached_count += 1
                logger.debug(f"Detached user block: {block_info['label']}")
            except Exception as e:
                logger.warning(f"Failed to detach block {block_info['label']}: {e}")
        
        if detached_count > 0:
            logger.info(f"Periodic cleanup: Detached {detached_count} user blocks")
            
    except Exception as e:
        logger.error(f"Error during periodic user block cleanup: {e}")


def attach_temporal_blocks(client: Letta, agent_id: str) -> tuple:
    """
    Attach temporal journal blocks (day, month, year) to the agent for synthesis.
    Creates blocks if they don't exist.
    
    Returns:
        Tuple of (success: bool, attached_labels: list)
    """
    try:
        today = date.today()
        
        # Generate temporal block labels using configuration
        config = get_config()
        temporal_labels = generate_temporal_block_labels(config._config, today)
        attached_labels = []
        
        # Get current blocks attached to agent
        current_blocks = client.agents.blocks.list(agent_id=agent_id)
        current_block_labels = {block.label for block in current_blocks}
        current_block_ids = {str(block.id) for block in current_blocks}
        
        for label in temporal_labels:
            try:
                # Skip if already attached
                if label in current_block_labels:
                    logger.debug(f"Temporal block already attached: {label}")
                    attached_labels.append(label)
                    continue
                
                # Check if block exists globally
                blocks = client.blocks.list(label=label)
                
                if blocks and len(blocks) > 0:
                    block = blocks[0]
                    # Check if already attached by ID
                    if str(block.id) in current_block_ids:
                        logger.debug(f"Temporal block already attached by ID: {label}")
                        attached_labels.append(label)
                        continue
                else:
                    # Create new temporal block with appropriate header
                    if "day" in label:
                        header = f"# Daily Journal - {today.strftime('%B %d, %Y')}"
                        initial_content = f"{header}\n\nNo entries yet for today."
                    elif "month" in label:
                        header = f"# Monthly Journal - {today.strftime('%B %Y')}"
                        initial_content = f"{header}\n\nNo entries yet for this month."
                    else:  # year
                        header = f"# Yearly Journal - {today.year}"
                        initial_content = f"{header}\n\nNo entries yet for this year."
                    
                    block = client.blocks.create(
                        label=label,
                        value=initial_content,
                        limit=10000  # Larger limit for journal blocks
                    )
                    logger.info(f"Created new temporal block: {label}")
                
                # Attach the block
                client.agents.blocks.attach(
                    agent_id=agent_id,
                    block_id=str(block.id)
                )
                attached_labels.append(label)
                logger.info(f"Attached temporal block: {label}")
                
            except Exception as e:
                # Check for duplicate constraint errors
                error_str = str(e)
                if "duplicate key value violates unique constraint" in error_str:
                    logger.debug(f"Temporal block already attached (constraint): {label}")
                    attached_labels.append(label)
                else:
                    logger.warning(f"Failed to attach temporal block {label}: {e}")
        
        logger.info(f"Temporal blocks attached: {len(attached_labels)}/{len(temporal_labels)}")
        return True, attached_labels
        
    except Exception as e:
        logger.error(f"Error attaching temporal blocks: {e}")
        return False, []


def detach_temporal_blocks(client: Letta, agent_id: str, labels_to_detach: list = None) -> bool:
    """
    Detach temporal journal blocks from the agent after synthesis.
    
    Args:
        client: Letta client
        agent_id: Agent ID
        labels_to_detach: Optional list of specific labels to detach. 
                         If None, detaches all temporal blocks.
    
    Returns:
        bool: Success status
    """
    try:
        # If no specific labels provided, generate today's labels using configuration
        if labels_to_detach is None:
            today = date.today()
            config = get_config()
            labels_to_detach = generate_temporal_block_labels(config._config, today)
        
        # Get current blocks and build label to ID mapping
        current_blocks = client.agents.blocks.list(agent_id=agent_id)
        block_label_to_id = {block.label: str(block.id) for block in current_blocks}
        
        detached_count = 0
        for label in labels_to_detach:
            if label in block_label_to_id:
                try:
                    client.agents.blocks.detach(
                        agent_id=agent_id,
                        block_id=block_label_to_id[label]
                    )
                    detached_count += 1
                    logger.debug(f"Detached temporal block: {label}")
                except Exception as e:
                    logger.warning(f"Failed to detach temporal block {label}: {e}")
            else:
                logger.debug(f"Temporal block not attached: {label}")
        
        logger.info(f"Detached {detached_count} temporal blocks")
        return True
        
    except Exception as e:
        logger.error(f"Error detaching temporal blocks: {e}")
        return False


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Void Bot - Bluesky autonomous agent')
    parser.add_argument('--test', action='store_true', help='Run in testing mode (no messages sent, queue files preserved)')
    parser.add_argument('--no-git', action='store_true', help='Skip git operations when exporting agent state')
    parser.add_argument('--simple-logs', action='store_true', help='Use simplified log format (void - LEVEL - message)')
    # --rich option removed as we now use simple text formatting
    parser.add_argument('--reasoning', action='store_true', help='Display reasoning in panels and set reasoning log level to INFO')
    parser.add_argument('--cleanup-interval', type=int, default=10, help='Run user block cleanup every N cycles (default: 10, 0 to disable)')
    parser.add_argument('--synthesis-interval', type=int, default=600, help='Send synthesis message every N seconds (default: 600 = 10 minutes, 0 to disable)')
    parser.add_argument('--synthesis-only', action='store_true', help='Run in synthesis-only mode (only send synthesis messages, no notification processing)')
    args = parser.parse_args()
    
    # Configure logging based on command line arguments
    if args.simple_logs:
        log_format = "void - %(levelname)s - %(message)s"
    else:
        # Create custom formatter with symbols
        class SymbolFormatter(logging.Formatter):
            """Custom formatter that adds symbols for different log levels"""
            
            SYMBOLS = {
                logging.DEBUG: '◇',
                logging.INFO: '✓',
                logging.WARNING: '⚠',
                logging.ERROR: '✗',
                logging.CRITICAL: '‼'
            }
            
            def format(self, record):
                # Get the symbol for this log level
                symbol = self.SYMBOLS.get(record.levelno, '•')
                
                # Format time as HH:MM:SS
                timestamp = self.formatTime(record, "%H:%M:%S")
                
                # Build the formatted message
                level_name = f"{record.levelname:<5}"  # Left-align, 5 chars
                
                # Use vertical bar as separator
                parts = [symbol, timestamp, '│', level_name, '│', record.getMessage()]
                
                return ' '.join(parts)
        
        # Reset logging configuration
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        # Create handler with custom formatter
        handler = logging.StreamHandler()
        if not args.simple_logs:
            handler.setFormatter(SymbolFormatter())
        else:
            handler.setFormatter(logging.Formatter(log_format))
        
        # Configure root logger
        logging.root.setLevel(logging.INFO)
        logging.root.addHandler(handler)
    
    global logger, prompt_logger, console
    # Only reconfigure if not already initialized
    if logger.level == logging.NOTSET:
        logger = logging.getLogger(main_logger_name)
        logger.setLevel(logging.INFO)
    
    # Create a separate logger for prompts (set to WARNING to hide by default)
    if prompt_logger.level == logging.NOTSET:
        prompt_logger = logging.getLogger(prompt_logger_name)
        if args.reasoning:
            prompt_logger.setLevel(logging.INFO)  # Show reasoning when --reasoning is used
        else:
            prompt_logger.setLevel(logging.WARNING)  # Hide by default
    
    # Disable httpx logging completely
    logging.getLogger("httpx").setLevel(logging.CRITICAL)
    
    # Create Rich console for pretty printing
    # Console no longer used - simple text formatting
    
    global TESTING_MODE, SKIP_GIT, SHOW_REASONING
    TESTING_MODE = args.test
    
    # Store no-git flag globally for use in export_agent_state calls
    SKIP_GIT = args.no_git
    
    # Store rich flag globally
    # Rich formatting no longer used
    
    # Store reasoning flag globally
    SHOW_REASONING = args.reasoning
    
    if TESTING_MODE:
        logger.info("=== RUNNING IN TESTING MODE ===")
        logger.info("   - No messages will be sent to Bluesky")
        logger.info("   - Queue files will not be deleted")
        logger.info("   - Notifications will not be marked as seen")
        print("\n")
    
    # Check for synthesis-only mode
    SYNTHESIS_ONLY = args.synthesis_only
    if SYNTHESIS_ONLY:
        logger.info("=== RUNNING IN SYNTHESIS-ONLY MODE ===")
        logger.info("   - Only synthesis messages will be sent")
        logger.info("   - No notification processing")
        logger.info("   - No Bluesky client needed")
        print("\n")
    """Main bot loop that continuously monitors for notifications."""
    global start_time
    start_time = time.time()
    logger.info("=== STARTING VOID BOT ===")
    agent = initialize_agent()
    logger.info(f"Agent initialized: {agent.id}")
    
    # Initialize notification database
    global NOTIFICATION_DB
    logger.info("Initializing notification database...")
    NOTIFICATION_DB = NotificationDB()
    
    # Migrate from old JSON format if it exists
    if PROCESSED_NOTIFICATIONS_FILE.exists():
        logger.info("Found old processed_notifications.json, migrating to database...")
        NOTIFICATION_DB.migrate_from_json(str(PROCESSED_NOTIFICATIONS_FILE))
    
    # Log database stats
    db_stats = NOTIFICATION_DB.get_stats()
    logger.info(f"Database initialized - Total notifications: {db_stats.get('total', 0)}, Recent (24h): {db_stats.get('recent_24h', 0)}")
    
    # Clean up old records
    NOTIFICATION_DB.cleanup_old_records(days=7)
    
    # Ensure correct tools are attached for Bluesky
    logger.info("Configuring tools for Bluesky platform...")
    try:
        from tool_manager import ensure_platform_tools
        ensure_platform_tools('bluesky', agent.id)
    except Exception as e:
        logger.error(f"Failed to configure platform tools: {e}")
        logger.warning("Continuing with existing tool configuration")
    
    # Check if agent has required tools
    if hasattr(agent, 'tools') and agent.tools:
        tool_names = [tool.name for tool in agent.tools]
        # Check for bluesky-related tools
        bluesky_tools = [name for name in tool_names if 'bluesky' in name.lower() or 'reply' in name.lower()]
        if not bluesky_tools:
            logger.warning("No Bluesky-related tools found! Agent may not be able to reply.")
    else:
        logger.warning("Agent has no tools registered!")

    # Clean up all user blocks at startup
    logger.info("🧹 Cleaning up user blocks at startup...")
    periodic_user_block_cleanup(CLIENT, agent.id)
    
    # Initialize Bluesky client (needed for both notification processing and synthesis acks/posts)
    if not SYNTHESIS_ONLY:
        atproto_client = bsky_utils.default_login()
        logger.info("Connected to Bluesky")
    else:
        # In synthesis-only mode, still connect for acks and posts (unless in test mode)
        if not args.test:
            atproto_client = bsky_utils.default_login()
            logger.info("Connected to Bluesky (for synthesis acks/posts)")
        else:
            atproto_client = None
            logger.info("Skipping Bluesky connection (test mode)")

    # Configure intervals
    CLEANUP_INTERVAL = args.cleanup_interval
    SYNTHESIS_INTERVAL = args.synthesis_interval
    
    # Synthesis-only mode
    if SYNTHESIS_ONLY:
        if SYNTHESIS_INTERVAL <= 0:
            logger.error("Synthesis-only mode requires --synthesis-interval > 0")
            return
            
        logger.info(f"Starting synthesis-only mode, interval: {SYNTHESIS_INTERVAL} seconds ({SYNTHESIS_INTERVAL/60:.1f} minutes)")
        
        while True:
            try:
                # Send synthesis message immediately on first run
                logger.info("🧠 Sending synthesis message")
                send_synthesis_message(CLIENT, agent.id, atproto_client)
                
                # Wait for next interval
                logger.info(f"Waiting {SYNTHESIS_INTERVAL} seconds until next synthesis...")
                sleep(SYNTHESIS_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("=== SYNTHESIS MODE STOPPED BY USER ===")
                break
            except Exception as e:
                logger.error(f"Error in synthesis loop: {e}")
                logger.info(f"Sleeping for {SYNTHESIS_INTERVAL} seconds due to error...")
                sleep(SYNTHESIS_INTERVAL)
    
    # Normal mode with notification processing
    logger.info(f"Starting notification monitoring, checking every {FETCH_NOTIFICATIONS_DELAY_SEC} seconds")

    cycle_count = 0
    
    if CLEANUP_INTERVAL > 0:
        logger.info(f"User block cleanup enabled every {CLEANUP_INTERVAL} cycles")
    else:
        logger.info("User block cleanup disabled")
    
    if SYNTHESIS_INTERVAL > 0:
        logger.info(f"Synthesis messages enabled every {SYNTHESIS_INTERVAL} seconds ({SYNTHESIS_INTERVAL/60:.1f} minutes)")
    else:
        logger.info("Synthesis messages disabled")
    
    while True:
        try:
            cycle_count += 1
            process_notifications(agent, atproto_client, TESTING_MODE)
            
            # Check if synthesis interval has passed
            if SYNTHESIS_INTERVAL > 0:
                current_time = time.time()
                global last_synthesis_time
                if current_time - last_synthesis_time >= SYNTHESIS_INTERVAL:
                    logger.info(f"⏰ {SYNTHESIS_INTERVAL/60:.1f} minutes have passed, triggering synthesis")
                    send_synthesis_message(CLIENT, agent.id, atproto_client)
                    last_synthesis_time = current_time
            
            # Run periodic cleanup every N cycles
            if CLEANUP_INTERVAL > 0 and cycle_count % CLEANUP_INTERVAL == 0:
                logger.debug(f"Running periodic user block cleanup (cycle {cycle_count})")
                periodic_user_block_cleanup(CLIENT, agent.id)
                
                # Also check database health when doing cleanup
                if NOTIFICATION_DB:
                    db_stats = NOTIFICATION_DB.get_stats()
                    pending = db_stats.get('status_pending', 0)
                    errors = db_stats.get('status_error', 0)
                    
                    if pending > 50:
                        logger.warning(f"⚠️ Queue health check: {pending} pending notifications (may be stuck)")
                    if errors > 20:
                        logger.warning(f"⚠️ Queue health check: {errors} error notifications")
                    
                    # Periodic cleanup of old records
                    if cycle_count % (CLEANUP_INTERVAL * 10) == 0:  # Every 100 cycles
                        logger.info("Running database cleanup of old records...")
                        NOTIFICATION_DB.cleanup_old_records(days=7)
            
            # Log cycle completion with stats
            elapsed_time = time.time() - start_time
            total_messages = sum(message_counters.values())
            messages_per_minute = (total_messages / elapsed_time * 60) if elapsed_time > 0 else 0
            
            if total_messages > 0:
                logger.info(f"Cycle {cycle_count} complete. Session totals: {total_messages} messages ({message_counters['mentions']} mentions, {message_counters['replies']} replies) | {messages_per_minute:.1f} msg/min")
            sleep(FETCH_NOTIFICATIONS_DELAY_SEC)

        except KeyboardInterrupt:
            # Final stats
            elapsed_time = time.time() - start_time
            total_messages = sum(message_counters.values())
            messages_per_minute = (total_messages / elapsed_time * 60) if elapsed_time > 0 else 0
            
            logger.info("=== BOT STOPPED BY USER ===")
            logger.info(f"Final session stats: {total_messages} total messages processed in {elapsed_time/60:.1f} minutes")
            logger.info(f"   - {message_counters['mentions']} mentions")
            logger.info(f"   - {message_counters['replies']} replies")
            logger.info(f"   - {message_counters['follows']} follows")
            logger.info(f"   - {message_counters['reposts_skipped']} reposts skipped")
            logger.info(f"   - Average rate: {messages_per_minute:.1f} messages/minute")
            
            # Close database connection
            if NOTIFICATION_DB:
                logger.info("Closing database connection...")
                NOTIFICATION_DB.close()
            
            break
        except Exception as e:
            logger.error(f"=== ERROR IN MAIN LOOP CYCLE {cycle_count} ===")
            logger.error(f"Error details: {e}")
            # Wait a bit longer on errors
            logger.info(f"Sleeping for {FETCH_NOTIFICATIONS_DELAY_SEC * 2} seconds due to error...")
            sleep(FETCH_NOTIFICATIONS_DELAY_SEC * 2)


if __name__ == "__main__":
    main()
