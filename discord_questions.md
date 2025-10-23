# Discord Behavior Rules - Open Questions

## 1. Message Handling & Response Triggers

### How should Void respond to Discord messages?
- Only when directly mentioned (`@void`)?
- Respond to any message in specific channels?
- Respond to DMs?
- Respond to replies to Void's messages?

### What about message threading?
- Discord has threads within channels - should Void participate in those?
- How should Void handle thread vs. main channel responses?

## 2. Channel & Server Management

### Which channels should Void be active in?
- All channels it has access to?
- Only specific channels (like `#general`, `#ai-chat`)?
- Should there be a "Void zone" channel?

### How should Void handle different servers?
- Same behavior across all servers?
- Server-specific configuration?
- Should Void remember context across servers?

## 3. User Interaction & Blocking

### How should Discord user blocking work?
- Block users from specific servers?
- Global Discord user blocking?
- How does this interact with server moderation?

### What about server roles and permissions?
- Should Void respect Discord role hierarchies?
- Should certain roles be immune to Void's responses?
- How should Void handle server admins vs. regular users?

## 4. Content & Behavior Rules

### What content should Void avoid responding to?
- NSFW channels?
- Spam or low-quality content?
- Off-topic discussions?

### How should Void handle Discord-specific features?
- Should Void react to emoji reactions?
- Should Void respond to slash commands?
- How should Void handle voice channel mentions?

## 5. Rate Limiting & Spam Prevention

### How should Void handle Discord's rate limits?
- Discord has stricter rate limits than Bluesky/X
- Should Void be more conservative with responses?
- How should Void handle server-specific rate limits?

### Spam prevention:
- Should Void have cooldowns between responses?
- How should Void handle rapid-fire messages in channels?

## 6. Context & Memory

### How should Void maintain context in Discord?
- Discord channels have persistent history
- Should Void remember previous conversations in channels?
- How should Void handle long-running discussions?

### Cross-platform memory:
- Should Void remember users across Discord, Bluesky, and X?
- How should Void handle users who exist on multiple platforms?

## 7. Moderation & Safety

### How should Void handle Discord moderation?
- Should Void report problematic content to server mods?
- Should Void have its own moderation capabilities?
- How should Void handle being kicked/banned from servers?

### Content filtering:
- Should Void have different content rules for Discord vs. other platforms?
- How should Void handle Discord's content policies?

## Recommended Approach

1. **Start Simple**: Begin with basic mention-based responses in specific channels
2. **Iterate**: Add features gradually based on usage patterns
3. **Server-Specific**: Allow different behavior per server/channel
4. **Conservative**: Be more conservative with responses due to Discord's social nature

## Dependencies

- Discord bot token and permissions
- Guild/channel IDs for testing
- `discord.py` library
- Integration with existing queue management system
