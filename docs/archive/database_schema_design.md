# SQLite Database Schema Design

## Overview
Design a comprehensive SQLite database schema to replace file-based data storage with proper relational database management.

## Current File-Based Storage Analysis

### Existing Files to Migrate
- `config.yaml` - Main configuration
- `x_config.yaml` - X-specific configuration  
- `x_downrank_users.txt` - X user blacklist
- `queue/` directory - Notification queues
- `x_queue/` directory - X notification queues
- `sessions/` directory - Session files
- `x_cache/` directory - X API cache
- `notification_db.sqlite` - Existing notification database

## Database Schema Design

### 1. Configuration Management
```sql
-- Centralized configuration storage
CREATE TABLE configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT NOT NULL,
    section TEXT NOT NULL,
    environment TEXT DEFAULT 'default',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Configuration versioning
CREATE TABLE config_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL,
    description TEXT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. User Management & Blacklisting
```sql
-- User profiles and metadata
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL, -- 'bluesky', 'x', 'discord'
    platform_user_id TEXT NOT NULL,
    username TEXT,
    display_name TEXT,
    profile_data TEXT, -- JSON metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform, platform_user_id)
);

-- Cross-platform user identity mapping
CREATE TABLE user_identities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    platform_user_id TEXT NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Blacklist/whitelist management
CREATE TABLE user_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    list_type TEXT NOT NULL, -- 'blacklist', 'whitelist', 'downrank'
    platform TEXT NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- User ranking and reputation
CREATE TABLE user_rankings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    ranking_score REAL DEFAULT 0.0,
    ranking_factors TEXT, -- JSON factors
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 3. Content Management
```sql
-- Post/notification tracking
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    platform_post_id TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    post_type TEXT NOT NULL, -- 'post', 'reply', 'mention'
    parent_post_id INTEGER,
    thread_id INTEGER,
    metadata TEXT, -- JSON additional data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (parent_post_id) REFERENCES posts(id)
);

-- Content moderation and filtering
CREATE TABLE content_moderation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    moderation_action TEXT NOT NULL, -- 'approved', 'flagged', 'blocked'
    reason TEXT,
    moderator_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES posts(id)
);

-- Thread and conversation management
CREATE TABLE threads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    platform_thread_id TEXT NOT NULL,
    root_post_id INTEGER NOT NULL,
    participant_count INTEGER DEFAULT 0,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (root_post_id) REFERENCES posts(id)
);
```

### 4. Platform Integration
```sql
-- Platform-specific settings
CREATE TABLE platform_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL UNIQUE,
    settings TEXT NOT NULL, -- JSON platform-specific config
    api_credentials TEXT, -- Encrypted credentials
    rate_limit_info TEXT, -- JSON rate limiting data
    last_sync TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API credentials and tokens (encrypted)
CREATE TABLE api_credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    credential_type TEXT NOT NULL, -- 'bot_token', 'api_key', 'access_token'
    encrypted_value TEXT NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rate limiting and quota management
CREATE TABLE rate_limits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    requests_made INTEGER DEFAULT 0,
    requests_limit INTEGER NOT NULL,
    reset_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5. Analytics & Reporting
```sql
-- Usage statistics
CREATE TABLE usage_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance metrics
CREATE TABLE performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation TEXT NOT NULL,
    platform TEXT NOT NULL,
    duration_ms INTEGER NOT NULL,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Error tracking and logging
CREATE TABLE error_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    error_type TEXT NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    context_data TEXT, -- JSON context
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit trails
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    old_values TEXT, -- JSON old state
    new_values TEXT, -- JSON new state
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 6. Queue Management
```sql
-- Notification queues
CREATE TABLE notification_queues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    notification_data TEXT NOT NULL, -- JSON notification
    priority INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- Processing status tracking
CREATE TABLE processing_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    queue_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (queue_id) REFERENCES notification_queues(id)
);

-- Priority management
CREATE TABLE queue_priorities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    priority_level INTEGER NOT NULL,
    description TEXT,
    max_processing_time INTEGER, -- seconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Migration Strategy

### Phase 1: Schema Creation
1. Create database schema
2. Implement database abstraction layer
3. Create migration scripts
4. Add database configuration

### Phase 2: Data Migration
1. Migrate configuration data
2. Migrate user data and blacklists
3. Migrate queue data
4. Migrate session data
5. Migrate cache data

### Phase 3: Code Migration
1. Update configuration loading
2. Update user management
3. Update queue management
4. Update session management
5. Update all modules to use database

### Phase 4: Testing & Validation
1. Comprehensive testing
2. Performance validation
3. Data integrity checks
4. Backup and recovery testing

## Benefits of Database Schema

- **Data Integrity**: Proper relationships and constraints
- **Performance**: Indexed queries and efficient data access
- **Scalability**: Handle larger datasets and concurrent access
- **Consistency**: Centralized data management
- **Backup & Recovery**: Proper database backup strategies
- **Migration**: Structured approach to data migration
- **Analytics**: Rich querying capabilities for reporting
- **Security**: Encrypted credential storage
- **Auditing**: Complete audit trail of all changes
