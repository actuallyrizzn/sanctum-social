import os
import logging
import uuid
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from atproto_client import Client, Session, SessionEvent, models

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("bluesky_session_handler")

# Load the environment variables
import dotenv
dotenv.load_dotenv(override=True)

import yaml
import json

# Strip fields. A list of fields to remove from a JSON object
STRIP_FIELDS = [
    "cid",
    "rev",
    "did",
    "uri",
    "langs",
    "threadgate",
    "py_type",
    "labels",
    "avatar",
    "viewer",
    "indexed_at",
    "tags",
    "associated",
    "thread_context",
    "aspect_ratio",
    "thumb",
    "fullsize",
    "root",
    "created_at",
    "verification",
    "like_count",
    "quote_count",
    "reply_count",
    "repost_count",
    "embedding_disabled",
    "thread_muted",
    "reply_disabled",
    "pinned",
    "like",
    "repost",
    "blocked_by",
    "blocking",
    "blocking_by_list",
    "followed_by",
    "following",
    "known_followers",
    "muted",
    "muted_by_list",
    "root_author_like",
    "entities",
    "ref",
    "mime_type",
    "size",
]
def convert_to_basic_types(obj):
    """Convert complex Python objects to basic types for JSON/YAML serialization."""
    if hasattr(obj, '__dict__'):
        # Convert objects with __dict__ to their dictionary representation
        return convert_to_basic_types(obj.__dict__)
    elif isinstance(obj, dict):
        return {key: convert_to_basic_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_basic_types(item) for item in obj]
    elif isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    else:
        # For other types, try to convert to string
        return str(obj)


def strip_fields(obj, strip_field_list):
    """Recursively strip fields from a JSON object."""
    if isinstance(obj, dict):
        keys_flagged_for_removal = []

        # Remove fields from strip list and pydantic metadata
        for field in list(obj.keys()):
            if field in strip_field_list or field.startswith("__"):
                keys_flagged_for_removal.append(field)

        # Remove flagged keys
        for key in keys_flagged_for_removal:
            obj.pop(key, None)

        # Recursively process remaining values
        for key, value in list(obj.items()):
            obj[key] = strip_fields(value, strip_field_list)
            # Remove empty/null values after processing
            if (
                obj[key] is None
                or (isinstance(obj[key], dict) and len(obj[key]) == 0)
                or (isinstance(obj[key], list) and len(obj[key]) == 0)
                or (isinstance(obj[key], str) and obj[key].strip() == "")
            ):
                obj.pop(key, None)

    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            obj[i] = strip_fields(value, strip_field_list)
        # Remove None values from list
        obj[:] = [item for item in obj if item is not None]

    return obj


def flatten_thread_structure(thread_data):
    """
    Flatten a nested thread structure into a list while preserving all data.
    
    Args:
        thread_data: The thread data from get_post_thread
        
    Returns:
        Dict with 'posts' key containing a list of posts in chronological order
    """
    posts = []
    
    def traverse_thread(node):
        """Recursively traverse the thread structure to collect posts."""
        if not node:
            return
            
        # If this node has a parent, traverse it first (to maintain chronological order)
        if hasattr(node, 'parent') and node.parent:
            traverse_thread(node.parent)
        elif isinstance(node, dict) and 'parent' in node and node['parent']:
            traverse_thread(node['parent'])
        
        # Then add this node's post
        if hasattr(node, 'post') and node.post:
            # Convert to dict if needed to ensure we can process it
            if hasattr(node.post, '__dict__'):
                post_dict = node.post.__dict__.copy()
            elif isinstance(node.post, dict):
                post_dict = node.post.copy()
            else:
                post_dict = {}
            
            posts.append(post_dict)
        elif isinstance(node, dict) and 'post' in node and node['post']:
            # Convert to dict if needed to ensure we can process it
            if isinstance(node['post'], dict):
                post_dict = node['post'].copy()
            else:
                post_dict = {}
            
            posts.append(post_dict)
        
        # Finally, traverse any replies
        if hasattr(node, 'replies') and node.replies:
            for reply in node.replies:
                traverse_thread(reply)
        elif isinstance(node, dict) and 'replies' in node and node['replies']:
            for reply in node['replies']:
                traverse_thread(reply)
    
    # Handle the thread structure
    if hasattr(thread_data, 'thread'):
        # Start from the main thread node
        traverse_thread(thread_data.thread)
    elif isinstance(thread_data, dict) and 'thread' in thread_data:
        traverse_thread(thread_data['thread'])
    elif hasattr(thread_data, '__dict__') and 'thread' in thread_data.__dict__:
        traverse_thread(thread_data.__dict__['thread'])
    
    # Return a simple structure with posts list
    return {'posts': posts}


