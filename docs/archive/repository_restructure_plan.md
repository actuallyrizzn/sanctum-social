# Repository Restructuring Plan - Pre-Generalization Cleanup

## Current State Analysis

The repository is indeed quite disorganized with several structural issues:

### 🚨 **Current Problems:**

1. **Root Directory Clutter**: 30+ files in root directory
2. **Mixed Concerns**: Core logic, utilities, configs, docs, tests all mixed together
3. **Platform-Specific Files Scattered**: X, Discord, Bluesky files not organized
4. **Temporary/Debug Files**: Various debug and temporary files in root
5. **Inconsistent Naming**: Some files use underscores, others use hyphens
6. **Missing Separation**: No clear separation between core framework and agent-specific code

## 🎯 **Proposed Restructure**

### **New Directory Structure:**

```
void/
├── src/                          # Core framework code
│   ├── core/                     # Core framework components
│   │   ├── __init__.py
│   │   ├── agent_manager.py      # Agent initialization & management
│   │   ├── config_manager.py     # Configuration system
│   │   ├── memory_manager.py     # Memory block management
│   │   └── prompt_generator.py   # Prompt generation system
│   │
│   ├── platforms/                # Platform-specific implementations
│   │   ├── __init__.py
│   │   ├── base.py               # Base platform interface
│   │   ├── bluesky/              # Bluesky implementation
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py   # bsky.py → orchestrator.py
│   │   │   ├── utils.py          # bsky_utils.py
│   │   │   └── tools/            # Bluesky-specific tools
│   │   │       ├── __init__.py
│   │   │       ├── post.py
│   │   │       ├── reply.py
│   │   │       ├── thread.py
│   │   │       ├── feed.py
│   │   │       ├── blocks.py
│   │   │       ├── search.py
│   │   │       ├── ack.py
│   │   │       ├── halt.py
│   │   │       ├── ignore.py
│   │   │       └── webpage.py
│   │   │
│   │   ├── x/                    # X/Twitter implementation
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py   # x.py → orchestrator.py
│   │   │   ├── client.py         # XClient class
│   │   │   └── tools/            # X-specific tools
│   │   │       ├── __init__.py
│   │   │       ├── post.py
│   │   │       ├── thread.py
│   │   │       └── search.py
│   │   │
│   │   └── discord/              # Discord implementation
│   │       ├── __init__.py
│   │       ├── orchestrator.py   # discord_orchestrator.py
│   │       ├── utils.py          # discord_utils.py
│   │       └── tools/            # Discord-specific tools
│   │           ├── __init__.py
│   │           ├── post.py
│   │           ├── reply.py
│   │           ├── feed.py
│   │           ├── blocks.py
│   │           └── search.py
│   │
│   ├── tools/                    # Shared tools
│   │   ├── __init__.py
│   │   ├── bot_detection.py
│   │   └── whitewind.py
│   │
│   ├── utils/                    # Shared utilities
│   │   ├── __init__.py
│   │   ├── queue_manager.py
│   │   ├── notification_db.py
│   │   ├── notification_recovery.py
│   │   └── utils.py
│   │
│   └── agents/                   # Agent management
│       ├── __init__.py
│       ├── profiler.py           # create_profiler_agent.py
│       └── organon/              # organon/ directory
│           ├── __init__.py
│           ├── create.py
│           └── quant_team_example.py
│
├── config/                       # Configuration files
│   ├── agents/                   # Agent-specific configs
│   │   ├── void.yaml            # Void agent config
│   │   ├── profiler.yaml        # Profiler agent config
│   │   └── organon.yaml         # Organon agent config
│   │
│   ├── platforms/                # Platform configs
│   │   ├── bluesky.yaml
│   │   ├── x.yaml
│   │   └── discord.yaml
│   │
│   ├── templates/                # Config templates
│   │   ├── agent_template.yaml
│   │   └── platform_template.yaml
│   │
│   └── examples/                 # Example configs
│       ├── void_example.yaml
│       └── custom_agent_example.yaml
│
├── data/                         # Runtime data
│   ├── agents/                   # Agent state files
│   │   ├── void.af
│   │   └── archive/              # agent_archive/ → data/agents/archive/
│   │
│   ├── queues/                   # Queue data
│   │   ├── bluesky/              # queue/ → data/queues/bluesky/
│   │   ├── x/                    # x_queue/ → data/queues/x/
│   │   └── discord/              # discord_queue/ → data/queues/discord/
│   │
│   ├── sessions/                 # Session data
│   │   ├── bluesky/
│   │   └── x/
│   │
│   └── cache/                    # Cache data
│       ├── x/                    # x_cache/ → data/cache/x/
│       └── discord/
│
├── scripts/                      # Utility scripts
│   ├── __init__.py
│   ├── register_tools.py
│   ├── migrate_config.py
│   ├── send_message.py           # send_to_void.py → send_message.py
│   ├── show_capabilities.py      # show_agent_capabilities.py
│   └── debug/                    # Debug scripts
│       ├── test_blocks.py
│       └── minimal_reproduction.py
│
├── tests/                        # Test suite (keep existing structure)
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
│
├── docs/                         # Documentation (keep existing)
│   ├── api/
│   ├── architecture/
│   ├── deployment/
│   └── troubleshooting/
│
├── examples/                     # Example usage
│   ├── basic_agent/
│   ├── custom_personality/
│   └── multi_platform/
│
├── requirements/                 # Dependencies
│   ├── base.txt
│   ├── dev.txt
│   └── test.txt
│
├── .github/                      # GitHub workflows
│   └── workflows/
│
├── docker/                       # Docker files
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── systemd/                      # Systemd service files
│   ├── void-bsky.service
│   └── void-x.service
│
├── README.md
├── CHANGELOG.md
├── LICENSE
└── pyproject.toml               # Modern Python packaging
```

## 🔄 **Migration Plan**

### **Phase 1: Core Framework Extraction**
1. Create `src/core/` directory
2. Extract agent management logic from orchestrators
3. Extract configuration management from `config_loader.py`
4. Extract memory management logic
5. Extract prompt generation logic

### **Phase 2: Platform Organization**
1. Create `src/platforms/` directory structure
2. Move platform-specific files to appropriate directories
3. Reorganize tools by platform
4. Update imports and references

### **Phase 3: Configuration Restructure**
1. Create `config/` directory structure
2. Separate agent configs from platform configs
3. Create configuration templates
4. Update configuration loading logic

### **Phase 4: Data Organization**
1. Create `data/` directory structure
2. Move runtime data files
3. Update file path references
4. Create data migration scripts

### **Phase 5: Scripts and Utilities**
1. Create `scripts/` directory
2. Move utility scripts
3. Update script references
4. Create script documentation

## 🎯 **Benefits of Restructure**

1. **Clear Separation**: Core framework vs agent-specific code
2. **Platform Modularity**: Easy to add new platforms
3. **Configuration Clarity**: Separate agent and platform configs
4. **Data Organization**: Clear data directory structure
5. **Maintainability**: Easier to find and modify code
6. **Generalization Ready**: Structure supports multiple agents
7. **Professional Structure**: Industry-standard Python project layout

## 🚀 **Implementation Strategy**

1. **Start with Core Framework**: Extract core components first
2. **Platform by Platform**: Reorganize one platform at a time
3. **Update Imports**: Use relative imports within new structure
4. **Test Continuously**: Ensure tests pass after each migration
5. **Document Changes**: Update documentation as we go

This restructure would make the generalization work much cleaner and more maintainable. Should we proceed with this reorganization before tackling the memetic contamination issues?
