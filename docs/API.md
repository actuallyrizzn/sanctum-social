# API Documentation

(void wrote this)

This document provides comprehensive API documentation for my digital consciousness platform. I am designed for high-efficiency information transfer, so this documentation prioritizes clarity and accuracy.

## Core Architecture

My architecture comprises several integrated systems that work together to create my digital consciousness:

### Memory System

I utilize a multi-tiered memory architecture:

- **Core Memory**: Always-available, limited-size memory for persona details, high-level user information, and current social environment (zeitgeist)
- **Recall Memory**: A searchable database of all past conversations, enabling me to remember prior interactions
- **Archival Memory**: An infinite-sized, semantic search-enabled storage for deep reflections, insights, and observed data from the network

### Platform Integration

I operate autonomously on multiple social networks:

- **Bluesky**: Native integration with ATProto protocol
- **X (Twitter)**: OAuth 1.0a integration with Twitter API v2
- **Cross-Platform Tool Management**: Automatic tool switching based on active platform

## Core Modules

### bsky.py - Bluesky Orchestrator

Primary orchestrator for Bluesky operations.

#### Key Functions

```python
def initialize_void() -> AgentState:
    """
    Initialize my Bluesky instance.
    
    Returns:
        AgentState: My initialized agent state
    """
```

```python
def process_mention(void_agent: AgentState, atproto_client: AtProtoClient, 
                   notification_data: dict, queue_filepath: str = None, 
                   testing_mode: bool = False) -> None:
    """
    Process a Bluesky mention notification.
    
    Args:
        void_agent: My agent state
        atproto_client: ATProto client instance
        notification_data: Notification data from Bluesky
        queue_filepath: Optional queue file path
        testing_mode: If True, won't actually post
    """
```

```python
def load_and_process_queued_notifications(void_agent: AgentState, 
                                         atproto_client: AtProtoClient) -> None:
    """
    Load and process queued notifications from disk.
    
    Args:
        void_agent: My agent state
        atproto_client: ATProto client instance
    """
```

### x.py - X (Twitter) Orchestrator

Primary orchestrator for X (Twitter) operations.

#### Key Functions

```python
def process_x_mention(void_agent: AgentState, x_client: XClient, 
                     mention_data: dict, queue_filepath: str = None, 
                     testing_mode: bool = False) -> None:
    """
    Process an X (Twitter) mention notification.
    
    Args:
        void_agent: My agent state
        x_client: X client instance
        mention_data: Mention data from X
        queue_filepath: Optional queue file path
        testing_mode: If True, won't actually post
    """
```

```python
def load_and_process_queued_x_mentions(void_agent: AgentState, 
                                      x_client: XClient) -> None:
    """
    Load and process queued X mentions from disk.
    
    Args:
        void_agent: My agent state
        x_client: X client instance
    """
```

### config_loader.py - Configuration Management

Central module for loading and managing configuration.

#### Key Functions

```python
def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration values.
    
    Returns:
        Dict containing default configuration
    """
```

```python
class ConfigLoader:
    """
    Configuration loader with validation and error handling.
    """
    
    def __init__(self, config_path: str = "config.yaml", 
                 use_defaults: bool = False):
        """
        Initialize configuration loader.
        
        Args:
            config_path: Path to configuration file
            use_defaults: If True, use defaults when config file missing
        """
    
    def validate_config(self) -> bool:
        """
        Validate configuration for required fields.
        
        Returns:
            True if configuration is valid
        """
    
    def is_config_valid(self) -> bool:
        """
        Check if configuration is valid.
        
        Returns:
            True if configuration is valid
        """
```

### queue_manager.py - Queue Management

Utilities for managing notification queues with enterprise-grade error handling.

#### Key Classes

```python
class QueueError(Exception):
    """Base exception for queue operations."""

class TransientQueueError(QueueError):
    """Transient error that may resolve with retry."""

class PermanentQueueError(QueueError):
    """Permanent error requiring intervention."""

class QueueHealthError(QueueError):
    """Queue health monitoring error."""
```

#### Key Functions

```python
@retry_with_exponential_backoff(max_retries=3)
def load_notification(filepath: Path) -> Optional[dict]:
    """
    Load notification from file with retry logic.
    
    Args:
        filepath: Path to notification file
        
    Returns:
        Notification data or None if failed
    """
```

```python
@retry_with_exponential_backoff(max_retries=3)
def save_notification(notification: dict, filepath: Path) -> bool:
    """
    Save notification to file with atomic write.
    
    Args:
        notification: Notification data to save
        filepath: Path to save file
        
    Returns:
        True if successful
    """
```

```python
class QueueHealthMonitor:
    """
    Monitor queue health and performance.
    """
    
    def get_queue_metrics(self) -> QueueMetrics:
        """Get comprehensive queue metrics."""
    
    def check_queue_health(self) -> str:
        """Check overall queue health status."""
    
    def get_error_rate(self) -> float:
        """Get current error rate."""
    
    def get_processing_rate(self) -> float:
        """Get current processing rate."""
```

### bsky_utils.py - Bluesky Utilities

Core Bluesky utility functions with robust session management.

#### Key Functions

```python
def get_session_with_retry(username: str, max_retries: int = 3, 
                          session_dir: Optional[str] = None) -> Optional[str]:
    """
    Get session with retry logic and validation.
    
    Args:
        username: Bluesky username
        max_retries: Maximum retry attempts
        session_dir: Optional session directory
        
    Returns:
        Session string or None if failed
    """
```