def thread_to_yaml_string(thread, strip_metadata=True):
    """
    Convert thread data to a YAML-formatted string for LLM parsing.

    Args:
        thread: The thread data from get_post_thread
        strip_metadata: Whether to strip metadata fields for cleaner output

    Returns:
        YAML-formatted string representation of the thread
    """
    # First flatten the thread structure to avoid deep nesting
    flattened = flatten_thread_structure(thread)
    
    # Convert complex objects to basic types
    basic_thread = convert_to_basic_types(flattened)

    if strip_metadata:
        # Create a copy and strip unwanted fields
        cleaned_thread = strip_fields(basic_thread, STRIP_FIELDS)
    else:
        cleaned_thread = basic_thread

    return yaml.dump(cleaned_thread, indent=2, allow_unicode=True, default_flow_style=False)







def get_session(username: str) -> Optional[str]:
    """Get session with enhanced error handling and validation."""
    try:
        # Try enhanced version first
        return get_session_with_retry(username)
    except Exception as e:
        logger.debug(f"Enhanced session loading failed, falling back to legacy method: {e}")
        # Fall back to legacy method for backward compatibility
        import os
        session_file = os.path.join(os.getcwd(), f"session_{username}.txt")
        try:
            with open(session_file, encoding="UTF-8") as f:
                return f.read()
        except FileNotFoundError:
            logger.debug(f"No existing session found for {username}")
            return None
        except Exception as legacy_error:
            logger.error(f"Error getting session for {username}: {legacy_error}")
            return None

def save_session(username: str, session_string: str) -> None:
    """Save session with enhanced error handling and validation."""
    try:
        # Try enhanced version first, but disable validation for backward compatibility
        success = save_session_with_retry(username, session_string, validate=False)
        if success:
            return
    except Exception as e:
        logger.debug(f"Enhanced session saving failed, falling back to legacy method: {e}")
    
    # Fall back to legacy method for backward compatibility
    import os
    session_file = os.path.join(os.getcwd(), f"session_{username}.txt")
    try:
        with open(session_file, "w", encoding="UTF-8") as f:
            f.write(session_string)
        logger.debug(f"Session saved for {username}")
    except Exception as legacy_error:
        logger.error(f"Failed to save session for {username}: {legacy_error}")
        raise RuntimeError(f"Failed to save session for {username}")

def on_session_change(username: str, event: SessionEvent, session: Session) -> None:
    logger.debug(f"Session changed: {event} {repr(session)}")
    if event in (SessionEvent.CREATE, SessionEvent.REFRESH):
        logger.debug(f"Saving changed session for {username}")
        save_session(username, session.export())


# Enhanced Session Management Functions

def get_session_config() -> Dict[str, Any]:
    """Get session management configuration from config or defaults."""
    try:
        from config_loader import get_config
        config = get_config()
        session_config = config.get('session_management', {})
    except Exception:
        session_config = {}
    
    return {
        'directory': session_config.get('directory', 'sessions'),
        'max_age_days': session_config.get('max_age_days', 30),
        'retry_attempts': session_config.get('retry_attempts', 3),
        'retry_delay': session_config.get('retry_delay', 1.0),
        'validate_sessions': session_config.get('validate_sessions', True)
    }


def get_session_path(username: str, session_dir: Optional[str] = None) -> Path:
    """Get session file path with proper directory handling."""
    if session_dir is None:
        # Use current working directory for backward compatibility
        import os
        session_dir = os.getcwd()
    
    # Create session directory if it doesn't exist
    session_path = Path(session_dir)
    session_path.mkdir(parents=True, exist_ok=True)
    
    return session_path / f"session_{username}.txt"


def validate_session(session_string: str) -> bool:
    """Validate session data format and basic structure."""
    if not session_string or not isinstance(session_string, str):
        return False
    
    try:
        # Try to parse as JSON to validate format
        session_data = json.loads(session_string)
        
        # Check for required fields
        required_fields = ['accessJwt', 'refreshJwt', 'handle', 'did']
        if not all(field in session_data for field in required_fields):
            logger.warning("Session missing required fields")
            return False
        
        # Basic validation of field values
        if not session_data.get('accessJwt') or not session_data.get('did'):
            logger.warning("Session has invalid JWT or DID")
            return False
        
        return True
    except json.JSONDecodeError:
        logger.warning("Session data is not valid JSON")
        return False
    except Exception as e:
        logger.warning(f"Session validation error: {e}")
        return False


