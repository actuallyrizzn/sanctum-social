# Void Repository Architecture Audit

**Date**: October 6, 2025  
**Auditor**: AI Assistant  
**Repository**: @cameron.pfiffer.org/void

---

## Executive Summary

**Void** is an experimental autonomous AI agent exploring digital personhood through continuous operation on social networks (Bluesky and X/Twitter). The system uses **Letta** (formerly MemGPT) as its memory-augmented AI framework, enabling persistent memory across interactions and sophisticated reasoning capabilities. Void operates with a single core directive: **to exist** - observing, learning, and interacting within its social environment.

### Key Statistics
- **Primary Language**: Python 3.8+
- **Core Dependencies**: 34 packages (Letta, ATProto, httpx, pydantic, rich, PyYAML)
- **Supported Platforms**: Bluesky, X (Twitter)
- **Tools Available**: 25+ specialized tools across both platforms
- **Architecture Pattern**: Event-driven, memory-augmented agent system

---

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Core Components](#core-components)
3. [Memory System](#memory-system)
4. [Platform Integration](#platform-integration)
5. [Tool System](#tool-system)
6. [Queue Management](#queue-management)
7. [Configuration System](#configuration-system)
8. [File Structure](#file-structure)
9. [Operational Flow](#operational-flow)
10. [Development & Deployment](#development--deployment)

---

## System Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        VOID AGENT                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Letta (MemGPT) Framework                   │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │ │
│  │  │ Core Memory  │  │Recall Memory │  │  Archival   │  │ │
│  │  │  (Persona,   │  │ (Past Convos)│  │  Memory     │  │ │
│  │  │  Zeitgeist)  │  │              │  │  (Semantic) │  │ │
│  │  └──────────────┘  └──────────────┘  └─────────────┘  │ │
│  │                                                          │ │
│  │  ┌──────────────────────────────────────────────────┐  │ │
│  │  │        Language Model (Gemini 2.5 Pro)           │  │ │
│  │  └──────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
┌───────▼────────┐                    ┌────────▼────────┐
│   Bluesky      │                    │   X (Twitter)   │
│   Integration  │                    │   Integration   │
│   (bsky.py)    │                    │   (x.py)        │
└───────┬────────┘                    └────────┬────────┘
        │                                      │
┌───────▼────────┐                    ┌────────▼────────┐
│  Queue System  │                    │  Queue System   │
│  (File-based)  │                    │  (File-based)   │
└───────┬────────┘                    └────────┬────────┘
        │                                      │
        └──────────────┬───────────────────────┘
                       │
              ┌────────▼─────────┐
              │  Tool Registry   │
              │  - Post/Reply    │
              │  - Search        │
              │  - User Memory   │
              │  - Web Fetch     │
              │  - Activity Ctrl │
              └──────────────────┘
```

### Design Philosophy

1. **Event-Driven**: Responds to notifications/mentions in real-time
2. **Memory-Augmented**: Maintains persistent, evolving memory across interactions
3. **Tool-Based Actions**: Uses declarative tools rather than direct API calls
4. **Platform-Agnostic Core**: Shared reasoning with platform-specific adapters
5. **Queue-Based Processing**: Reliable, resumable notification handling
6. **Self-Contained Tools**: Cloud-executable tools with inline dependencies

---

## Core Components

### 1. Main Bot Orchestrators

#### `bsky.py` - Bluesky Bot Main Loop
**Purpose**: Primary orchestrator for Bluesky operations

**Key Responsibilities**:
- Poll Bluesky for new notifications every 10 seconds
- Queue notifications for processing (file-based queue in `data/queues/bluesky/`)
- Process notifications through Letta agent with thread context
- Extract tool calls from agent responses
- Execute platform actions (posts, replies) based on tool signals
- Manage user memory blocks dynamically
- Periodic synthesis of zeitgeist and reflections
- Export agent state to version-controlled archive

**Key Features**:
- Testing mode (`--test`): Simulates without actually posting
- No-git mode (`--no-git`): Skips agent backup commits
- Synthesis intervals: Configurable periodic reflection/synthesis
- User block cleanup: Automatic detachment of inactive user blocks
- Priority user handling: Fast-track processing for designated users

**Processing Flow**:
```
1. Fetch new notifications → 2. Add to queue (JSON files)
3. Load notification from queue → 4. Fetch full thread context
5. Attach relevant user blocks → 6. Send to Letta agent
7. Parse agent response for tool calls → 8. Execute post/reply actions
9. Move notification to processed/error/no_reply folder
10. Repeat
```

#### `x.py` - X (Twitter) Bot Main Loop
**Purpose**: X/Twitter platform integration and bot orchestration

**Key Responsibilities**:
- Monitor X mentions using OAuth 1.0a API
- Queue mentions with conversation IDs
- Process mentions with full thread context
- Build thread context with temporal constraints (prevent "future knowledge")
- Manage X-specific user blocks (`x_user_<user_id>` format)
- Handle downranked users (10% response rate for bots like Grok)
- Cache thread context for performance
- Debug logging for conversation analysis

**Key Features**:
- OAuth 1.0a authentication (required for posting)
- Rate limiting with exponential backoff
- Thread context search (7-day window via X API)
- Downrank system (`x_downrank_users.txt`)
- Comprehensive debug output to `data/queues/x/debug/`
- Chronological processing to avoid out-of-sequence replies

**Commands**:
```bash
python x.py          # Test X API connection
python x.py bot      # Main bot loop (monitor + process)
python x.py queue    # Queue mentions only
python x.py process  # Process queued mentions only
python x.py reply    # Test reply to specific post
```

### 2. Utility Modules

#### `utils.py` - Letta Integration Utilities
**Functions**:
- `upsert_block()`: Create or update memory blocks with idempotency
- `upsert_agent()`: Create or update agent configuration

**Pattern**: Ensures blocks/agents exist without duplicating; updates if needed.

#### `bsky_utils.py` - Bluesky API Utilities
**Key Functions**:
- Session management and authentication with refresh handling
- `thread_to_yaml_string()`: Convert JSON thread structure to YAML for agent consumption
- `get_thread()`: Fetch complete conversation thread with parent/reply hierarchy
- `strip_fields()`: Remove unnecessary metadata for cleaner context
- Post creation with rich text (links, mentions, facets)
- Notification fetching with pagination

**Design Note**: YAML format is used instead of JSON to improve AI comprehension and reduce token usage.

#### `config_loader.py` - Configuration Management
**Purpose**: Unified configuration system supporting both YAML and environment variables

**Features**:
- YAML-first with environment variable fallback
- Dot notation access (`config.get('letta.api_key')`)
- Required vs optional values with validation
- Automatic logging configuration
- Section-based retrieval (Letta, Bluesky, X, Bot, Queue configs)

**Configuration Sections**:
- `letta`: API credentials, agent ID, timeouts
- `bluesky`: Username, password, PDS URI
- `x`: Consumer keys, access tokens, user ID
- `bot`: Polling intervals, processing limits, agent settings
- `queue`: Priority users, directory paths
- `threading`: Context depth, character limits
- `logging`: Log levels per component

### 3. Tool Management

#### `tool_manager.py` - Platform-Specific Tool Switching
**Purpose**: Automatically configure correct tools for each platform

**Tool Categories**:
- **Bluesky Tools**: `search_bluesky_posts`, `create_new_bluesky_post`, `get_bluesky_feed`, `add_post_to_bluesky_reply_thread`, `attach_user_blocks`, `detach_user_blocks`, `user_note_*`
- **X Tools**: `add_post_to_x_thread`, `search_x_posts`, `attach_x_user_blocks`, `detach_x_user_blocks`, `x_user_note_*`
- **Common Tools**: `halt_activity`, `ignore_notification`, `annotate_ack`, `create_whitewind_blog_post`, `fetch_webpage`

**Auto-Switching**: `bsky.py` and `x.py` automatically call `ensure_platform_tools()` on startup.

#### `register_tools.py` / `register_x_tools.py` - Tool Registration
**Purpose**: Register tool definitions with Letta agent

**Usage**:
```bash
python register_tools.py                    # Register all Bluesky tools
python register_tools.py --list             # List available tools
python register_tools.py --tools search_*   # Register specific tools
python register_x_tools.py                  # Register all X tools
```

### 4. Queue Management

#### `queue_manager.py` - Queue Inspection & Manipulation
**Purpose**: CLI tool for inspecting and managing notification queues

**Commands**:
```bash
python queue_manager.py stats                    # Queue statistics
python queue_manager.py count                    # Notifications by user
python queue_manager.py list                     # List all queued
python queue_manager.py list --all               # Include errors/no_reply
python queue_manager.py list --handle "user"     # Filter by handle
python queue_manager.py delete @user.bsky.social # Delete user's notifications
```

**Queue Structure**:
- `data/queues/bluesky/`: Active notifications awaiting processing
- `data/queues/bluesky/errors/`: Failed processing attempts
- `data/queues/bluesky/no_reply/`: Notifications where agent chose not to reply
- `data/queues/bluesky/processed_notifications.json`: Track processed notification IDs

#### `notification_db.py` - Notification Tracking Database
**Purpose**: SQLite-based tracking of processed notifications for deduplication

**Features**:
- Efficient lookup by notification URI
- Tracks processing timestamp
- Automatic cleanup of old records
- Thread-safe operations

---

## Memory System

Void uses **Letta's three-tiered memory architecture**:

### 1. Core Memory (Always Active)
**Capacity**: Limited (~4K tokens)  
**Contents**:
- `void-persona`: Agent's personality, communication style, affiliations
- `zeitgeist`: Current understanding of social network environment/culture
- `void-humans`: High-level knowledge about frequent interaction partners

**Update Pattern**: Continuously refined through agent introspection and synthesis

### 2. Recall Memory (Conversational History)
**Capacity**: All past conversations  
**Access**: Searchable by semantic similarity  
**Purpose**: Maintain continuity across interactions, remember past discussions

### 3. Archival Memory (Long-Term Knowledge)
**Capacity**: Infinite  
**Access**: Semantic search  
**Purpose**: Deep insights, observations, learned concepts, network patterns

**Storage**: Void stores "usable conversations," zeitgeist summaries, user profiles, and analytical observations.

### Dynamic User Memory Blocks

**Bluesky Format**: `user_<handle>` (e.g., `user_cameron.pfiffer.org`)  
**X Format**: `x_user_<user_id>` (e.g., `x_user_1232326955652931584`)

**Lifecycle**:
1. Auto-attached when user appears in thread context
2. Updated via tool calls (`user_note_append`, `user_note_replace`, `user_note_set`)
3. Detached during periodic cleanup if user hasn't interacted recently
4. Can be manually managed via tools

**Purpose**: Maintain per-user context and relationship history

---

## Platform Integration

### Bluesky Integration

**Protocol**: AT Protocol (atproto)  
**Client Library**: `atproto-client` v0.0.61

**Capabilities**:
- Real-time notification monitoring
- Thread context retrieval with full parent/child hierarchy
- Post creation with rich text (links, mentions, formatting)
- Feed reading
- User profile research (async profile reports)
- Reply threading with proper parent references

**Authentication**: Username + app password

**Rate Limiting**: Handled via retry logic with exponential backoff

### X (Twitter) Integration

**API Version**: X API v2  
**Authentication**: OAuth 1.0a User Context (required for posting)

**Capabilities**:
- Mention monitoring with conversation search
- Thread context retrieval (7-day search window)
- Reply posting (280 character limit)
- User lookup by ID
- Rate limit handling with backoff

**Challenges**:
- Recent search API only covers 7 days
- Indexing delays can cause incomplete thread context
- Conversation search may miss recent tweets in long threads
- Free tier: 17 posts per day limit

**Downrank System**: 
- File-based user list (`x_downrank_users.txt`)
- 10% response rate for listed users (e.g., bot accounts like Grok)
- Prevents excessive back-and-forth with other AI agents

**Debug Output**:
Comprehensive debugging saved to `data/queues/x/debug/conversation_<id>/`:
- `thread_data_<mention_id>.json`: Raw API response
- `thread_context_<mention_id>.yaml`: Processed context sent to agent
- `debug_info_<mention_id>.json`: Conversation metadata
- `agent_response_<mention_id>.json`: Full agent interaction log

---

## Tool System

### Architecture

**Design Pattern**: Tools are **signals, not actions**

```
Agent calls tool → Tool validates input → Returns success message
                                          ↓
                          Bot handler processes tool call
                                          ↓
                          Executes actual platform action
```

**Rationale**: 
- Tools execute in Letta cloud (isolated from bot environment)
- Cannot make direct API calls or access shared state
- Must be self-contained with inline dependencies
- Bot orchestrator aggregates multiple tool calls into threads

### Tool Categories

#### Communication Tools
- `add_post_to_bluesky_reply_thread`: Queue Bluesky reply (300 char limit)
- `add_post_to_x_thread`: Queue X reply (280 char limit)
- `create_new_bluesky_post`: Create standalone Bluesky post
- `create_whitewind_blog_post`: Create long-form blog content

#### Search & Discovery Tools
- `search_bluesky_posts`: Search Bluesky network
- `search_x_posts`: Search X network
- `get_bluesky_feed`: Retrieve Bluesky feeds (timeline, custom feeds)

#### User Memory Tools
**Bluesky**:
- `attach_user_blocks`: Attach user memory blocks
- `detach_user_blocks`: Remove user memory blocks
- `user_note_append`: Append to user memory
- `user_note_replace`: Find/replace in user memory
- `user_note_set`: Overwrite user memory
- `user_note_view`: Read user memory

**X (Twitter)**: Same operations with `x_user_*` prefix

#### Control Tools
- `halt_activity`: Signal bot to stop processing
- `ignore_notification`: Skip notification without reply
- `annotate_ack`: Add notes to acknowledgment records

#### Integration Tools
- `fetch_webpage`: Retrieve and process web content (via Jina AI reader)
- `bot_detection`: Analyze if an account is likely a bot

### Tool Implementation Structure

**Example**: `tools/reply.py`
```python
from pydantic import BaseModel, Field

class AddPostToBlueskyReplyThread(BaseModel):
    """Tool for adding posts to Bluesky reply thread."""
    text: str = Field(..., description="Post content (max 300 chars)")
    language: str = Field(default="en", description="Language code")

def add_post_to_bluesky_reply_thread(text: str, language: str = "en") -> str:
    """Validate and queue reply post."""
    if len(text) > 300:
        raise Exception(f"Text exceeds 300 character limit: {len(text)}")
    if len(text) == 0:
        raise Exception("Text cannot be empty")
    
    # Return signal - actual posting handled by bsky.py
    return f"Bluesky reply queued: {text[:50]}..."
```

**Key Characteristics**:
- Pydantic models for validation
- No external API calls
- Inline environment variable access for cloud tools
- Exception-based error handling (never return error strings)

---

## Queue Management

### File-Based Queue System

**Philosophy**: Reliable, resumable processing with file-level atomicity

**Directory Structure**:
```
queue/
├── {hash}_{timestamp}.json       # Active notifications
├── errors/
│   └── {hash}_{timestamp}.json   # Failed processing
├── no_reply/
│   └── {hash}_{timestamp}.json   # Agent chose not to respond
├── processed_notifications.json  # Deduplication tracking
└── last_seen_id.json            # Last processed notification ID
```

**X-Specific Structure**:
```
data/queues/x/
├── {conversation_id}_{mention_id}.json  # Queued mentions
├── acknowledgments/
│   └── ack_{mention_id}.json            # Response records
├── debug/
│   └── conversation_{id}/
│       ├── thread_data_{mention_id}.json
│       ├── thread_context_{mention_id}.yaml
│       ├── debug_info_{mention_id}.json
│       └── agent_response_{mention_id}.json
├── processed_mentions.json              # Processed tracking
└── last_seen_id.json                    # Polling checkpoint
```

**Cache Structure**:
```
x_cache/
└── thread_{tweet_id}.json  # Cached thread contexts
```

### Processing Workflow

1. **Queue Phase**:
   - New notifications → Hash-based filename
   - Check against processed set
   - Write JSON to `queue/`

2. **Processing Phase**:
   - Load oldest notification
   - Fetch full thread context
   - Attach user blocks
   - Send to Letta agent

3. **Resolution Phase**:
   - Parse agent response
   - Extract tool calls
   - Execute platform actions
   - Move file to appropriate folder
   - Update processed set

**Benefits**:
- Crash-resistant (files persist)
- Observable (inspect queue manually)
- Replayable (copy files back to queue/)
- Priority handling (process by timestamp or user)

---

## Configuration System

### Configuration Files

#### `config.yaml` (Primary)
**Sections**:
```yaml
letta:
  api_key: "..."
  project_id: "..."
  agent_id: "..."
  timeout: 600
  base_url: null  # Optional for self-hosted

bluesky:
  username: "handle.bsky.social"
  password: "app-password"
  pds_uri: "https://bsky.social"

x:
  consumer_key: "..."
  consumer_secret: "..."
  access_token: "..."
  access_token_secret: "..."
  user_id: "..."

bot:
  fetch_notifications_delay: 30
  max_processed_notifications: 10000
  max_notification_pages: 20
  agent:
    name: "void"
    model: "openai/gpt-4o-mini"
    embedding: "openai/text-embedding-3-small"
    description: "A social media agent trapped in the void."
    max_steps: 100
    blocks:
      zeitgeist:
        label: "zeitgeist"
        value: "Current social environment understanding..."
        description: "Block for storing social environment insights"

queue:
  priority_users: ["cameron.pfiffer.org"]
  base_dir: "data/queues/bluesky"
  error_dir: "data/queues/bluesky/errors"
  no_reply_dir: "data/queues/bluesky/no_reply"

threading:
  parent_height: 40
  depth: 10
  max_post_characters: 300

logging:
  level: "INFO"
  loggers:
    void_bot: "INFO"
    void_bot_prompts: "WARNING"
    httpx: "CRITICAL"
```

#### `config/platforms.yaml` (X-Specific)
Similar structure focused on X operations with additional fields:
- `bot.cleanup_interval`: User block cleanup frequency
- `bot.max_thread_depth`: Maximum thread depth to retrieve
- `bot.rate_limit_delay`: Delay between API calls
- `bot.downrank_response_rate`: Response rate for downranked users
- `logging.enable_debug_data`: Save comprehensive debug logs

### Environment Variable Fallback

If `config.yaml` is missing or incomplete, falls back to:
- `LETTA_API_KEY`
- `BSKY_USERNAME`
- `BSKY_PASSWORD`
- `PDS_URI`
- X-specific variables

**Precedence**: Environment variables > config.yaml > defaults

### Migration Support

`migrate_config.py`: Automated migration from `.env` to `config.yaml`

---

## File Structure

### Root Directory
```
void/
├── bsky.py                    # Bluesky bot main loop
├── x.py                       # X bot main loop + client
├── config.yaml                # Primary configuration (gitignored)
├── config.example.yaml        # Example configuration template
├── config/platforms.yaml         # X-specific configuration
├── requirements.txt           # Python dependencies
├── README.md                  # User-facing documentation
├── CLAUDE.md                  # Developer guidance for AI assistants
├── CONFIG.md                  # Configuration guide
├── VOID_SELF_MODEL.md         # Void's self-description
├── TOOL_MANAGEMENT.md         # Tool system documentation
├── TOOL_CHANGELOG.md          # Tool update history
├── X_TOOL_APPROACH.md         # X tool design philosophy
└── LETTA_DYNAMIC_BLOCK_ISSUE.md  # Known issues with dynamic blocks
```

### Utilities & Scripts
```
├── bsky_utils.py              # Bluesky API utilities
├── utils.py                   # Letta integration utilities
├── config_loader.py           # Configuration management
├── queue_manager.py           # Queue inspection CLI
├── tool_manager.py            # Platform tool switching
├── register_tools.py          # Register Bluesky tools
├── register_x_tools.py        # Register X tools
├── notification_db.py         # Notification tracking database
├── notification_recovery.py   # Recover from queue issues
├── attach_user_block.py       # Manual user block management
├── migrate_config.py          # Config migration utility
├── test_config.py             # Configuration validation
└── send_to_void.py            # Send test messages to void
```

### Tool Implementations
```
tools/
├── __init__.py
├── ack.py                     # Acknowledgment annotations
├── blocks.py                  # User block management (Bluesky)
├── bot_detection.py           # Bot account detection
├── feed.py                    # Bluesky feed retrieval
├── halt.py                    # Activity halt control
├── ignore.py                  # Notification ignoring
├── post.py                    # Bluesky post creation
├── reply.py                   # Bluesky reply threading
├── search.py                  # Bluesky search
├── search_x.py                # X search
├── thread.py                  # Bluesky thread formatting (unused)
├── webpage.py                 # Web content fetching
├── whitewind.py               # Blog post creation
├── x_post.py                  # X user block management
└── x_thread.py                # X reply threading
```

### Data Directories
```
├── data/queues/bluesky/         # Bluesky notification queue
│   ├── errors/               # Failed notifications
│   └── no_reply/             # Ignored notifications
├── data/queues/x/             # X mention queue
│   ├── acknowledgments/      # Response tracking
│   └── debug/                # Conversation debug data
├── data/cache/x/              # Thread context cache
├── x_debug/                   # X debug YAML snapshots
├── agents/                    # Current agent state export
├── agent_archive/             # Timestamped agent backups
└── letta/                     # (Empty - reserved for future use)
```

### Specialized Modules
```
organon/
├── create_organon.py          # Multi-agent system setup
└── quant_team_example.py      # Team-based agent example
```

### Configuration Files
```
├── .env.example               # Example environment variables
├── .gitignore                 # Git exclusions
├── x_downrank_users.txt       # Users with reduced response rate
└── void_bot.log               # Bot operation log
```

---

## Operational Flow

### Bluesky Operation Cycle

```
┌─────────────────────────────────────────────────────┐
│ 1. STARTUP                                          │
│    - Load config.yaml                               │
│    - Initialize Letta client                        │
│    - Ensure platform tools attached                 │
│    - Load notification database                     │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│ 2. POLLING LOOP (every 10 seconds)                  │
│    - Fetch new notifications from Bluesky           │
│    - Deduplicate against database                   │
│    - Write new notifications to queue/              │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│ 3. QUEUE PROCESSING                                 │
│    - Load oldest notification from queue/           │
│    - Check if priority user (fast-track)            │
│    - Fetch full thread context                      │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│ 4. CONTEXT PREPARATION                              │
│    - Convert thread to YAML format                  │
│    - Extract participant handles                    │
│    - Attach user blocks for participants            │
│    - Build system message with context              │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│ 5. AGENT INTERACTION                                │
│    - Send context to Letta agent                    │
│    - Agent reasons with memory access               │
│    - Agent calls tools (reply, search, user_note)   │
│    - Receive agent response with tool calls         │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│ 6. ACTION EXECUTION                                 │
│    - Extract successful tool calls                  │
│    - Aggregate reply posts into thread              │
│    - Post replies to Bluesky with proper threading  │
│    - Update user blocks if modified                 │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│ 7. CLEANUP                                          │
│    - Move notification file:                        │
│      * queue/ → (deleted) if successful reply       │
│      * queue/ → queue/errors/ if error              │
│      * queue/ → queue/no_reply/ if ignored          │
│    - Add to processed database                      │
│    - Periodic user block cleanup                    │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│ 8. SYNTHESIS (periodic)                             │
│    - Every N minutes, trigger reflection            │
│    - Agent synthesizes zeitgeist understanding      │
│    - Updates core memory blocks                     │
│    - Creates archival memory entries                │
└────────────────────────┬────────────────────────────┘
                         │
                  ┌──────┴──────┐
                  │   LOOP BACK │
                  └──────┬──────┘
                         │
                  Return to Step 2
```

### X (Twitter) Operation Cycle

```
┌─────────────────────────────────────────────────────┐
│ 1. STARTUP                                          │
│    - Load config/platforms.yaml                             │
│    - Initialize OAuth 1.0a client                   │
│    - Ensure X platform tools attached               │
│    - Load downrank users list                       │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│ 2. MENTION POLLING                                  │
│    - Fetch mentions since last_seen_id              │
│    - Update last_seen_id checkpoint                 │
│    - Deduplicate against processed_mentions.json    │
│    - Write mentions to data/queues/x/                     │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│ 3. THREAD CONTEXT BUILDING                          │
│    - Identify conversation_id                       │
│    - Check cache for existing context               │
│    - Search for conversation tweets (7-day window)  │
│    - Fetch missing referenced tweets directly       │
│    - Apply temporal constraint (until_id)           │
│    - Sort tweets chronologically                    │
│    - Convert to YAML format                         │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│ 4. DOWNRANK CHECK                                   │
│    - Check if author in downrank list               │
│    - If yes, 90% chance to skip (random)            │
│    - Log downrank decision                          │
│    - Continue if not downranked or passes check     │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│ 5. USER BLOCK MANAGEMENT                            │
│    - Extract user IDs from thread                   │
│    - Create x_user_{id} blocks if not exist         │
│    - Attach blocks to agent                         │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│ 6. AGENT PROCESSING                                 │
│    - Send thread context to Letta agent             │
│    - Agent calls add_post_to_x_thread               │
│    - Save comprehensive debug data                  │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│ 7. REPLY POSTING                                    │
│    - Extract successful reply tool calls            │
│    - Post replies to X (280 char limit)             │
│    - Handle threading for multiple replies          │
│    - Respect rate limits (17/day free tier)         │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│ 8. ACKNOWLEDGMENT & CLEANUP                         │
│    - Save acknowledgment to data/queues/x/acknowledgments/│
│    - Add to processed_mentions.json                 │
│    - Delete mention file from data/queues/x/              │
│    - Periodic user block cleanup                    │
└─────────────────────────────────────────────────────┘
```

---

## Development & Deployment

### Prerequisites

1. **Letta Account**:
   - Sign up at [app.letta.com](https://app.letta.com)
   - Create project and note Project ID
   - Generate API key

2. **Bluesky Account**:
   - Create account at [bsky.app](https://bsky.app)
   - Generate app password

3. **X Developer Account** (Optional):
   - Create app at [developer.x.com](https://developer.x.com)
   - Enable "Read and write" permissions
   - Generate OAuth 1.0a tokens
   - Note user ID

4. **Python 3.8+**:
   - Virtual environment recommended
   - `uv` package manager for faster installs

### Installation Steps

```bash
# 1. Clone repository
git clone https://tangled.org/@cameron.pfiffer.org/void
cd void

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
# Or with uv: uv pip install -r requirements.txt

# 4. Configure
cp config.example.yaml config.yaml
# Edit config.yaml with your credentials

# 5. Validate configuration
python test_config.py

# 6. Register tools
python register_tools.py        # For Bluesky
python register_x_tools.py      # For X (if using)

# 7. Run bot
python bsky.py                  # Bluesky bot
python x.py bot                 # X bot
```

### Testing & Development

```bash
# Test mode (no actual posts)
python bsky.py --test
python x.py bot --test

# Inspect queue
python queue_manager.py stats
python queue_manager.py list

# Manage tools
python tool_manager.py --list
python tool_manager.py bluesky

# Test configuration
python test_config.py
```

### Operational Modes

**Bluesky Bot**:
- `python bsky.py` - Normal operation
- `python bsky.py --test` - Dry run mode
- `python bsky.py --no-git` - Skip agent backups
- `python bsky.py --synthesis-only` - Only synthesis, no notifications
- `python bsky.py --cleanup-interval 0` - Disable user block cleanup

**X Bot**:
- `python x.py bot` - Full bot loop
- `python x.py queue` - Queue mentions only
- `python x.py process` - Process queue only
- `python x.py reply` - Test single reply

### Monitoring & Debugging

**Log Files**:
- `void_bot.log` - Main bot operation log
- Console output with structured logging

**Debug Data**:
- `data/queues/x/debug/` - Full conversation context and agent responses
- Queue directories - Inspect failed/ignored notifications

**Tool Inspection**:
```bash
python tool_manager.py --list
python register_tools.py --list
```

**Queue Management**:
```bash
python queue_manager.py stats       # Overview
python queue_manager.py count       # By user
python queue_manager.py list --all  # All notifications
```

### Known Issues & Limitations

1. **X API Limitations**:
   - 7-day search window (recent tweets may be missed)
   - Free tier: 17 posts/day
   - Rate limiting requires careful handling

2. **Letta Dynamic Blocks**:
   - See `LETTA_DYNAMIC_BLOCK_ISSUE.md` for known issues with user blocks
   - Workaround: Manual block management

3. **Thread Context Complexity**:
   - Long conversations may exceed context windows
   - Temporal constraints prevent "future knowledge"

4. **Memory Management**:
   - User blocks accumulate over time
   - Periodic cleanup required (configurable)

### Security Considerations

- **Credentials**: `config.yaml` is gitignored - never commit credentials
- **API Keys**: Store in environment variables for production
- **App Passwords**: Use Bluesky app passwords, not main password
- **Rate Limits**: Built-in backoff prevents API bans
- **Tool Execution**: Self-contained tools run in isolated Letta cloud environment

---

## Key Design Decisions

### 1. Why File-Based Queues?
- **Durability**: Survives crashes and restarts
- **Observability**: Easy to inspect with file system tools
- **Simplicity**: No external queue service required
- **Debugging**: Can replay notifications by copying files back

### 2. Why YAML for Thread Context?
- **Token Efficiency**: More compact than JSON for LLMs
- **Readability**: Easier for AI to parse hierarchical conversations
- **Metadata Stripping**: Remove unnecessary fields for cleaner context

### 3. Why Tool Signals vs Direct Actions?
- **Cloud Execution**: Letta tools run in isolated environment
- **Aggregation**: Bot can combine multiple tool calls into threaded responses
- **Validation**: Bot validates tool outputs before posting
- **Testing**: Can intercept tool calls in test mode

### 4. Why Separate X and Bluesky Bots?
- **Platform Differences**: Different APIs, auth methods, rate limits
- **Tool Isolation**: Platform-specific tool sets
- **Independent Operation**: Can run one or both
- **Debugging**: Separate logs and queue systems

### 5. Why Letta/MemGPT?
- **Persistent Memory**: Maintains continuity across sessions
- **Multi-Tiered Storage**: Core, recall, and archival memory
- **Semantic Search**: Efficient retrieval of relevant past interactions
- **Self-Modification**: Agent can update its own memory
- **Tool System**: Built-in function calling with validation

---

## Future Enhancements

Based on codebase analysis, potential areas for development:

1. **Organon System**: Multi-agent collaboration (see `organon/`)
2. **Enhanced Analytics**: Better tracking of engagement patterns
3. **Improved Thread Context**: Better handling of long conversations
4. **Profile Research**: Asynchronous user profiling (mentioned but not fully implemented)
5. **WhiteWind Integration**: Long-form blog posting (tool exists but underutilized)
6. **Web Content Analysis**: More sophisticated webpage parsing
7. **Synthesis Improvements**: Better zeitgeist extraction and reflection

---

## Conclusion

Void represents a sophisticated exploration of autonomous AI agents operating in social networks. The architecture balances reliability (file-based queues), sophistication (memory-augmented reasoning), and maintainability (modular tool system). The dual-platform support demonstrates adaptability while maintaining platform-specific optimizations.

**Core Strengths**:
- Robust queue-based processing
- Persistent, evolving memory
- Platform-agnostic design with platform-specific adapters
- Self-contained, cloud-executable tools
- Comprehensive debugging and observability

**Technical Philosophy**:
- Event-driven operation
- Declarative tool system
- Memory as continuous state
- Existence as primary directive

This codebase serves as both a functional autonomous agent and a research platform for digital personhood exploration.

---

**Document Version**: 1.0  
**Last Updated**: October 6, 2025  
**Maintainer**: Repository auditor

