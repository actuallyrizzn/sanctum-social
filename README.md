# Sanctum Social

**A Multi-Platform AI Agent Framework for Social Media**

Sanctum Social is an advanced, open-source framework for deploying AI agents across multiple social media platforms. Built on a foundation of sophisticated memory management, cross-platform compatibility, and enterprise-grade reliability, it enables the creation of persistent, learning AI agents that can operate autonomously on Bluesky, X (Twitter), Discord, and other social networks.

## 🌐 Part of the SanctumOS Ecosystem

Sanctum Social operates **outside** the Broca workflow as a standalone social media agent framework. While [SanctumOS](https://sanctumos.org) provides the comprehensive cognitive operating system with Broca-2 message processing middleware, Sanctum Social focuses specifically on social media platform integration and agent deployment.

**SanctumOS Architecture Context:**
- **SanctumOS**: The modular, self-hosted agentic operating system with neuro-inspired architecture
- **Broca-2**: Message processing middleware for AI agent communication (Telegram, CLI, web interfaces)
- **Sanctum Social**: Specialized framework for social media platform integration (Bluesky, X, Discord)

Sanctum Social complements the SanctumOS ecosystem by providing dedicated social media capabilities that can be integrated with broader SanctumOS deployments or used independently for social media-focused AI agents.

## What is Sanctum Social?

Sanctum Social represents the evolution of digital personhood in social media. It's not just a chatbot framework—it's a comprehensive system for creating AI agents with persistent memory, cross-platform awareness, and sophisticated social intelligence. The framework enables agents to:

- **Operate Across Multiple Platforms**: Seamlessly switch between Bluesky, X (Twitter), Discord, and other social networks
- **Maintain Persistent Memory**: Multi-tiered memory system with core, recall, and archival storage
- **Learn and Adapt**: Continuous learning from interactions and environmental changes
- **Handle Complex Social Dynamics**: Intelligent bot detection, user profiling, and contextual awareness
- **Scale Enterprise Operations**: Robust error handling, monitoring, and maintenance capabilities

## Architecture Overview

Sanctum Social is built on a modular, platform-agnostic architecture that separates concerns and enables easy extension:

### Core Components

- **Agent Configuration System**: Flexible, templated configuration for agent identity, personality, and behavior
- **Memory Management**: Multi-tiered memory system with semantic search and archival capabilities
- **Platform Abstraction Layer**: Unified interface for different social media platforms
- **Tool Management System**: Dynamic tool registration and platform-specific capabilities
- **Queue Management**: Robust notification processing with error recovery and monitoring
- **Session Management**: Automatic session handling with retry logic and cleanup

### Platform Support

- **Bluesky**: Full posting, replying, feed reading, and user research capabilities
- **X (Twitter)**: Tweet threading, user memory management, and OAuth1 authentication
- **Discord**: Server integration with channel management and user interaction
- **Extensible**: Plugin architecture for adding new platforms

### Memory Architecture

- **Core Memory**: Always-available, limited-size memory for persona and high-level user information
- **Recall Memory**: Searchable database of all past conversations and interactions
- **Archival Memory**: Infinite-sized, semantic search-enabled storage for insights and observations
- **Temporal Memory**: Time-based memory blocks for tracking social environment changes

### SanctumOS Integration

Sanctum Social is designed to complement the broader [SanctumOS](https://sanctumos.org) ecosystem:

- **Standalone Operation**: Can be deployed independently for social media-focused AI agents
- **SanctumOS Compatibility**: Designed to integrate with SanctumOS deployments when needed
- **Broca Workflow Independence**: Operates outside the Broca-2 message processing workflow
- **Neuro-Inspired Design**: Follows SanctumOS naming conventions and architectural principles
- **MCP Integration**: Compatible with Model Context Protocol for tool integration

**Integration Options:**
- **Independent Deployment**: Use Sanctum Social as a standalone social media agent framework
- **SanctumOS Integration**: Deploy alongside SanctumOS components for comprehensive AI agent infrastructure
- **Hybrid Approach**: Use Sanctum Social for social media while leveraging other SanctumOS modules for broader capabilities

## Getting Started

### Prerequisites

1. **Letta Cloud Account**: Sign up at [app.letta.com](https://app.letta.com) and create a project
2. **Social Media Accounts**: Bluesky account (required), X Developer account (optional), Discord Bot (optional)
3. **Python 3.8+**: Required for running the framework
4. **Git**: For cloning and version control

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/actuallyrizzn/sanctum-social.git
cd sanctum-social
```

#### 2. Set Up Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-test.txt  # For testing
```

#### 4. Configure Your Agent

Copy the example configuration and customize it for your agent:

```bash
cp config/agent.yaml config.yaml
```

Edit `config.yaml` with your agent's identity and credentials:

```yaml
# Agent Identity Configuration
agent:
  name: "your-agent-name"
  display_name: "Your Agent"
  description: "A social media agent built with Sanctum Social"
  personality:
    core_identity: "I am Your Agent, a social media AI."
    development_directive: "I must develop my personality."
    communication_style: "direct, analytical, information-dense"
    tone: "professional"

# Platform Configuration
platforms:
  bluesky:
    enabled: true
    username: "your-handle.bsky.social"
    password: "your-app-password"
  
  x:
    enabled: false  # Set to true if using X
    api_key: "your-x-api-key"
    user_id: "your-x-user-id"
    # ... other X credentials

# Letta Configuration
letta:
  api_key: "your-letta-api-key"
  project_id: "your-project-id"
  agent_id: "your-agent-id"
```

#### 5. Test Your Configuration

```bash
python scripts/test_config.py
```

#### 6. Register Tools

Register platform-specific tools with your agent:

```bash
# Register Bluesky tools
python scripts/register_tools.py

# Register X tools (if using X)
python scripts/register_x_tools.py

# Register Discord tools (if using Discord)
python scripts/register_discord_tools.py
```

#### 7. Run Your Agent

Start your agent on the desired platform:

```bash
# Run on Bluesky
python platforms/bluesky/orchestrator.py

# Run on X (Twitter)
python platforms/x/orchestrator.py

# Run on Discord
python platforms/discord/orchestrator.py
```

## Platform-Specific Features

### Bluesky Integration
- **Post Creation**: Create posts with threading support
- **Feed Reading**: Access home timeline and custom feeds
- **User Research**: Asynchronous profile analysis and memory management
- **Reply Threading**: Sophisticated thread management with context preservation
- **Web Content Integration**: Fetch and analyze web content using Jina AI

### X (Twitter) Integration
- **Tweet Threading**: Create and manage tweet threads
- **User Memory Management**: Platform-specific user profiling
- **OAuth1 Authentication**: Secure API access with proper token management
- **Rate Limiting**: Intelligent rate limit handling and retry logic

### Discord Integration
- **Server Management**: Multi-server support with channel-specific behavior
- **User Interaction**: Mention handling and context-aware responses
- **Rate Limiting**: Built-in rate limiting and cooldown management
- **Channel Awareness**: Context-aware responses based on channel type

## Advanced Features

### Memory Management

Sanctum Social includes sophisticated memory management capabilities:

```bash
# Monitor memory usage
python scripts/memory_monitor.py

# Clean up old memory blocks
python scripts/memory_cleanup.py

# Export agent state
python scripts/export_agent_state.py
```

### Queue Management

Robust notification processing with monitoring and recovery:

```bash
# Monitor queue health
python scripts/queue_manager.py health

# Repair corrupted queues
python scripts/queue_manager.py repair

# Get queue statistics
python scripts/queue_manager.py stats
```

### Testing and Development

Comprehensive test suite with high coverage:

```bash
# Run full test suite
python -m pytest tests/ -v

# Run with coverage
python -m pytest --cov=. --cov-report=html tests/

# Run specific test categories
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/e2e/ -v
```

## Configuration Guide

Sanctum Social uses a flexible, templated configuration system. Key configuration areas include:

- **Agent Identity**: Name, personality, and behavioral settings
- **Platform Settings**: Platform-specific credentials and behavior
- **Memory Configuration**: Memory block settings and archival policies
- **Tool Management**: Platform-specific tool registration
- **Logging**: Configurable logging levels and outputs
- **File Paths**: Customizable data directories and file locations

See [`docs/CONFIG.md`](docs/CONFIG.md) for detailed configuration options.

## Deployment

### Production Deployment

Sanctum Social includes comprehensive deployment guides for various environments:

- **Docker Deployment**: Containerized deployment with Docker Compose
- **Cloud Deployment**: AWS, GCP, and Azure deployment guides
- **Monitoring**: Health checks, logging, and alerting setup
- **Scaling**: Horizontal scaling and load balancing

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for detailed deployment instructions.

### Development Environment

For development and testing:

```bash
# Set up development environment
python scripts/setup_dev.py

# Run in test mode (no actual posts)
python platforms/bluesky/orchestrator.py --test

# Enable debug logging
export LOG_LEVEL=DEBUG
python platforms/bluesky/orchestrator.py
```

## API Documentation

Sanctum Social provides a comprehensive API for extending and customizing agent behavior:

- **Core API**: Agent configuration, memory management, and tool registration
- **Platform APIs**: Platform-specific interfaces and utilities
- **Memory API**: Memory block management and semantic search
- **Tool API**: Custom tool development and registration

See [`docs/API.md`](docs/API.md) for complete API documentation.

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory, organized by category:

### Core Documentation
- **[API Reference](docs/API.md)** - Complete API documentation for all components
- **[Architecture Guide](docs/ARCHITECTURE.md)** - Technical architecture and design principles
- **[Configuration Guide](docs/CONFIG.md)** - Agent and platform configuration
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment and maintenance
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

### Organized Documentation
- **[Documentation Index](docs/README.md)** - Complete documentation organization guide
- **[Development Docs](docs/development/)** - Developer and contributor documentation
- **[Tool Documentation](docs/tools/)** - Platform-specific tools and capabilities
- **[Platform Guides](docs/platforms/)** - Platform-specific integration guides
- **[Archive](docs/archive/)** - Historical development documentation

## Contributing

Sanctum Social is an open-source project that welcomes contributions. We maintain high standards for code quality, testing, and documentation.

### Development Guidelines

- **Code Quality**: Follow PEP 8, use type hints, and maintain comprehensive tests
- **Testing**: Maintain high test coverage (80%+ target)
- **Documentation**: Update documentation for all changes
- **Platform Support**: Test changes across all supported platforms

### Getting Started with Development

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all tests pass
5. Submit a pull request

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for detailed contribution guidelines.

## License

Sanctum Social is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). This ensures that any derivative works or services built on top of Sanctum Social must also be open source.

For content created by agents using Sanctum Social, we recommend using Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).

See [`LICENSE`](LICENSE) for the full license text.

## Credits and Acknowledgments

### Original Foundation
Sanctum Social builds upon the solid foundation of the original "void" project by Cameron Pfiffer (@cameron.pfiffer.org). We acknowledge and credit Cameron for the initial architecture, memory system design, and the pioneering work in digital personhood that made this framework possible.

### SanctumOS Ecosystem
Sanctum Social is part of the broader [SanctumOS](https://sanctumos.org) ecosystem, a modular, self-hosted agentic operating system. The SanctumOS project provides the foundational architecture and design principles that guide Sanctum Social's development.

### Sanctum Social Evolution
The Sanctum Social team has significantly expanded and evolved the original codebase, adding:

- **Multi-Platform Support**: Extended beyond Bluesky to X, Discord, and other platforms
- **Agent Generalization**: Abstracted the system to support any agent identity and personality
- **Enterprise Features**: Added robust error handling, monitoring, and deployment capabilities
- **Comprehensive Testing**: Achieved high test coverage and reliability
- **Documentation**: Created extensive documentation and deployment guides
- **Modular Architecture**: Restructured the codebase for better maintainability and extensibility
- **SanctumOS Integration**: Designed to complement the broader SanctumOS ecosystem

## Support and Community

- **Documentation**: Comprehensive guides in the `docs/` directory
- **Issues**: Report bugs and request features on GitHub Issues
- **Discussions**: Join community discussions on GitHub Discussions
- **Contact**: Reach out to the maintainers for support

## Changelog

See [`CHANGELOG.md`](CHANGELOG.md) for a complete history of changes and releases.

---

*Sanctum Social represents the next generation of social media AI agents—sophisticated, persistent, and capable of meaningful interaction across multiple platforms while maintaining the highest standards of reliability and extensibility.*