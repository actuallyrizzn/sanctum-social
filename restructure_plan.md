## Repository Restructuring Plan - Groundwork Implementation

### Approach
- **One installation per one agent** (not multi-agent)
- **Platforms as plugins** (configurable on/off, no autodiscovery yet)
- **Clean organization** for maintainability and configurability

### Proposed Structure
```
void/
├── core/                         # Core framework
│   ├── agent.py                  # Agent initialization & management
│   ├── config.py                 # Configuration system
│   ├── memory.py                 # Memory block management
│   └── prompts.py                # Prompt generation system
├── platforms/                    # Platform plugins
│   ├── base.py                   # Base platform interface
│   ├── bluesky/                  # Bluesky plugin
│   │   ├── orchestrator.py       # bsky.py → orchestrator.py
│   │   ├── utils.py              # bsky_utils.py
│   │   └── tools/                # Bluesky tools
│   ├── x/                        # X plugin
│   │   ├── orchestrator.py       # x.py → orchestrator.py
│   │   ├── client.py             # XClient class
│   │   └── tools/                # X tools
│   └── discord/                  # Discord plugin
│       ├── orchestrator.py       # discord_orchestrator.py
│       ├── utils.py              # discord_utils.py
│       └── tools/                # Discord tools
├── tools/                        # Shared tools
├── utils/                        # Shared utilities
├── config/                       # Configuration
│   ├── agent.yaml                # Agent personality & behavior
│   └── platforms.yaml           # Platform enable/disable config
├── data/                         # Runtime data
│   ├── agent/                    # Agent state
│   ├── queues/                   # Queue data by platform
│   ├── sessions/                 # Session data
│   └── cache/                    # Cache data
├── scripts/                      # Utility scripts
├── tests/                        # Keep existing test structure
├── docs/                         # Keep existing docs
└── agents/                       # Supporting agents
```

### Key Benefits
- **Platform Plugins**: Each platform self-contained
- **Core Extraction**: Core logic separated from platform code
- **Config Separation**: Agent config vs platform config
- **Data Organization**: All runtime data in data/ directory
- **Clean Root**: Only essential files in root directory

### Implementation Plan
1. Create new directory structure
2. Move files to appropriate locations
3. Update imports (relative imports)
4. Extract core components from orchestrators
5. Create platform base class
6. Update configuration system

This provides clean foundation for making agent configurable while keeping platforms as simple plugins.
