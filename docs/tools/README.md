# Tool Documentation

This folder contains documentation for specific tools and capabilities within Sanctum Social.

## 📋 Tool Documents

### Tool Management
- **`TOOL_MANAGEMENT.md`** - Tool management and registration guide
  - How to register tools with Letta
  - Tool lifecycle management
  - Platform-specific tool handling

- **`TOOL_CHANGELOG.md`** - Tool development changelog
  - History of tool additions and modifications
  - Version tracking for tool capabilities
  - Breaking changes and migrations

### Platform-Specific Tools
- **`whitewind_tool_guide.md`** - Whitewind blog post creation tool guide
  - ATProto blog post creation
  - Whitewind integration patterns
  - Usage examples and best practices

- **`X_TOOL_APPROACH.md`** - X (Twitter) tool implementation approach
  - X API integration patterns
  - OAuth1 authentication handling
  - Tweet threading and user management

## 🎯 Purpose

These documents are intended for:
- **Tool Developers**: Creating new tools for Sanctum Social
- **Platform Integrators**: Adding support for new platforms
- **Users**: Understanding available tools and capabilities
- **Maintainers**: Managing tool lifecycle and updates

## 🛠️ Tool Categories

### Core Tools
- Bot detection and user profiling
- Memory management and archival
- Session management and recovery

### Platform Tools
- **Bluesky**: Posting, replying, feed reading, user research
- **X (Twitter)**: Tweet threading, user memory, OAuth1 auth
- **Discord**: Server integration, channel management

### Utility Tools
- **Whitewind**: Blog post creation on ATProto
- **Search**: Cross-platform content search
- **Analytics**: User interaction tracking

## 📝 Development Guidelines

When creating new tools:

1. **Documentation First**: Create comprehensive documentation before implementation
2. **Platform Agnostic**: Design tools to work across multiple platforms when possible
3. **Error Handling**: Include robust error handling and recovery mechanisms
4. **Testing**: Provide comprehensive test coverage
5. **Examples**: Include practical usage examples

## 🔄 Contributing

When adding new tool documentation:
- Follow the established naming conventions
- Include usage examples and best practices
- Cross-reference related tools and platforms
- Update this README.md when adding new files

## 📚 Related Documentation

- **API Reference**: See `../API.md` for complete tool API documentation
- **Platform Guides**: See `../platforms/` for platform-specific documentation
- **Configuration**: See `../CONFIG.md` for tool configuration options