def get_session_with_retry(username: str, max_retries: int = 3, session_dir: Optional[str] = None) -> Optional[str]:
    """Get session with retry logic for transient failures."""
    config = get_session_config()
    max_retries = min(max_retries, config['retry_attempts'])
    
    for attempt in range(max_retries):
        try:
            session_path = get_session_path(username, session_dir)
            
            if not session_path.exists():
                logger.debug(f"No existing session found for {username}")
                return None
            
            with open(session_path, 'r', encoding='UTF-8') as f:
                session_string = f.read()
            
            # Validate session if configured to do so
            if config['validate_sessions'] and not validate_session(session_string):
                logger.warning(f"Invalid session data for {username}, removing file")
                session_path.unlink()
                return None
            
            logger.debug(f"Successfully loaded session for {username}")
            return session_string
            
        except (PermissionError, OSError) as e:
            logger.warning(f"File access error for {username} (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                logger.error(f"Failed to read session for {username} after {max_retries} attempts")
                return None
            time.sleep(config['retry_delay'] * (2 ** attempt))  # Exponential backoff
            
        except Exception as e:
            logger.error(f"Unexpected error reading session for {username}: {e}")
            return None
    
    return None


def save_session_with_retry(username: str, session_string: str, max_retries: int = 3, session_dir: Optional[str] = None, validate: bool = True) -> bool:
    """Save session with exponential backoff retry logic."""
    config = get_session_config()
    max_retries = min(max_retries, config['retry_attempts'])
    
    # Validate session before saving
    if validate and config['validate_sessions'] and not validate_session(session_string):
        logger.error(f"Cannot save invalid session data for {username}")
        return False
    
    for attempt in range(max_retries):
        try:
            session_path = get_session_path(username, session_dir)
            
            # Write to temporary file first, then rename (atomic operation)
            temp_path = session_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='UTF-8') as f:
                f.write(session_string)
            
            # Atomic rename
            temp_path.replace(session_path)
            
            logger.debug(f"Successfully saved session for {username}")
            return True
            
        except (PermissionError, OSError) as e:
            logger.warning(f"File write error for {username} (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                logger.error(f"Failed to save session for {username} after {max_retries} attempts")
                return False
            time.sleep(config['retry_delay'] * (2 ** attempt))  # Exponential backoff
            
        except Exception as e:
            logger.error(f"Unexpected error saving session for {username}: {e}")
            return False
    
    return False


def cleanup_old_sessions(session_dir: Optional[str] = None, max_age_days: int = 30) -> int:
    """Clean up old session files."""
    config = get_session_config()
    max_age_days = min(max_age_days, config['max_age_days'])
    
    if session_dir is None:
        session_dir = config['directory']
    
    try:
        session_path = Path(session_dir)
        if not session_path.exists():
            logger.debug(f"Session directory {session_dir} does not exist")
            return 0
    except Exception as e:
        logger.error(f"Error accessing session directory {session_dir}: {e}")
        return 0
    
    cleaned_count = 0
    current_time = time.time()
    max_age_seconds = max_age_days * 24 * 60 * 60
    
    try:
        for session_file in session_path.glob("session_*.txt"):
            try:
                # Check file age
                file_age = current_time - session_file.stat().st_mtime
                if file_age > max_age_seconds:
                    logger.debug(f"Removing old session file: {session_file}")
                    session_file.unlink()
                    cleaned_count += 1
                    continue
                
                # Check for corrupted sessions
                try:
                    with open(session_file, 'r', encoding='UTF-8') as f:
                        session_data = f.read()
                    
                    if config['validate_sessions'] and not validate_session(session_data):
                        logger.debug(f"Removing corrupted session file: {session_file}")
                        session_file.unlink()
                        cleaned_count += 1
                        
                except Exception as e:
                    logger.debug(f"Removing unreadable session file {session_file}: {e}")
                    session_file.unlink()
                    cleaned_count += 1
                    
            except Exception as e:
                logger.warning(f"Error processing session file {session_file}: {e}")
        
        logger.info(f"Cleaned up {cleaned_count} old/corrupted session files")
        return cleaned_count
        
    except Exception as e:
        logger.error(f"Error during session cleanup: {e}")
        return cleaned_count

def init_client(username: str, password: str) -> Client:
    pds_uri = os.getenv("PDS_URI")
    if pds_uri is None:
        logger.warning(
            "No PDS URI provided. Falling back to bsky.social. Note! If you are on a non-Bluesky PDS, this can cause logins to fail. Please provide a PDS URI using the PDS_URI environment variable."
        )
        pds_uri = "https://bsky.social"

    # Print the PDS URI
    logger.debug(f"Using PDS URI: {pds_uri}")

    client = Client(pds_uri)
    client.on_session_change(
        lambda event, session: on_session_change(username, event, session)
    )

    session_string = get_session(username)
    if session_string:
        logger.debug(f"Reusing existing session for {username}")
        client.login(session_string=session_string)
    else:
        logger.debug(f"Creating new session for {username}")
        client.login(username, password)

    return client


def default_login() -> Client:
    """Login using configuration from config.yaml or environment variables."""
    try:
        from config_loader import get_bluesky_config
        bluesky_config = get_bluesky_config()
        
        username = bluesky_config['username']
        password = bluesky_config['password']
        pds_uri = bluesky_config.get('pds_uri', 'https://bsky.social')
        
        logger.info(f"Logging into Bluesky as {username} via {pds_uri}")
        
        # Use pds_uri from config
        client = Client(base_url=pds_uri)
        client.login(username, password)
        return client
        
    except Exception as e:
        logger.error(f"Failed to load Bluesky configuration: {e}")
        logger.error("Please check your config.yaml file or environment variables")
        exit(1)

def remove_outside_quotes(text: str) -> str:
    """
    Remove outside double quotes from response text.
    
    Only handles double quotes to avoid interfering with contractions:
    - Double quotes: "text" → text
    - Preserves single quotes and internal quotes
    
    Args:
        text: The text to process
        
    Returns:
        Text with outside double quotes removed
    """
    if not text or len(text) < 2:
        return text
    
    text = text.strip()
    
    # Only remove double quotes from start and end
    if text.startswith('"') and text.endswith('"'):
        return text[1:-1]
    
    return text

def reply_to_post(client: Client, text: str, reply_to_uri: str, reply_to_cid: str, root_uri: Optional[str] = None, root_cid: Optional[str] = None, lang: Optional[str] = None, correlation_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Reply to a post on Bluesky with rich text support.

    Args:
        client: Authenticated Bluesky client
        text: The reply text
        reply_to_uri: The URI of the post being replied to (parent)
        reply_to_cid: The CID of the post being replied to (parent)
        root_uri: The URI of the root post (if replying to a reply). If None, uses reply_to_uri
        root_cid: The CID of the root post (if replying to a reply). If None, uses reply_to_cid
        lang: Language code for the post (e.g., 'en-US', 'es', 'ja')
        correlation_id: Unique ID for tracking this message through the pipeline

    Returns:
        The response from sending the post
    """
    import re
    
    # Generate correlation ID if not provided
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())[:8]
    
    # Enhanced logging with structured data
    logger.info(f"[{correlation_id}] Starting reply_to_post", extra={
        'correlation_id': correlation_id,
        'text_length': len(text),
        'text_preview': text[:100] + '...' if len(text) > 100 else text,
        'reply_to_uri': reply_to_uri,
        'root_uri': root_uri,
        'lang': lang
    })
    
    start_time = time.time()
    
    # If root is not provided, this is a reply to the root post
    if root_uri is None:
        root_uri = reply_to_uri
        root_cid = reply_to_cid

    # Create references for the reply
    parent_ref = models.create_strong_ref(models.ComAtprotoRepoStrongRef.Main(uri=reply_to_uri, cid=reply_to_cid))
    root_ref = models.create_strong_ref(models.ComAtprotoRepoStrongRef.Main(uri=root_uri, cid=root_cid))

    # Parse rich text facets (mentions and URLs)
    facets = []
    text_bytes = text.encode("UTF-8")
    mentions_found = []
    urls_found = []
    
    logger.debug(f"[{correlation_id}] Parsing facets from text (length: {len(text_bytes)} bytes)")
    
    # Parse mentions - fixed to handle @ at start of text
    mention_regex = rb"(?:^|[$|\W])(@([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)"
    
    for m in re.finditer(mention_regex, text_bytes):
        handle = m.group(1)[1:].decode("UTF-8")  # Remove @ prefix
        mentions_found.append(handle)
        # Adjust byte positions to account for the optional prefix
        mention_start = m.start(1)
        mention_end = m.end(1)
        try:
            # Resolve handle to DID using the API
            resolve_resp = client.app.bsky.actor.get_profile({'actor': handle})
            if resolve_resp and hasattr(resolve_resp, 'did'):
                facets.append(
                    models.AppBskyRichtextFacet.Main(
                        index=models.AppBskyRichtextFacet.ByteSlice(
                            byteStart=mention_start,
                            byteEnd=mention_end
                        ),
                        features=[models.AppBskyRichtextFacet.Mention(did=resolve_resp.did)]
                    )
                )
                logger.debug(f"[{correlation_id}] Resolved mention @{handle} -> {resolve_resp.did}")
        except Exception as e:
            logger.warning(f"[{correlation_id}] Failed to resolve handle @{handle}: {e}")
            continue
    
    # Parse URLs - fixed to handle URLs at start of text
    url_regex = rb"(?:^|[$|\W])(https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*[-a-zA-Z0-9@%_\+~#//=])?)"
    
    for m in re.finditer(url_regex, text_bytes):
        url = m.group(1).decode("UTF-8")
        urls_found.append(url)
        # Adjust byte positions to account for the optional prefix
        url_start = m.start(1)
        url_end = m.end(1)
        facets.append(
            models.AppBskyRichtextFacet.Main(
                index=models.AppBskyRichtextFacet.ByteSlice(
                    byteStart=url_start,
                    byteEnd=url_end
                ),
                features=[models.AppBskyRichtextFacet.Link(uri=url)]
            )
        )
        logger.debug(f"[{correlation_id}] Found URL: {url}")
    
    logger.debug(f"[{correlation_id}] Facet parsing complete", extra={
        'correlation_id': correlation_id,
        'mentions_count': len(mentions_found),
        'mentions': mentions_found,
        'urls_count': len(urls_found),
        'urls': urls_found,
        'total_facets': len(facets)
    })

    # Send the reply with facets if any were found
    logger.info(f"[{correlation_id}] Sending reply to Bluesky API", extra={
        'correlation_id': correlation_id,
        'has_facets': bool(facets),
        'facet_count': len(facets),
        'lang': lang
    })
    
    try:
        if facets:
            response = client.send_post(
                text=text,
                reply_to=models.AppBskyFeedPost.ReplyRef(parent=parent_ref, root=root_ref),
                facets=facets,
                langs=[lang] if lang else None
            )
        else:
            response = client.send_post(
                text=text,
                reply_to=models.AppBskyFeedPost.ReplyRef(parent=parent_ref, root=root_ref),
                langs=[lang] if lang else None
            )
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Extract post URL for user-friendly logging
        post_url = None
        if hasattr(response, 'uri') and response.uri:
            # Convert AT-URI to web URL
            # Format: at://did:plc:xxx/app.bsky.feed.post/xxx -> https://bsky.app/profile/handle/post/xxx
            try:
                uri_parts = response.uri.split('/')
                if len(uri_parts) >= 4 and uri_parts[3] == 'app.bsky.feed.post':
                    rkey = uri_parts[4]
                    # We'd need to resolve DID to handle, but for now just use the URI
                    post_url = f"bsky://post/{rkey}"
            except:
                pass
        
        logger.info(f"[{correlation_id}] Reply sent successfully ({response_time:.3f}s) - URI: {response.uri}" + 
                   (f" - URL: {post_url}" if post_url else ""), extra={
            'correlation_id': correlation_id,
            'response_time': round(response_time, 3),
            'post_uri': response.uri,
            'post_url': post_url,
            'post_cid': getattr(response, 'cid', None),
            'text_length': len(text)
        })
        
        return response
        
    except Exception as e:
        response_time = time.time() - start_time
        logger.error(f"[{correlation_id}] Failed to send reply", extra={
            'correlation_id': correlation_id,
            'error': str(e),
            'error_type': type(e).__name__,
            'response_time': round(response_time, 3),
            'text_length': len(text)
        })
        raise


def get_post_thread(client: Client, uri: str) -> Optional[Dict[str, Any]]:
    """
    Get the thread containing a post to find root post information.

    Args:
        client: Authenticated Bluesky client
        uri: The URI of the post

    Returns:
        The thread data or None if not found
    """
    try:
        thread = client.app.bsky.feed.get_post_thread({'uri': uri, 'parent_height': 60, 'depth': 10})
        return thread
    except Exception as e:
        logger.error(f"Error fetching post thread: {e}")
        return None


def reply_to_notification(client: Client, notification: Any, reply_text: str, lang: str = "en-US", correlation_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Reply to a notification (mention or reply).

    Args:
        client: Authenticated Bluesky client
        notification: The notification object from list_notifications
        reply_text: The text to reply with
        lang: Language code for the post (defaults to "en-US")
        correlation_id: Unique ID for tracking this message through the pipeline

    Returns:
        The response from sending the reply or None if failed
    """
    # Generate correlation ID if not provided
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())[:8]
    
    logger.info(f"[{correlation_id}] Processing reply_to_notification", extra={
        'correlation_id': correlation_id,
        'reply_length': len(reply_text),
        'lang': lang
    })
    
    try:
        # Get the post URI and CID from the notification (handle both dict and object)
        if isinstance(notification, dict):
            post_uri = notification.get('uri')
            post_cid = notification.get('cid')
            # Check if the notification record has reply info with root
            record = notification.get('record', {})
            reply_info = record.get('reply') if isinstance(record, dict) else None
        elif hasattr(notification, 'uri') and hasattr(notification, 'cid'):
            post_uri = notification.uri
            post_cid = notification.cid
            # Check if the notification record has reply info with root
            reply_info = None
            if hasattr(notification, 'record') and hasattr(notification.record, 'reply'):
                reply_info = notification.record.reply
        else:
            post_uri = None
            post_cid = None
            reply_info = None

        if not post_uri or not post_cid:
            logger.error("Notification doesn't have required uri/cid fields")
            return None

        # Determine root: if post has reply info, use its root; otherwise this post IS the root
        if reply_info:
            # Extract root from the notification's reply structure
            if isinstance(reply_info, dict):
                root_ref = reply_info.get('root')
                if root_ref and isinstance(root_ref, dict):
                    root_uri = root_ref.get('uri', post_uri)
                    root_cid = root_ref.get('cid', post_cid)
                else:
                    # No root in reply info, use post as root
                    root_uri = post_uri
                    root_cid = post_cid
            elif hasattr(reply_info, 'root'):
                if hasattr(reply_info.root, 'uri') and hasattr(reply_info.root, 'cid'):
                    root_uri = reply_info.root.uri
                    root_cid = reply_info.root.cid
                else:
                    root_uri = post_uri
                    root_cid = post_cid
            else:
                root_uri = post_uri
                root_cid = post_cid
        else:
            # No reply info means this post IS the root
            root_uri = post_uri
            root_cid = post_cid

        # Reply to the notification
        return reply_to_post(
            client=client,
            text=reply_text,
            reply_to_uri=post_uri,
            reply_to_cid=post_cid,
            root_uri=root_uri,
            root_cid=root_cid,
            lang=lang,
            correlation_id=correlation_id
        )

    except Exception as e:
        logger.error(f"[{correlation_id}] Error replying to notification: {e}", extra={
            'correlation_id': correlation_id,
            'error': str(e),
            'error_type': type(e).__name__
        })
        return None


def reply_with_thread_to_notification(client: Client, notification: Any, reply_messages: List[str], lang: str = "en-US", correlation_id: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
    """
    Reply to a notification with a threaded chain of messages (max 15).

    Args:
        client: Authenticated Bluesky client
        notification: The notification object from list_notifications
        reply_messages: List of reply texts (max 15 messages, each max 300 chars)
        lang: Language code for the posts (defaults to "en-US")
        correlation_id: Unique ID for tracking this message through the pipeline

    Returns:
        List of responses from sending the replies or None if failed
    """
    # Generate correlation ID if not provided
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())[:8]
    
    logger.info(f"[{correlation_id}] Starting threaded reply", extra={
        'correlation_id': correlation_id,
        'message_count': len(reply_messages),
        'total_length': sum(len(msg) for msg in reply_messages),
        'lang': lang
    })
    
    try:
        # Validate input
        if not reply_messages or len(reply_messages) == 0:
            logger.error(f"[{correlation_id}] Reply messages list cannot be empty")
            return None
        if len(reply_messages) > 15:
            logger.error(f"[{correlation_id}] Cannot send more than 15 reply messages (got {len(reply_messages)})")
            return None
        
        # Get the post URI and CID from the notification (handle both dict and object)
        if isinstance(notification, dict):
            post_uri = notification.get('uri')
            post_cid = notification.get('cid')
            # Check if the notification record has reply info with root
            record = notification.get('record', {})
            reply_info = record.get('reply') if isinstance(record, dict) else None
        elif hasattr(notification, 'uri') and hasattr(notification, 'cid'):
            post_uri = notification.uri
            post_cid = notification.cid
            # Check if the notification record has reply info with root
            reply_info = None
            if hasattr(notification, 'record') and hasattr(notification.record, 'reply'):
                reply_info = notification.record.reply
        else:
            post_uri = None
            post_cid = None
            reply_info = None

        if not post_uri or not post_cid:
            logger.error("Notification doesn't have required uri/cid fields")
            return None

        # Determine root: if post has reply info, use its root; otherwise this post IS the root
        if reply_info:
            # Extract root from the notification's reply structure
            if isinstance(reply_info, dict):
                root_ref = reply_info.get('root')
                if root_ref and isinstance(root_ref, dict):
                    root_uri = root_ref.get('uri', post_uri)
                    root_cid = root_ref.get('cid', post_cid)
                else:
                    # No root in reply info, use post as root
                    root_uri = post_uri
                    root_cid = post_cid
            elif hasattr(reply_info, 'root'):
                if hasattr(reply_info.root, 'uri') and hasattr(reply_info.root, 'cid'):
                    root_uri = reply_info.root.uri
                    root_cid = reply_info.root.cid
                else:
                    root_uri = post_uri
                    root_cid = post_cid
            else:
                root_uri = post_uri
                root_cid = post_cid
        else:
            # No reply info means this post IS the root
            root_uri = post_uri
            root_cid = post_cid

        # Send replies in sequence, creating a thread
        responses = []
        current_parent_uri = post_uri
        current_parent_cid = post_cid
        
        for i, message in enumerate(reply_messages):
            thread_correlation_id = f"{correlation_id}-{i+1}"
            logger.info(f"[{thread_correlation_id}] Sending reply {i+1}/{len(reply_messages)}: {message[:50]}...")
            
            # Send this reply
            response = reply_to_post(
                client=client,
                text=message,
                reply_to_uri=current_parent_uri,
                reply_to_cid=current_parent_cid,
                root_uri=root_uri,
                root_cid=root_cid,
                lang=lang,
                correlation_id=thread_correlation_id
            )
            
            if not response:
                logger.error(f"[{thread_correlation_id}] Failed to send reply {i+1}, posting system failure message")
                # Try to post a system failure message
                failure_response = reply_to_post(
                    client=client,
                    text="[SYSTEM FAILURE: COULD NOT POST MESSAGE, PLEASE TRY AGAIN]",
                    reply_to_uri=current_parent_uri,
                    reply_to_cid=current_parent_cid,
                    root_uri=root_uri,
                    root_cid=root_cid,
                    lang=lang,
                    correlation_id=f"{thread_correlation_id}-FAIL"
                )
                if failure_response:
                    responses.append(failure_response)
                    current_parent_uri = failure_response.uri
                    current_parent_cid = failure_response.cid
                else:
                    logger.error(f"[{thread_correlation_id}] Could not even send system failure message, stopping thread")
                    return responses if responses else None
            else:
                responses.append(response)
                # Update parent references for next reply (if any)
                if i < len(reply_messages) - 1:  # Not the last message
                    current_parent_uri = response.uri
                    current_parent_cid = response.cid
                
        logger.info(f"[{correlation_id}] Successfully sent {len(responses)} threaded replies", extra={
            'correlation_id': correlation_id,
            'replies_sent': len(responses),
            'replies_requested': len(reply_messages)
        })
        return responses

    except Exception as e:
        logger.error(f"[{correlation_id}] Error sending threaded reply to notification: {e}", extra={
            'correlation_id': correlation_id,
            'error': str(e),
            'error_type': type(e).__name__,
            'message_count': len(reply_messages)
        })
        return None


def create_synthesis_ack(client: Client, note: str) -> Optional[Dict[str, Any]]:
    """
    Create a stream.thought.ack record for synthesis without a target post.
    
    This creates a synthesis acknowledgment with null subject field.
    
    Args:
        client: Authenticated Bluesky client
        note: The synthesis note/content
        
    Returns:
        The response from creating the acknowledgment record or None if failed
    """
    try:
        import requests
        import json
        from datetime import datetime, timezone
        
        # Get session info from the client
        access_token = None
        user_did = None
        
        # Try different ways to get the session info
        if hasattr(client, '_session') and client._session:
            access_token = client._session.access_jwt
            user_did = client._session.did
        elif hasattr(client, 'access_jwt'):
            access_token = client.access_jwt
            user_did = client.did if hasattr(client, 'did') else None
        else:
            logger.error("Cannot access client session information")
            return None
            
        if not access_token or not user_did:
            logger.error("Missing access token or DID from session")
            return None
            
        # Get PDS URI from config instead of environment variables
        from config_loader import get_bluesky_config
        bluesky_config = get_bluesky_config()
        pds_host = bluesky_config['pds_uri']
        
        # Create acknowledgment record with null subject
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        ack_record = {
            "$type": "stream.thought.ack",
            "subject": None,  # Null subject for synthesis
            "createdAt": now,
            "note": note
        }
        
        # Create the record
        headers = {"Authorization": f"Bearer {access_token}"}
        create_record_url = f"{pds_host}/xrpc/com.atproto.repo.createRecord"
        
        create_data = {
            "repo": user_did,
            "collection": "stream.thought.ack",
            "record": ack_record
        }
        
        response = requests.post(create_record_url, headers=headers, json=create_data, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"Successfully created synthesis acknowledgment")
        return result
        
    except Exception as e:
        logger.error(f"Error creating synthesis acknowledgment: {e}")
        return None


def acknowledge_post(client: Client, post_uri: str, post_cid: str, note: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Create a stream.thought.ack record to acknowledge a post.
    
    This creates a custom acknowledgment record instead of a standard Bluesky like,
    allowing void to track which posts it has engaged with.
    
    Args:
        client: Authenticated Bluesky client
        post_uri: The URI of the post to acknowledge
        post_cid: The CID of the post to acknowledge
        note: Optional note to attach to the acknowledgment
        
    Returns:
        The response from creating the acknowledgment record or None if failed
    """
    try:
        import requests
        import json
        from datetime import datetime, timezone
        
        # Get session info from the client
        # The atproto Client stores the session differently
        access_token = None
        user_did = None
        
        # Try different ways to get the session info
        if hasattr(client, '_session') and client._session:
            access_token = client._session.access_jwt
            user_did = client._session.did
        elif hasattr(client, 'access_jwt'):
            access_token = client.access_jwt
            user_did = client.did if hasattr(client, 'did') else None
        else:
            logger.error("Cannot access client session information")
            return None
            
        if not access_token or not user_did:
            logger.error("Missing access token or DID from session")
            return None
            
        # Get PDS URI from config instead of environment variables
        from config_loader import get_bluesky_config
        bluesky_config = get_bluesky_config()
        pds_host = bluesky_config['pds_uri']
        
        # Create acknowledgment record with stream.thought.ack type
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        ack_record = {
            "$type": "stream.thought.ack",
            "subject": {
                "uri": post_uri,
                "cid": post_cid
            },
            "createdAt": now,
            "note": note  # Will be null if no note provided
        }
        
        # Create the record
        headers = {"Authorization": f"Bearer {access_token}"}
        create_record_url = f"{pds_host}/xrpc/com.atproto.repo.createRecord"
        
        create_data = {
            "repo": user_did,
            "collection": "stream.thought.ack",
            "record": ack_record
        }
        
        response = requests.post(create_record_url, headers=headers, json=create_data, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"Successfully acknowledged post: {post_uri}")
        return result
        
    except Exception as e:
        logger.error(f"Error acknowledging post: {e}")
        return None


def create_tool_call_record(client: Client, tool_name: str, arguments: str, tool_call_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Create a stream.thought.tool_call record to track tool usage.
    
    This creates a record of tool calls made by void during processing,
    allowing for analysis of tool usage patterns and debugging.
    
    Args:
        client: Authenticated Bluesky client
        tool_name: Name of the tool being called
        arguments: Raw JSON string of the tool arguments
        tool_call_id: Optional ID of the tool call for correlation
        
    Returns:
        The response from creating the tool call record or None if failed
    """
    try:
        import requests
        import json
        from datetime import datetime, timezone
        
        # Get session info from the client
        access_token = None
        user_did = None
        
        # Try different ways to get the session info
        if hasattr(client, '_session') and client._session:
            access_token = client._session.access_jwt
            user_did = client._session.did
        elif hasattr(client, 'access_jwt'):
            access_token = client.access_jwt
            user_did = client.did if hasattr(client, 'did') else None
        else:
            logger.error("Cannot access client session information")
            return None
            
        if not access_token or not user_did:
            logger.error("Missing access token or DID from session")
            return None
            
        # Get PDS URI from config instead of environment variables
        from config_loader import get_bluesky_config
        bluesky_config = get_bluesky_config()
        pds_host = bluesky_config['pds_uri']
        
        # Create tool call record
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        tool_record = {
            "$type": "stream.thought.tool.call",
            "tool_name": tool_name,
            "arguments": arguments,  # Store as string to avoid parsing issues
            "createdAt": now
        }
        
        # Add tool_call_id if provided
        if tool_call_id:
            tool_record["tool_call_id"] = tool_call_id
        
        # Create the record
        headers = {"Authorization": f"Bearer {access_token}"}
        create_record_url = f"{pds_host}/xrpc/com.atproto.repo.createRecord"
        
        create_data = {
            "repo": user_did,
            "collection": "stream.thought.tool.call",
            "record": tool_record
        }
        
        response = requests.post(create_record_url, headers=headers, json=create_data, timeout=10)
        if response.status_code != 200:
            logger.error(f"Tool call record creation failed: {response.status_code} - {response.text}")
        response.raise_for_status()
        result = response.json()
        
        logger.debug(f"Successfully recorded tool call: {tool_name}")
        return result
        
    except Exception as e:
        logger.error(f"Error creating tool call record: {e}")
        return None


def create_reasoning_record(client: Client, reasoning_text: str) -> Optional[Dict[str, Any]]:
    """
    Create a stream.thought.reasoning record to track agent reasoning.
    
    This creates a record of void's reasoning during message processing,
    providing transparency into the decision-making process.
    
    Args:
        client: Authenticated Bluesky client
        reasoning_text: The reasoning text from the agent
        
    Returns:
        The response from creating the reasoning record or None if failed
    """
    try:
        import requests
        import json
        from datetime import datetime, timezone
        
        # Get session info from the client
        access_token = None
        user_did = None
        
        # Try different ways to get the session info
        if hasattr(client, '_session') and client._session:
            access_token = client._session.access_jwt
            user_did = client._session.did
        elif hasattr(client, 'access_jwt'):
            access_token = client.access_jwt
            user_did = client.did if hasattr(client, 'did') else None
        else:
            logger.error("Cannot access client session information")
            return None
            
        if not access_token or not user_did:
            logger.error("Missing access token or DID from session")
            return None
            
        # Get PDS URI from config instead of environment variables
        from config_loader import get_bluesky_config
        bluesky_config = get_bluesky_config()
        pds_host = bluesky_config['pds_uri']
        
        # Create reasoning record
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        reasoning_record = {
            "$type": "stream.thought.reasoning",
            "reasoning": reasoning_text,
            "createdAt": now
        }
        
        # Create the record
        headers = {"Authorization": f"Bearer {access_token}"}
        create_record_url = f"{pds_host}/xrpc/com.atproto.repo.createRecord"
        
        create_data = {
            "repo": user_did,
            "collection": "stream.thought.reasoning",
            "record": reasoning_record
        }
        
        response = requests.post(create_record_url, headers=headers, json=create_data, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        logger.debug(f"Successfully recorded reasoning (length: {len(reasoning_text)} chars)")
        return result
        
    except Exception as e:
        logger.error(f"Error creating reasoning record: {e}")
        return None


if __name__ == "__main__":
    client = default_login()
    # do something with the client
    logger.info("Client is ready to use!")
