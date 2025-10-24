# Sanctum Social Architecture Guide

This document provides a comprehensive overview of the Sanctum Social architecture, design principles, and system components.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Core Components](#core-components)
- [Platform Abstraction](#platform-abstraction)
- [Memory System](#memory-system)
- [Configuration System](#configuration-system)
- [Tool Management](#tool-management)
- [Queue Management](#queue-management)
- [Session Management](#session-management)
- [Error Handling](#error-handling)
- [Security Architecture](#security-architecture)
- [Performance Considerations](#performance-considerations)
- [Extensibility](#extensibility)

## Architecture Overview

Sanctum Social is built on a modular, platform-agnostic architecture that separates concerns and enables easy extension. The system is designed around the following core principles:

### Design Principles

1. **Modularity**: Clear separation of concerns with well-defined interfaces
2. **Platform Agnostic**: Unified interface for different social media platforms
3. **Agent Generalization**: Support for any agent identity and personality
4. **Extensibility**: Easy addition of new platforms and capabilities
5. **Reliability**: Robust error handling and recovery mechanisms
6. **Scalability**: Designed for both single-instance and distributed deployments

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Sanctum Social                          │
├─────────────────────────────────────────────────────────────┤
│  Agent Layer                                               │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │   Agent Config  │ │  Memory Mgmt    │ │  Tool Registry  │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Platform Abstraction Layer                                │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │    Bluesky      │ │       X         │ │    Discord      │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Core Services Layer                                       │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │ Queue Management│ │ Session Mgmt    │ │ Error Handling  │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Infrastructure Layer                                      │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │ Configuration   │ │    Logging      │ │   Monitoring    │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### Agent Configuration System

The agent configuration system provides flexible, templated configuration for agent identity, personality, and behavior.

#### Configuration Structure

```yaml
agent:
  name: "agent-name"                    # Unique agent identifier
  display_name: "Agent Display Name"    # Human-readable name
  description: "Agent description"    # Agent description
  
  personality:
    core_identity: "Agent identity"     # Core personality
    development_directive: "Directive"  # Development goal
    communication_style: "style"       # Communication style
    tone: "tone"                        # Communication tone
    
  capabilities:
    model: "openai/gpt-4o-mini"         # LLM model
    embedding: "openai/text-embedding-3-small"  # Embedding model
    max_steps: 100                      # Maximum processing steps
    
  memory_blocks:
    zeitgeist:                          # Social environment
      label: "zeitgeist"
      value: "Current social state"
    persona:                            # Agent personality
      label: "{agent_name}-persona"
      value: "{personality.core_identity}"
    humans:                             # User information
      label: "{agent_name}-humans"
      value: "User knowledge base"
```

#### Configuration Templating

The system supports templating with placeholders:

- `{agent_name}`: Agent name
- `{personality.core_identity}`: Core identity
- `{personality.development_directive}`: Development directive
- `{timestamp}`: Current timestamp
- `{date}`: Current date

### Memory Management System

Sanctum Social implements a sophisticated multi-tiered memory system designed for persistent, learning AI agents.

#### Memory Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Memory System                            │
├─────────────────────────────────────────────────────────────┤
│  Core Memory (Always Available)                            │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │    Persona      │ │   Zeitgeist     │ │    Humans       │ │
│  │   (Limited)     │ │   (Limited)     │ │   (Limited)     │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Recall Memory (Searchable Database)                       │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │           Conversation History                          │ │
│  │         (Semantic Search)                              │ │
│  └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Archival Memory (Infinite Storage)                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │           Deep Reflections                             │ │
│  │         Insights & Observations                        │ │
│  │         (Semantic Search)                              │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

#### Memory Types

1. **Core Memory**: Always-available, limited-size memory for essential information
2. **Recall Memory**: Searchable database of all past conversations
3. **Archival Memory**: Infinite-sized, semantic search-enabled storage for insights

#### Memory Operations

```python
# Create/Update memory block
block = upsert_block(
    client=client,
    label="user-profile",
    value="User information",
    description="User profile data"
)

# Search memory
results = search_memory(client, "artificial intelligence", limit=10)

# Attach temporal blocks
temporal_blocks = attach_temporal_blocks(client, agent_id)

# Detach temporal blocks
detach_temporal_blocks(client, agent_id, block_labels)
```

### Platform Abstraction Layer

The platform abstraction layer provides a unified interface for different social media platforms while maintaining platform-specific optimizations.

#### Platform Interface

```python
class PlatformInterface:
    def initialize_client(self) -> Client:
        """Initialize platform client."""
        pass
    
    def post_content(self, text: str, **kwargs) -> Dict[str, Any]:
        """Post content to platform."""
        pass
    
    def search_content(self, query: str, **kwargs) -> str:
        """Search platform content."""
        pass
    
    def get_user_profile(self, username: str) -> str:
        """Get user profile information."""
        pass
```

#### Platform Implementations

##### Bluesky Platform

```python
class BlueskyPlatform(PlatformInterface):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None
    
    def initialize_client(self) -> Client:
        """Initialize Bluesky client."""
        return Client(
            base_url=self.config['pds_uri'],
            username=self.config['username'],
            password=self.config['password']
        )
    
    def post_content(self, text: str, reply_to: str = None) -> Dict[str, Any]:
        """Post to Bluesky."""
        return self.client.post(text, reply_to=reply_to)
```

##### X (Twitter) Platform

```python
class XPlatform(PlatformInterface):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None
    
    def initialize_client(self) -> XClient:
        """Initialize X client with OAuth1."""
        return XClient(
            api_key=self.config['api_key'],
            consumer_key=self.config['consumer_key'],
            consumer_secret=self.config['consumer_secret'],
            access_token=self.config['access_token'],
            access_token_secret=self.config['access_token_secret']
        )
    
    def post_content(self, text: str) -> Dict[str, Any]:
        """Post to X."""
        return self.client.post_tweet(text)
```

##### Discord Platform

```python
class DiscordPlatform(PlatformInterface):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None
    
    def initialize_client(self) -> discord.Client:
        """Initialize Discord client."""
        return discord.Client(intents=discord.Intents.default())
    
    def post_content(self, messages: List[str], channel_id: str = None) -> str:
        """Post to Discord."""
        return self.client.post_messages(messages, channel_id)
```

## Tool Management System

The tool management system provides dynamic tool registration and platform-specific capabilities.

### Tool Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Tool Management                          │
├─────────────────────────────────────────────────────────────┤
│  Tool Registry                                              │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │  Platform Tools │ │  Shared Tools    │ │  Custom Tools    │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Tool Execution Engine                                      │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │  Validation     │ │  Execution      │ │  Result Format   │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Tool Categories

#### Platform-Specific Tools

- **Bluesky Tools**: `create_new_bluesky_post`, `search_bluesky_posts`, `research_bluesky_profile`
- **X Tools**: `post_to_x`, `search_x_posts`, `create_x_thread`
- **Discord Tools**: `create_discord_post`, `search_discord_messages`, `ignore_discord_users`

#### Shared Tools

- **Web Tools**: `fetch_webpage`, `create_whitewind_blog_post`
- **Memory Tools**: `attach_user_block`, `update_user_block`, `detach_user_block`
- **Utility Tools**: `check_known_bots`, `should_respond_to_bot_thread`

### Tool Registration

```python
# Register platform-specific tools
register_tools(agent_id="my-agent", platform="bluesky")

# Register specific tools
register_tools(agent_id="my-agent", tools=["search_bluesky_posts", "create_new_bluesky_post"])

# List available tools
available_tools = list_available_tools(platform="bluesky")
```

## Queue Management System

The queue management system handles notification processing with robust error recovery and monitoring.

### Queue Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Queue Management                         │
├─────────────────────────────────────────────────────────────┤
│  Notification Queue                                        │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │   New Queue     │ │  Error Queue     │ │ No Reply Queue  │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Processing Engine                                          │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │  Load Queue     │ │  Process Items   │ │  Update Status   │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Health Monitoring                                          │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │  Queue Stats    │ │  Error Tracking │ │  Performance     │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Queue Operations

```python
# Save notification to queue
save_notification_to_queue(notification, priority=True)

# Process queued notifications
processed_count = load_and_process_queued_notifications()

# Get queue statistics
stats = get_queue_stats()

# Check queue health
health = check_queue_health()

# Repair corrupted queue
repair_queue()
```

### Error Classification

The system classifies errors into different types for appropriate handling:

- **Transient Errors**: Network issues, temporary API failures
- **Permanent Errors**: Invalid credentials, permission denied
- **Queue Errors**: File system issues, corruption
- **Health Errors**: Resource exhaustion, system overload

## Session Management System

The session management system handles authentication sessions with automatic retry logic and cleanup.

### Session Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Session Management                      │
├─────────────────────────────────────────────────────────────┤
│  Session Storage                                            │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │  Active Sessions│ │  Expired Sessions│ │  Corrupted Files│ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Session Operations                                         │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │  Create Session │ │  Validate Session│ │  Refresh Session│ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Retry Logic                                                │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │  Exponential    │ │  Max Retries     │ │  Error Handling │ │
│  │  Backoff        │ │  Configuration   │ │  & Recovery     │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Session Operations

```python
# Get session with retry
session = get_session_with_retry(username, max_retries=3)

# Save session with retry
success = save_session_with_retry(username, session_data, max_retries=3)

# Cleanup old sessions
cleaned_count = cleanup_old_sessions()

# Validate session
is_valid = validate_session(session_data)
```

## Error Handling System

Sanctum Social implements comprehensive error handling with automatic recovery and monitoring.

### Error Handling Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Error Handling                          │
├─────────────────────────────────────────────────────────────┤
│  Error Classification                                      │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │  Transient      │ │  Permanent      │ │  System          │ │
│  │  Errors         │ │  Errors         │ │  Errors         │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Recovery Mechanisms                                        │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │  Retry Logic    │ │  Fallback       │ │  Graceful       │ │
│  │  & Backoff      │ │  Strategies     │ │  Degradation    │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Monitoring & Alerting                                      │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │  Error Tracking │ │  Performance     │ │  Health Checks   │ │
│  │  & Logging      │ │  Monitoring     │ │  & Alerts        │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Error Recovery Strategies

#### Retry Logic

```python
@retry_with_backoff(max_retries=3, base_delay=1.0)
def api_call():
    """API call with automatic retry."""
    try:
        return external_api.call()
    except TransientError as e:
        logger.warning(f"Transient error: {e}")
        raise  # Will trigger retry
    except PermanentError as e:
        logger.error(f"Permanent error: {e}")
        raise  # Will not retry
```

#### Fallback Strategies

```python
def post_with_fallback(text: str, platform: str):
    """Post with fallback strategy."""
    try:
        return post_to_primary_platform(text, platform)
    except PrimaryPlatformError:
        logger.warning("Primary platform failed, trying fallback")
        return post_to_fallback_platform(text, platform)
```

## Security Architecture

Sanctum Social implements multiple layers of security to protect credentials, data, and system integrity.

### Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Architecture                    │
├─────────────────────────────────────────────────────────────┤
│  Credential Management                                      │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │  Environment    │ │  Secret         │ │  Encryption      │ │
│  │  Variables      │ │  Management     │ │  at Rest        │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Network Security                                           │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │  TLS/SSL        │ │  Firewall       │ │  Rate Limiting   │ │
│  │  Encryption     │ │  Rules          │ │  & DDoS         │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Application Security                                       │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │  Input          │ │  Authentication │ │  Authorization  │ │
│  │  Validation     │ │  & Session      │ │  & Access       │ │
│  │  & Sanitization │ │  Management     │ │  Control        │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Security Measures

#### Credential Protection

```python
# Use environment variables
import os
api_key = os.getenv('LETTA_API_KEY')

# Use secret management
from aws_secrets_manager import get_secret
api_key = get_secret('sanctum-social/credentials')['letta_api_key']

# Encrypt sensitive data
from cryptography.fernet import Fernet
cipher = Fernet(key)
encrypted_data = cipher.encrypt(sensitive_data.encode())
```

#### Input Validation

```python
from pydantic import BaseModel, validator

class PostRequest(BaseModel):
    text: str
    platform: str
    
    @validator('text')
    def validate_text(cls, v):
        if len(v) > 300:
            raise ValueError('Text too long')
        if '<script>' in v.lower():
            raise ValueError('Invalid content')
        return v
    
    @validator('platform')
    def validate_platform(cls, v):
        allowed_platforms = ['bluesky', 'x', 'discord']
        if v not in allowed_platforms:
            raise ValueError('Invalid platform')
        return v
```

#### Rate Limiting

```python
from functools import wraps
import time

def rate_limit(calls_per_minute=60):
    def decorator(func):
        calls = []
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            calls[:] = [call for call in calls if now - call < 60]
            
            if len(calls) >= calls_per_minute:
                raise RateLimitError("Rate limit exceeded")
            
            calls.append(now)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
```

## Performance Considerations

### Performance Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Performance Architecture                 │
├─────────────────────────────────────────────────────────────┤
│  Caching Layer                                              │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │  Memory Cache   │ │  Disk Cache     │ │  Session Cache   │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Optimization Strategies                                   │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │  Lazy Loading   │ │  Connection     │ │  Batch          │ │
│  │  & Initialization│ │  Pooling        │ │  Processing     │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Resource Management                                        │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│  │  Memory         │ │  CPU            │ │  Network        │ │
│  │  Management     │ │  Optimization   │ │  Optimization   │ │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Performance Optimizations

#### Caching Strategy

```python
from functools import lru_cache
import time

# Memory caching
@lru_cache(maxsize=128)
def get_user_profile(username: str):
    """Get user profile with caching."""
    return fetch_user_profile(username)

# Disk caching
def get_cached_data(key: str, ttl: int = 3600):
    """Get data from disk cache."""
    cache_file = f"cache/{key}.json"
    if os.path.exists(cache_file):
        if time.time() - os.path.getmtime(cache_file) < ttl:
            with open(cache_file, 'r') as f:
                return json.load(f)
    return None
```

#### Connection Pooling

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Create session with connection pooling
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)
```

#### Batch Processing

```python
def process_notifications_batch(notifications: List[Dict], batch_size: int = 10):
    """Process notifications in batches."""
    for i in range(0, len(notifications), batch_size):
        batch = notifications[i:i + batch_size]
        process_batch(batch)
        time.sleep(0.1)  # Rate limiting
```

## Extensibility

### Extension Points

Sanctum Social is designed for easy extension through well-defined interfaces:

#### Platform Extensions

```python
class CustomPlatform(PlatformInterface):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def initialize_client(self) -> Client:
        """Initialize custom platform client."""
        pass
    
    def post_content(self, text: str, **kwargs) -> Dict[str, Any]:
        """Post to custom platform."""
        pass
```

#### Tool Extensions

```python
def custom_tool(param1: str, param2: int = 10) -> str:
    """
    Custom tool for specific functionality.
    
    Args:
        param1: Description of parameter
        param2: Description of parameter with default
        
    Returns:
        Tool result as string
    """
    # Tool implementation
    return "Tool result"
```

#### Memory Extensions

```python
class CustomMemoryProvider:
    def store(self, key: str, value: Any) -> bool:
        """Store data in custom memory provider."""
        pass
    
    def retrieve(self, key: str) -> Any:
        """Retrieve data from custom memory provider."""
        pass
    
    def search(self, query: str) -> List[Any]:
        """Search data in custom memory provider."""
        pass
```

### Plugin Architecture

```python
class Plugin:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def initialize(self) -> bool:
        """Initialize plugin."""
        pass
    
    def cleanup(self) -> bool:
        """Cleanup plugin resources."""
        pass
    
    def get_tools(self) -> List[str]:
        """Get plugin tools."""
        pass
    
    def get_platforms(self) -> List[str]:
        """Get plugin platforms."""
        pass
```

---

## Conclusion

Sanctum Social's architecture is designed to be modular, extensible, and reliable. The system provides a solid foundation for building sophisticated AI agents that can operate across multiple social media platforms while maintaining high standards of performance, security, and maintainability.

The architecture supports:

- **Easy Platform Addition**: New platforms can be added by implementing the platform interface
- **Flexible Agent Configuration**: Agents can be customized through templated configuration
- **Robust Error Handling**: Comprehensive error recovery and monitoring
- **Scalable Deployment**: Support for both single-instance and distributed deployments
- **Security**: Multiple layers of security protection
- **Performance**: Optimized for high-performance operation

This architecture enables Sanctum Social to serve as a comprehensive framework for deploying AI agents across multiple social media platforms while maintaining the flexibility and reliability required for production use.