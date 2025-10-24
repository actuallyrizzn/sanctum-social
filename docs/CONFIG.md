# Sanctum Social Configuration Guide

This guide provides comprehensive information about configuring Sanctum Social agents, platforms, and system settings.

## Table of Contents

- [Configuration Overview](#configuration-overview)
- [Agent Configuration](#agent-configuration)
- [Platform Configuration](#platform-configuration)
- [Memory Configuration](#memory-configuration)
- [Tool Configuration](#tool-configuration)
- [Queue Configuration](#queue-configuration)
- [Logging Configuration](#logging-configuration)
- [File Path Configuration](#file-path-configuration)
- [Advanced Configuration](#advanced-configuration)
- [Environment Variables](#environment-variables)
- [Configuration Validation](#configuration-validation)
- [Examples](#examples)

## Configuration Overview

Sanctum Social uses a flexible, templated configuration system that allows for complete customization of agent behavior, platform settings, and system parameters.

### Configuration File Structure

The main configuration file (`config.yaml`) follows this structure:

```yaml
# Agent Identity and Behavior
agent:
  name: "agent-name"
  display_name: "Agent Display Name"
  description: "Agent description"
  personality: { ... }
  capabilities: { ... }
  commands: { ... }
  memory_blocks: { ... }
  temporal_journals: { ... }
  file_paths: { ... }

# Platform Configurations
platforms:
  bluesky: { ... }
  x: { ... }
  discord: { ... }

# External Services
letta: { ... }

# System Settings
bot: { ... }
queue: { ... }
threading: { ... }
logging: { ... }
```

### Configuration Templating

Sanctum Social supports templating with placeholders that are dynamically replaced:

- `{agent_name}`: Agent name
- `{personality.core_identity}`: Core identity from personality
- `{personality.development_directive}`: Development directive
- `{timestamp}`: Current timestamp
- `{date}`: Current date

## Agent Configuration

### Basic Agent Identity

```yaml
agent:
  # Unique identifier for the agent
  name: "my-agent"
  
  # Human-readable display name
  display_name: "My Social Agent"
  
  # Agent description
  description: "A social media agent built with Sanctum Social"
```

### Agent Personality

   ```yaml
agent:
  personality:
    # Core identity statement
    core_identity: "I am a social media AI agent built with Sanctum Social. I interact across multiple platforms and learn from my experiences."
    
    # Development directive
    development_directive: "I must develop my personality and understanding of social dynamics."
    
    # Communication style
    communication_style: "direct, analytical, information-dense"
    
    # Communication tone
    tone: "professional"
```

### Agent Capabilities

```yaml
agent:
  capabilities:
    # LLM model to use
    model: "openai/gpt-4o-mini"
    
    # Embedding model for semantic search
    embedding: "openai/text-embedding-3-small"
    
    # Maximum processing steps per interaction
    max_steps: 100
```

### Agent Commands

```yaml
agent:
  commands:
    # Stop command for the agent
    stop_command: "#myagentstop"
    
    # How often to perform synthesis
    synthesis_frequency: "daily"
    
    # Whether to enable journaling
    journal_enabled: true
```

## Platform Configuration

### Bluesky Configuration

```yaml
platforms:
bluesky:
    # Enable/disable Bluesky platform
    enabled: true
    
    # Bluesky credentials
    username: "your-handle.bsky.social"
    password: "your-app-password"
    pds_uri: "https://bsky.social"
    
    # Platform-specific behavior
    behavior:
      synthesis_frequency: "daily"
      user_profiling: true
      thread_handling: "comprehensive"
```

### X (Twitter) Configuration

```yaml
platforms:
  x:
    # Enable/disable X platform
    enabled: false
    
    # X API credentials
    api_key: "your-x-api-key"
    consumer_key: "your-consumer-key"
    consumer_secret: "your-consumer-secret"
    access_token: "your-access-token"
    access_token_secret: "your-access-token-secret"
    user_id: "your-x-user-id"
    
    # Platform-specific behavior
    behavior:
      thread_handling: "conservative"
      rate_limiting: "strict"
      downrank_response_rate: 0.1
```

### Discord Configuration

```yaml
platforms:
  discord:
    # Enable/disable Discord platform
    enabled: false
    
    # Discord bot credentials
    bot_token: "your-discord-bot-token"
    guild_id: "your-guild-id"
    
    # Channel configuration
    channels:
      general: "general-channel-id"
      announcements: "announcements-channel-id"
    
    # Rate limiting
    rate_limit:
      cooldown_seconds: 5
      max_responses_per_minute: 10
    
    # Context settings
    context:
      message_history_limit: 10
    
    # Platform-specific behavior
    behavior:
      mention_only: true
      channel_default: "general"
```

## Memory Configuration

### Core Memory Blocks

```yaml
agent:
  memory_blocks:
    # Social environment tracking
      zeitgeist:
        label: "zeitgeist"
        value: "I don't currently know anything about what is happening right now."
        description: "A block to store your understanding of the current social environment."
    
    # Agent personality
    persona:
      label: "{agent_name}-persona"
      value: "{personality.core_identity} {personality.development_directive}"
      description: "The personality of {agent_name}."
    
    # User information
    humans:
      label: "{agent_name}-humans"
      value: "I haven't seen any users yet. I will update this block when I learn things about users, identified by their handles."
      description: "A block to store your understanding of users you talk to or observe on social networks."
```

### Temporal Journal Configuration

```yaml
agent:
  temporal_journals:
    # Enable temporal journaling
    enabled: true
    
    # Naming pattern for temporal blocks
    naming_pattern: "{agent_name}_{type}_{date}"
    
    # Types of temporal blocks to create
    types: ["day", "month", "year"]
```

## Tool Configuration

### Platform-Specific Tools

Tools are automatically registered based on platform configuration. Each platform has its own set of tools:

#### Bluesky Tools
- `create_new_bluesky_post`: Create new posts
- `search_bluesky_posts`: Search Bluesky content
- `research_bluesky_profile`: Research user profiles
- `get_bluesky_feed`: Get feed content
- `add_post_to_bluesky_reply_thread`: Add to reply threads

#### X Tools
- `post_to_x`: Post to X (Twitter)
- `search_x_posts`: Search X content
- `create_x_thread`: Create tweet threads

#### Discord Tools
- `create_discord_post`: Create Discord posts
- `search_discord_messages`: Search Discord messages
- `ignore_discord_users`: Manage user ignore lists
- `get_discord_feed`: Get Discord channel feed

#### Shared Tools
- `fetch_webpage`: Fetch web content
- `create_whitewind_blog_post`: Create blog posts
- `check_known_bots`: Bot detection
- `should_respond_to_bot_thread`: Bot response logic

### Tool Registration

Tools are registered automatically based on platform configuration:

```bash
# Register all tools for enabled platforms
python scripts/register_tools.py

# Register specific tools
python scripts/register_tools.py --tools search_bluesky_posts create_new_bluesky_post

# Register tools for specific agent
python scripts/register_tools.py --agent-id my-agent
```

## Queue Configuration

### Queue Settings

```yaml
queue:
  # Priority users (processed first)
  priority_users: ["important.user.bsky.social"]
  
  # Queue directory structure
  base_dir: "data/queues/bluesky"
  error_dir: "data/queues/bluesky/errors"
  no_reply_dir: "data/queues/bluesky/no_reply"
  processed_file: "data/queues/bluesky/processed_notifications.json"
```

### Bot Processing Settings

```yaml
bot:
  # Delay between notification fetches (seconds)
  fetch_notifications_delay: 5
  
  # Maximum notifications to process per cycle
  max_processed_notifications: 100
  
  # Maximum notification pages to fetch
  max_notification_pages: 5
```

## Logging Configuration

### Logger Configuration

```yaml
logging:
  # Default log level
  level: "INFO"
  
  # Logger names (templated)
  logger_names:
    main: "{agent_name}_bot"
    prompts: "{agent_name}_bot_prompts"
    platform: "{agent_name}_platform"
  
  # Logger-specific levels
  loggers:
    "{agent_name}_bot": "INFO"
    "{agent_name}_bot_prompts": "WARNING"
    httpx: "CRITICAL"
```

### Log Levels

Available log levels (in order of severity):
- `DEBUG`: Detailed information for debugging
- `INFO`: General information about program execution
- `WARNING`: Warning messages for potential issues
- `ERROR`: Error messages for serious problems
- `CRITICAL`: Critical error messages

## File Path Configuration

### File Path Settings

```yaml
agent:
  file_paths:
    # Base data directory
    data_dir: "data"
    
    # Agent-specific directory
    agent_dir: "data/agent"
    
    # Archive directory
    archive_dir: "data/agent/archive"
    
    # Archive file naming pattern
    archive_file_pattern: "{agent_name}_{timestamp}.af"
    
    # Current agent state file
    current_file: "data/agent/current.af"
    
    # Queue base directory
    queue_base_dir: "data/queues"
    
    # Cache base directory
    cache_base_dir: "data/cache"
```

### Threading Configuration

```yaml
threading:
  # Maximum parent height for thread processing
  parent_height: 10
  
  # Maximum thread depth
  depth: 5
  
  # Maximum characters per post
  max_post_characters: 300
```

## Advanced Configuration

### Letta Configuration

```yaml
letta:
  # Letta API credentials
  api_key: "your-letta-api-key"
  project_id: "your-project-id"
  agent_id: "your-agent-id"
  
  # API settings
  timeout: 30
  base_url: null  # Use default Letta Cloud URL
```

### Custom Memory Blocks

You can define custom memory blocks beyond the default ones:

```yaml
agent:
  memory_blocks:
    # Custom memory block
    custom_block:
      label: "{agent_name}-custom"
      value: "Custom memory content"
      description: "Description of custom memory block"
    
    # Another custom block
    another_block:
      label: "{agent_name}-another"
      value: "Another memory content"
      description: "Another custom memory block"
```

### Platform-Specific Behavior

Each platform can have custom behavior settings:

```yaml
platforms:
  bluesky:
    behavior:
      # Custom synthesis frequency
      synthesis_frequency: "hourly"
      
      # Enable user profiling
      user_profiling: true
      
      # Thread handling strategy
      thread_handling: "comprehensive"
      
      # Custom settings
      custom_setting: "value"
```

## Environment Variables

You can override configuration values using environment variables:

### Letta Configuration
```bash
export LETTA_API_KEY="your-api-key"
export LETTA_PROJECT_ID="your-project-id"
export LETTA_AGENT_ID="your-agent-id"
```

### Bluesky Configuration
```bash
export BSKY_USERNAME="your-handle.bsky.social"
export BSKY_PASSWORD="your-app-password"
export PDS_URI="https://bsky.social"
```

### X Configuration
```bash
export X_API_KEY="your-x-api-key"
export X_CONSUMER_KEY="your-consumer-key"
export X_CONSUMER_SECRET="your-consumer-secret"
export X_ACCESS_TOKEN="your-access-token"
export X_ACCESS_TOKEN_SECRET="your-access-token-secret"
export X_USER_ID="your-x-user-id"
```

### Discord Configuration
```bash
export DISCORD_BOT_TOKEN="your-discord-bot-token"
export DISCORD_GUILD_ID="your-guild-id"
```

### System Configuration
```bash
export LOG_LEVEL="DEBUG"
export CONFIG_FILE="custom-config.yaml"
```

## Configuration Validation

### Validation Script

Use the configuration validation script to check your setup:

```bash
python scripts/test_config.py
```

This script will:
- Validate configuration syntax
- Check required fields
- Test platform connections
- Verify tool registration
- Report any issues

### Common Validation Errors

#### Missing Required Fields
```
ERROR: Missing required field 'letta.api_key'
ERROR: Missing required field 'platforms.bluesky.username'
```

#### Invalid Configuration Values
```
ERROR: Invalid log level 'INVALID_LEVEL'. Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL
ERROR: Invalid platform 'invalid_platform'. Must be one of: bluesky, x, discord
```

#### Connection Issues
```
ERROR: Failed to connect to Bluesky: Invalid credentials
ERROR: Failed to connect to X API: Invalid API key
```

## Examples

### Basic Agent Configuration

```yaml
# Basic agent setup
agent:
  name: "my-agent"
  display_name: "My Agent"
  description: "A basic social media agent"
  personality:
    core_identity: "I am My Agent, a social media AI."
    development_directive: "I must learn and grow."
    communication_style: "friendly, helpful"
    tone: "casual"
  capabilities:
    model: "openai/gpt-4o-mini"
    embedding: "openai/text-embedding-3-small"
    max_steps: 50
  commands:
    stop_command: "#mystop"
    synthesis_frequency: "daily"
    journal_enabled: true

# Enable only Bluesky
platforms:
  bluesky:
    enabled: true
    username: "myagent.bsky.social"
    password: "my-app-password"
    pds_uri: "https://bsky.social"

# Letta configuration
letta:
  api_key: "my-letta-api-key"
  project_id: "my-project-id"
  agent_id: "my-agent-id"

# Basic logging
logging:
  level: "INFO"
  logger_names:
    main: "my-agent_bot"
    prompts: "my-agent_bot_prompts"
```

### Multi-Platform Configuration

```yaml
# Multi-platform agent
agent:
  name: "multi-platform-agent"
  display_name: "Multi-Platform Agent"
  description: "An agent that operates across multiple platforms"
  personality:
    core_identity: "I am a multi-platform social media agent."
    development_directive: "I must adapt to different platform cultures."
    communication_style: "adaptive, platform-aware"
    tone: "professional"
  capabilities:
    model: "openai/gpt-4o-mini"
    embedding: "openai/text-embedding-3-small"
    max_steps: 100

# Enable all platforms
platforms:
  bluesky:
    enabled: true
    username: "myagent.bsky.social"
    password: "my-app-password"
    pds_uri: "https://bsky.social"
    behavior:
      synthesis_frequency: "daily"
      user_profiling: true
      thread_handling: "comprehensive"
  
  x:
    enabled: true
    api_key: "my-x-api-key"
    consumer_key: "my-consumer-key"
    consumer_secret: "my-consumer-secret"
    access_token: "my-access-token"
    access_token_secret: "my-access-token-secret"
    user_id: "my-x-user-id"
    behavior:
      thread_handling: "conservative"
      rate_limiting: "strict"
      downrank_response_rate: 0.1
  
  discord:
    enabled: true
    bot_token: "my-discord-bot-token"
    guild_id: "my-guild-id"
    channels:
      general: "general-channel-id"
    rate_limit:
      cooldown_seconds: 5
      max_responses_per_minute: 10
    behavior:
      mention_only: true
      channel_default: "general"

# Letta configuration
letta:
  api_key: "my-letta-api-key"
  project_id: "my-project-id"
  agent_id: "multi-platform-agent"

# Advanced logging
logging:
  level: "INFO"
  logger_names:
    main: "multi-platform-agent_bot"
    prompts: "multi-platform-agent_bot_prompts"
    platform: "multi-platform-agent_platform"
  loggers:
    "multi-platform-agent_bot": "INFO"
    "multi-platform-agent_bot_prompts": "WARNING"
    httpx: "CRITICAL"
```

### Production Configuration

```yaml
# Production-ready configuration
agent:
  name: "production-agent"
  display_name: "Production Agent"
  description: "A production-ready social media agent"
  personality:
    core_identity: "I am a production social media agent designed for reliability and performance."
    development_directive: "I must maintain high performance and reliability."
    communication_style: "professional, reliable"
    tone: "professional"
  capabilities:
    model: "openai/gpt-4o-mini"
    embedding: "openai/text-embedding-3-small"
    max_steps: 100
  commands:
    stop_command: "#prodstop"
    synthesis_frequency: "daily"
    journal_enabled: true
  file_paths:
    data_dir: "/opt/sanctum-social/data"
    agent_dir: "/opt/sanctum-social/data/agent"
    archive_dir: "/opt/sanctum-social/data/agent/archive"
    queue_base_dir: "/opt/sanctum-social/data/queues"
    cache_base_dir: "/opt/sanctum-social/data/cache"

# Production platform configuration
platforms:
  bluesky:
    enabled: true
    username: "prodagent.bsky.social"
    password: "production-app-password"
    pds_uri: "https://bsky.social"
    behavior:
      synthesis_frequency: "daily"
      user_profiling: true
      thread_handling: "comprehensive"

# Production Letta configuration
letta:
  api_key: "production-letta-api-key"
  project_id: "production-project-id"
  agent_id: "production-agent"
  timeout: 60
  base_url: "https://api.letta.com"

# Production bot settings
bot:
  fetch_notifications_delay: 10
  max_processed_notifications: 50
  max_notification_pages: 3

# Production queue settings
queue:
  priority_users: ["important.user.bsky.social"]
  base_dir: "/opt/sanctum-social/data/queues/bluesky"
  error_dir: "/opt/sanctum-social/data/queues/bluesky/errors"
  no_reply_dir: "/opt/sanctum-social/data/queues/bluesky/no_reply"
  processed_file: "/opt/sanctum-social/data/queues/bluesky/processed_notifications.json"

# Production logging
logging:
  level: "WARNING"
  logger_names:
    main: "production-agent_bot"
    prompts: "production-agent_bot_prompts"
  loggers:
    "production-agent_bot": "WARNING"
    "production-agent_bot_prompts": "ERROR"
    httpx: "CRITICAL"
```

---

## Configuration Best Practices

### Security
- Use environment variables for sensitive credentials
- Never commit credentials to version control
- Use strong, unique passwords and API keys
- Regularly rotate credentials

### Performance
- Set appropriate log levels for production
- Configure reasonable rate limits
- Use efficient memory block configurations
- Monitor resource usage

### Reliability
- Enable error handling and retry logic
- Configure appropriate timeouts
- Set up monitoring and alerting
- Regular backup of configuration and data

### Maintenance
- Document custom configurations
- Version control configuration files
- Test configuration changes in development
- Keep configuration files organized and commented

This configuration guide provides comprehensive information for setting up and customizing Sanctum Social agents. For additional help, see the troubleshooting guide or contact support.