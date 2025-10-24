# Sanctum Social API Documentation

This document provides comprehensive API documentation for Sanctum Social, the multi-platform AI agent framework.

## Table of Contents

- [Core API](#core-api)
- [Configuration API](#configuration-api)
- [Memory Management API](#memory-management-api)
- [Platform APIs](#platform-apis)
- [Tool Management API](#tool-management-api)
- [Queue Management API](#queue-management-api)
- [Session Management API](#session-management-api)
- [Error Handling](#error-handling)
- [Examples](#examples)

## Core API

### Agent Initialization

#### `initialize_agent() -> Agent`

Initialize an agent for platform operations.

**Returns:**
- `Agent`: The initialized agent object

**Raises:**
- `Exception`: If agent initialization fails

**Example:**
```python
from platforms.bluesky.orchestrator import initialize_agent

agent = initialize_agent()
print(f"Agent initialized: {agent.name}")
```

### Configuration Management

#### `get_config() -> ConfigLoader`

Get the current configuration loader instance.

**Returns:**
- `ConfigLoader`: Configuration loader with access to all settings

**Example:**
```python
from core.config import get_config

config = get_config()
agent_name = config.get_agent_name()
print(f"Agent name: {agent_name}")
```

#### `get_letta_config() -> Dict[str, Any]`

Get Letta-specific configuration.

**Returns:**
- `Dict[str, Any]`: Letta configuration dictionary

**Example:**
```python
from core.config import get_letta_config

letta_config = get_letta_config()
api_key = letta_config['api_key']
```

## Configuration API

### ConfigLoader Class

The `ConfigLoader` class provides access to all configuration settings.

#### Methods

##### `get(key: str, default: Any = None) -> Any`

Get a configuration value by key.

**Parameters:**
- `key`: Configuration key (supports dot notation for nested keys)
- `default`: Default value if key not found

**Returns:**
- Configuration value or default

**Example:**
```python
config = get_config()
username = config.get('platforms.bluesky.username')
timeout = config.get('letta.timeout', 30)
```

##### `get_agent_name() -> str`

Get the configured agent name.

**Returns:**
- Agent name string

##### `get_agent_config() -> Dict[str, Any]`

Get the complete agent configuration.

**Returns:**
- Agent configuration dictionary

##### `get_memory_blocks_config() -> Dict[str, Any]`

Get memory blocks configuration.

**Returns:**
- Memory blocks configuration dictionary

##### `get_platform_config(platform: str) -> Dict[str, Any]`

Get platform-specific configuration.

**Parameters:**
- `platform`: Platform name ('bluesky', 'x', 'discord')

**Returns:**
- Platform configuration dictionary

##### `is_platform_enabled(platform: str) -> bool`

Check if a platform is enabled.

**Parameters:**
- `platform`: Platform name

**Returns:**
- True if platform is enabled

##### `get_stop_command() -> str`

Get the configured stop command.

**Returns:**
- Stop command string

### Configuration Functions

#### `template_config(config: Dict[str, Any], agent_name: str) -> Dict[str, Any]`

Template configuration values with agent name and other variables.

**Parameters:**
- `config`: Configuration dictionary
- `agent_name`: Agent name for templating

**Returns:**
- Templated configuration dictionary

#### `generate_synthesis_prompt(config: Dict[str, Any], today: datetime) -> str`

Generate synthesis prompt using configuration.

**Parameters:**
- `config`: Configuration dictionary
- `today`: Current date

**Returns:**
- Generated synthesis prompt

#### `generate_mention_prompt(config: Dict[str, Any], platform: str, author_handle: str, author_name: str, mention_text: str, thread_context: str) -> str`

Generate mention prompt for platform interactions.

**Parameters:**
- `config`: Configuration dictionary
- `platform`: Platform name
- `author_handle`: Author's handle
- `author_name`: Author's display name
- `mention_text`: Mention text content
- `thread_context`: Thread context

**Returns:**
- Generated mention prompt

## Memory Management API

### Memory Block Operations

#### `upsert_block(client: Client, label: str, value: str, **kwargs) -> Block`

Create or update a memory block.

**Parameters:**
- `client`: Letta client instance
- `label`: Block label
- `value`: Block value
- `**kwargs`: Additional block parameters

**Returns:**
- Created or updated block

**Example:**
```python
from utils import upsert_block

block = upsert_block(
    client=client,
    label="user-profile",
    value="User is interested in AI and technology",
    description="User profile information"
)
```

#### `get_memory_blocks(client: Client, agent_id: str) -> List[Block]`

Get all memory blocks for an agent.

**Parameters:**
- `client`: Letta client instance
- `agent_id`: Agent ID

**Returns:**
- List of memory blocks

#### `attach_temporal_blocks(client: Client, agent_id: str) -> List[Block]`

Attach temporal memory blocks for the current time period.

**Parameters:**
- `client`: Letta client instance
- `agent_id`: Agent ID

**Returns:**
- List of attached temporal blocks

#### `detach_temporal_blocks(client: Client, agent_id: str, block_labels: List[str]) -> bool`

Detach temporal memory blocks.

**Parameters:**
- `client`: Letta client instance
- `agent_id`: Agent ID
- `block_labels`: List of block labels to detach

**Returns:**
- True if successful

### Memory Search

#### `search_memory(client: Client, query: str, limit: int = 10) -> List[Block]`

Search memory blocks by content.

**Parameters:**
- `client`: Letta client instance
- `query`: Search query
- `limit`: Maximum number of results

**Returns:**
- List of matching memory blocks

## Platform APIs

### Bluesky Platform

#### `initialize_bluesky_client() -> Client`

Initialize Bluesky client with configuration.

**Returns:**
- Bluesky client instance

#### `post_to_bluesky(text: str, reply_to: Optional[str] = None) -> Dict[str, Any]`

Post content to Bluesky.

**Parameters:**
- `text`: Post text content
- `reply_to`: Optional reply-to URI

**Returns:**
- Post creation result

#### `get_bluesky_feed(feed_name: str = None, max_posts: int = 25) -> str`

Get Bluesky feed content.

**Parameters:**
- `feed_name`: Feed name ('home', 'discover', etc.)
- `max_posts`: Maximum number of posts

**Returns:**
- Feed content as YAML string

#### `research_bluesky_profile(username: str) -> str`

Research a Bluesky user profile.

**Parameters:**
- `username`: Username to research

**Returns:**
- Profile research results

### X (Twitter) Platform

#### `initialize_x_client() -> XClient`

Initialize X client with OAuth1 authentication.

**Returns:**
- X client instance

#### `post_to_x(text: str) -> Dict[str, Any]`

Post content to X (Twitter).

**Parameters:**
- `text`: Tweet text content

**Returns:**
- Tweet creation result

#### `search_x_posts(username: str, max_results: int = 10, exclude_replies: bool = False, exclude_retweets: bool = False) -> str`

Search X posts by username.

**Parameters:**
- `username`: Username to search
- `max_results`: Maximum number of results
- `exclude_replies`: Exclude reply tweets
- `exclude_retweets`: Exclude retweets

**Returns:**
- Search results as YAML string

### Discord Platform

#### `initialize_discord_client() -> discord.Client`

Initialize Discord client.

**Returns:**
- Discord client instance

#### `create_discord_post(messages: List[str], channel_id: str = None) -> str`

Create Discord post.

**Parameters:**
- `messages`: List of message texts
- `channel_id`: Optional channel ID

**Returns:**
- Post creation result

#### `search_discord_messages(query: str, max_results: int = 10, channel_id: str = None) -> str`

Search Discord messages.

**Parameters:**
- `query`: Search query
- `max_results`: Maximum number of results
- `channel_id`: Optional channel ID

**Returns:**
- Search results as YAML string

## Tool Management API

### Tool Registration

#### `register_tools(agent_id: str, tools: List[str] = None) -> List[Tool]`

Register tools with an agent.

**Parameters:**
- `agent_id`: Agent ID
- `tools`: List of tool names (None for all available)

**Returns:**
- List of registered tools

**Example:**
```python
from scripts.register_tools import register_tools

tools = register_tools(
    agent_id="my-agent",
    tools=["search_bluesky_posts", "create_new_bluesky_post"]
)
```

#### `list_available_tools(platform: str = None) -> List[str]`

List available tools for a platform.

**Parameters:**
- `platform`: Platform name (None for all platforms)

**Returns:**
- List of available tool names

### Tool Execution

Tools are executed through the Letta framework. Each tool has a specific signature and return format.

#### Tool Signatures

All tools follow this pattern:

```python
def tool_name(param1: str, param2: int = 10) -> str:
    """
    Tool description.
    
    Args:
        param1: Description of parameter
        param2: Description of parameter with default
        
    Returns:
        Tool result as string
    """
```

## Queue Management API

### Queue Operations

#### `save_notification_to_queue(notification: Dict[str, Any], priority: bool = False) -> bool`

Save notification to processing queue.

**Parameters:**
- `notification`: Notification data
- `priority`: Whether to prioritize this notification

**Returns:**
- True if successful

#### `load_and_process_queued_notifications() -> int`

Load and process queued notifications.

**Returns:**
- Number of notifications processed

#### `get_queue_stats() -> Dict[str, Any]`

Get queue statistics.

**Returns:**
- Queue statistics dictionary

### Queue Health Monitoring

#### `check_queue_health() -> Dict[str, Any]`

Check queue health and status.

**Returns:**
- Queue health information

#### `repair_queue() -> bool`

Repair corrupted queue files.

**Returns:**
- True if repair successful

## Session Management API

### Session Operations

#### `get_session(username: str) -> Optional[str]`

Get saved session for username.

**Parameters:**
- `username`: Username

**Returns:**
- Session data or None

#### `save_session(username: str, session_data: str) -> bool`

Save session data for username.

**Parameters:**
- `username`: Username
- `session_data`: Session data

**Returns:**
- True if successful

#### `cleanup_old_sessions() -> int`

Clean up old session files.

**Returns:**
- Number of sessions cleaned up

### Session Retry Logic

#### `get_session_with_retry(username: str, max_retries: int = 3) -> Optional[str]`

Get session with retry logic.

**Parameters:**
- `username`: Username
- `max_retries`: Maximum retry attempts

**Returns:**
- Session data or None

#### `save_session_with_retry(username: str, session_data: str, max_retries: int = 3, validate: bool = True) -> bool`

Save session with retry logic.

**Parameters:**
- `username`: Username
- `session_data`: Session data
- `max_retries`: Maximum retry attempts
- `validate`: Whether to validate session data

**Returns:**
- True if successful

## Error Handling

### Exception Types

#### `ConfigurationError`

Raised when configuration is invalid or missing.

```python
from core.config import ConfigurationError

try:
    config = get_config()
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

#### `PlatformError`

Raised when platform operations fail.

```python
from platforms.bluesky.orchestrator import PlatformError

try:
    result = post_to_bluesky("Hello world")
except PlatformError as e:
    print(f"Platform error: {e}")
```

#### `MemoryError`

Raised when memory operations fail.

```python
from utils import MemoryError

try:
    block = upsert_block(client, "test", "value")
except MemoryError as e:
    print(f"Memory error: {e}")
```

### Error Recovery

#### `retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0)`

Retry function with exponential backoff.

**Parameters:**
- `func`: Function to retry
- `max_retries`: Maximum retry attempts
- `base_delay`: Base delay between retries

**Example:**
```python
from utils import retry_with_backoff

@retry_with_backoff(max_retries=3)
def api_call():
    # API call implementation
    pass
```

## Examples

### Basic Agent Setup

```python
from core.config import get_config
from platforms.bluesky.orchestrator import initialize_agent
from utils import upsert_block

# Initialize configuration and agent
config = get_config()
agent = initialize_agent()

# Create a memory block
block = upsert_block(
    client=agent.client,
    label="test-block",
    value="This is a test memory block",
    description="Test block for demonstration"
)

print(f"Agent {agent.name} initialized with {len(agent.memory_blocks)} memory blocks")
```

### Platform-Specific Operations

```python
from platforms.bluesky.tools.post import create_new_bluesky_post
from platforms.x.tools.post import post_to_x
from platforms.discord.tools.post import create_discord_post

# Post to different platforms
bluesky_result = create_new_bluesky_post("Hello from Bluesky!")
x_result = post_to_x("Hello from X!")
discord_result = create_discord_post(["Hello from Discord!"])

print("Posted to all platforms successfully")
```

### Memory Management

```python
from utils import upsert_block, search_memory
from core.config import get_config

config = get_config()
client = config.get_letta_client()

# Create user profile block
user_block = upsert_block(
    client=client,
    label="user-alice",
    value="Alice is interested in AI, machine learning, and robotics.",
    description="Profile information for user Alice"
)

# Search for AI-related blocks
ai_blocks = search_memory(client, "artificial intelligence", limit=5)
print(f"Found {len(ai_blocks)} AI-related memory blocks")
```

### Queue Management

```python
from utils.queue_manager import save_notification_to_queue, load_and_process_queued_notifications

# Save notification to queue
notification = {
    "id": "notif-123",
    "text": "Hello world",
    "author": "alice.bsky.social",
    "platform": "bluesky"
}

success = save_notification_to_queue(notification, priority=True)
if success:
    print("Notification queued successfully")

# Process queued notifications
processed = load_and_process_queued_notifications()
print(f"Processed {processed} notifications")
```

### Error Handling

```python
from core.config import ConfigurationError
from platforms.bluesky.orchestrator import PlatformError
from utils import retry_with_backoff

try:
    config = get_config()
    agent = initialize_agent()
    
    @retry_with_backoff(max_retries=3)
    def post_with_retry():
        return agent.post("Hello world!")
    
    result = post_with_retry()
    print("Post successful")
    
except ConfigurationError as e:
    print(f"Configuration error: {e}")
except PlatformError as e:
    print(f"Platform error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## API Reference Summary

### Core Classes

- **ConfigLoader**: Configuration management
- **Agent**: Agent instance with memory and tools
- **Client**: Platform-specific client instances

### Key Functions

- **Configuration**: `get_config()`, `get_letta_config()`
- **Agent Management**: `initialize_agent()`
- **Memory**: `upsert_block()`, `search_memory()`
- **Platforms**: Platform-specific posting and search functions
- **Tools**: `register_tools()`, `list_available_tools()`
- **Queue**: `save_notification_to_queue()`, `load_and_process_queued_notifications()`
- **Sessions**: `get_session()`, `save_session()`

### Error Types

- **ConfigurationError**: Configuration issues
- **PlatformError**: Platform operation failures
- **MemoryError**: Memory operation failures

For more detailed examples and platform-specific APIs, see the individual platform documentation files in the `docs/` directory.