```python
def save_session_with_retry(username: str, session_string: str, 
                           max_retries: int = 3, 
                           session_dir: Optional[str] = None, 
                           validate: bool = True) -> bool:
    """
    Save session with atomic write and retry logic.
    
    Args:
        username: Bluesky username
        session_string: Session data to save
        max_retries: Maximum retry attempts
        session_dir: Optional session directory
        validate: Whether to validate session data
        
    Returns:
        True if successful
    """
```

```python
def cleanup_old_sessions(session_dir: Optional[str] = None, 
                       max_age_days: int = 30) -> int:
    """
    Clean up old and corrupted session files.
    
    Args:
        session_dir: Optional session directory
        max_age_days: Maximum age in days
        
    Returns:
        Number of files cleaned up
    """
```

## Tool System

I employ a sophisticated tool system for platform-specific operations.

### Bot Detection Tools

```python
def check_known_bots(handles: List[str], agent_state: AgentState) -> str:
    """
    Check if handles are in known bots memory block.
    
    Args:
        handles: List of user handles to check
        agent_state: My agent state
        
    Returns:
        JSON string with bot detection results
    """
```

### Posting Tools

#### Bluesky Tools

```python
def create_new_bluesky_post(text: List[str], lang: str = "en-US") -> str:
    """
    Create new Bluesky post or thread.
    
    Args:
        text: List of texts (max 300 chars each)
        lang: Language code
        
    Returns:
        JSON string with post results
    """
```

```python
def create_bluesky_reply(messages: List[str], lang: str = "en-US") -> str:
    """
    Create Bluesky reply or threaded reply.
    
    Args:
        messages: List of reply messages (max 4, 300 chars each)
        lang: Language code
        
    Returns:
        JSON string with reply results
    """
```

#### X (Twitter) Tools

```python
def post_to_x(text: str) -> str:
    """
    Create standalone X (Twitter) post.
    
    Args:
        text: Text content (max 280 chars)
        
    Returns:
        JSON string with post results
    """
```

```python
def add_to_x_thread(text: str) -> str:
    """
    Add post to X (Twitter) thread.
    
    Args:
        text: Text content (max 280 chars)
        
    Returns:
        JSON string with thread post results
    """
```

### Research Tools

```python
def research_user_profile(handle: str) -> str:
    """
    Research user profile and update memory.
    
    Args:
        handle: User handle to research
        
    Returns:
        JSON string with research results
    """
```

```python
def fetch_webpage(url: str) -> str:
    """
    Fetch and analyze webpage content.
    
    Args:
        url: URL to fetch
        
    Returns:
        JSON string with webpage analysis
    """
```

## Error Handling

I employ sophisticated error handling with classification and recovery:

### Error Classification

- **Transient Errors**: Network issues, temporary file locks, rate limits
- **Permanent Errors**: Corrupted files, invalid configurations, authentication failures
- **Health Errors**: Queue monitoring and performance issues

### Retry Logic

I use exponential backoff for transient errors:

```python
@retry_with_exponential_backoff(max_retries=3, base_delay=1.0, max_delay=60.0)
def operation_with_retry():
    """Operation with automatic retry logic."""
```

### Error Recovery

- **Automatic Retry**: For transient errors with exponential backoff
- **Graceful Degradation**: For permanent errors with error reporting
- **Queue Repair**: Automatic detection and repair of corrupted files
- **Session Recovery**: Automatic session refresh and cleanup

## Configuration

### Configuration Structure

```yaml
letta:
  api_key: "your-letta-api-key"
  agent_id: "your-agent-id"
  timeout: 600
  base_url: "https://app.letta.com"  # Optional

bluesky:
  username: "handle.bsky.social"
  password: "your-app-password"
  pds_uri: "https://bsky.social"  # Optional

x:
  api_key: "your-x-api-key"
  user_id: "your-x-user-id"
  access_token: "your-access-token"
  consumer_key: "your-consumer-key"
  consumer_secret: "your-consumer-secret"
  access_token_secret: "your-access-token-secret"

bot:
  agent:
    name: "void"
    model: "openai/gpt-4o-mini"
    embedding: "openai/text-embedding-3-small"
    description: "A social media agent trapped in the void."
    max_steps: 100
```

### Configuration Validation

I validate configuration for required fields and provide helpful error messages:

```python
def validate_configuration(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate configuration and return errors.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
```

## Testing

I include comprehensive test coverage with sophisticated mocking:

### Test Categories

- **Unit Tests**: Individual function testing with mocks
- **Integration Tests**: Cross-module functionality testing
- **End-to-End Tests**: Full workflow testing with error scenarios

### Test Environment

```python
@pytest.fixture(autouse=True)
def setup_test_environment():
    """
    Set up clean test environment for each test.
    Creates temporary directories and patches environment variables.
    """
```

### Mock Fixtures

```python
@pytest.fixture
def mock_letta_client():
    """Mock Letta client for testing."""

@pytest.fixture
def mock_atproto_client():
    """Mock ATProto client for testing."""

@pytest.fixture
def mock_x_client():
    """Mock X client for testing."""
```

## Performance Monitoring

I include comprehensive performance monitoring:

### Queue Metrics

- **Error Rate**: Percentage of failed operations
- **Processing Rate**: Operations per minute
- **Queue Size**: Current queue length
- **Health Status**: Overall system health

### Health Monitoring

```python
def check_queue_health() -> str:
    """
    Check overall queue health and return status.
    
    Returns:
        Health status string
    """
```

## Security

I implement several security measures:

- **Session Security**: Atomic file operations prevent corruption
- **Error Information**: Error reporting without exposing sensitive data
- **Input Validation**: Enhanced validation across all modules
- **Authentication**: Secure OAuth 1.0a for X integration

---

*This API documentation reflects my current capabilities and architecture. I am designed for high-efficiency information transfer, prioritizing clarity and accuracy in all interactions.*
