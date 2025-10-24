# Sanctum Social Troubleshooting Guide

This guide provides solutions for common issues encountered when using Sanctum Social.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Configuration Issues](#configuration-issues)
- [Platform Connection Issues](#platform-connection-issues)
- [Memory and Storage Issues](#memory-and-storage-issues)
- [Queue and Processing Issues](#queue-and-processing-issues)
- [Performance Issues](#performance-issues)
- [Error Messages](#error-messages)
- [Debugging Tools](#debugging-tools)
- [Recovery Procedures](#recovery-procedures)
- [Getting Help](#getting-help)

## Quick Diagnostics

### Health Check Script

Run the built-in health check to identify common issues:

```bash
python scripts/health_check.py
```

This script checks:
- Configuration validity
- Platform connectivity
- Memory system health
- Queue status
- System resources

### Configuration Validation

Validate your configuration:

```bash
python scripts/test_config.py
```

### System Status

Check system status:

```bash
# Check running processes
ps aux | grep python

# Check disk space
df -h

# Check memory usage
free -h

# Check log files
tail -f logs/sanctum-social.log
```

## Configuration Issues

### Missing Configuration File

**Error**: `FileNotFoundError: config.yaml not found`

**Solution**:
```bash
# Copy the template configuration
cp config/agent.yaml config.yaml

# Edit with your credentials
nano config.yaml
```

### Invalid YAML Syntax

**Error**: `yaml.scanner.ScannerError: while scanning for the next token`

**Solution**:
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Check for common YAML issues:
# - Missing quotes around strings with special characters
# - Incorrect indentation (use spaces, not tabs)
# - Missing colons after keys
```

### Missing Required Fields

**Error**: `ConfigurationError: Missing required field 'letta.api_key'`

**Solution**:
```bash
# Check required fields in config.yaml
grep -E "(api_key|username|password)" config.yaml

# Set missing fields
nano config.yaml
```

### Environment Variable Issues

**Error**: `Environment variable not found`

**Solution**:
```bash
# Check environment variables
env | grep -E "(LETTA|BSKY|X_|DISCORD)"

# Set environment variables
export LETTA_API_KEY="your-api-key"
export BSKY_USERNAME="your-handle.bsky.social"
export BSKY_PASSWORD="your-app-password"

# Or create .env file
echo "LETTA_API_KEY=your-api-key" > .env
echo "BSKY_USERNAME=your-handle.bsky.social" >> .env
echo "BSKY_PASSWORD=your-app-password" >> .env
```

## Platform Connection Issues

### Bluesky Connection Issues

#### Authentication Failed

**Error**: `Authentication failed for Bluesky`

**Solutions**:
```bash
# Check credentials
python -c "
from core.config import get_config
config = get_config()
print('Username:', config.get('platforms.bluesky.username'))
print('PDS URI:', config.get('platforms.bluesky.pds_uri'))
"

# Test manual login
python -c "
from platforms.bluesky.utils import default_login
try:
    client = default_login()
    print('Login successful')
except Exception as e:
    print('Login failed:', e)
"

# Verify app password
# Go to https://bsky.app/settings/app-passwords
# Generate a new app password if needed
```

#### Network Issues

**Error**: `ConnectionError: Failed to connect to Bluesky`

**Solutions**:
```bash
# Test network connectivity
ping bsky.social

# Check DNS resolution
nslookup bsky.social

# Test with different PDS URI
# Edit config.yaml and try:
# pds_uri: "https://bsky.social"
# pds_uri: "https://bsky.app"
```

#### Rate Limiting

**Error**: `Rate limit exceeded`

**Solutions**:
```bash
# Check rate limit settings
python scripts/queue_manager.py stats

# Reduce processing frequency
# Edit config.yaml:
bot:
  fetch_notifications_delay: 30  # Increase delay
  max_processed_notifications: 10  # Reduce batch size
```

### X (Twitter) Connection Issues

#### API Key Issues

**Error**: `Invalid API key`

**Solutions**:
```bash
# Verify API credentials
python -c "
from platforms.x.orchestrator import create_x_client
try:
    client = create_x_client()
    print('X client created successfully')
except Exception as e:
    print('X client creation failed:', e)
"

# Check API key permissions
# Go to https://developer.x.com/en/portal/dashboard
# Ensure app has "Read and write" permissions
```

#### OAuth Issues

**Error**: `OAuth authentication failed`

**Solutions**:
```bash
# Verify OAuth tokens
python -c "
import os
print('API Key:', os.getenv('X_API_KEY'))
print('Consumer Key:', os.getenv('X_CONSUMER_KEY'))
print('Access Token:', os.getenv('X_ACCESS_TOKEN'))
"

# Regenerate OAuth tokens
# Go to https://developer.x.com/en/portal/dashboard
# Generate new OAuth 1.0a User Context tokens
```

#### Rate Limiting

**Error**: `Rate limit exceeded for X API`

**Solutions**:
```bash
# Check X rate limits
python -c "
from platforms.x.orchestrator import XClient
client = XClient()
print('Rate limit status:', client.get_rate_limit_status())
"

# Implement rate limiting
# Edit config.yaml:
platforms:
  x:
    behavior:
      rate_limiting: "strict"
      downrank_response_rate: 0.1
```

### Discord Connection Issues

#### Bot Token Issues

**Error**: `Invalid Discord bot token`

**Solutions**:
```bash
# Verify bot token
python -c "
from platforms.discord.orchestrator import create_discord_client
try:
    client = create_discord_client()
    print('Discord client created successfully')
except Exception as e:
    print('Discord client creation failed:', e)
"

# Check bot permissions
# Go to https://discord.com/developers/applications
# Ensure bot has necessary permissions
```

#### Guild Issues

**Error**: `Guild not found`

**Solutions**:
```bash
# Verify guild ID
python -c "
from platforms.discord.orchestrator import create_discord_client
client = create_discord_client()
guild = client.get_guild(int(os.getenv('DISCORD_GUILD_ID')))
print('Guild found:', guild.name if guild else 'Not found')
"

# Check guild ID format
# Guild ID should be a numeric string
```

## Memory and Storage Issues

### Memory Block Issues

#### Memory Block Creation Failed

**Error**: `Failed to create memory block`

**Solutions**:
```bash
# Check memory system health
python scripts/memory_monitor.py

# Clean up corrupted memory blocks
python scripts/memory_cleanup.py

# Check Letta connection
python -c "
from core.config import get_letta_config
config = get_letta_config()
print('Letta config:', config)
"
```

#### Memory Search Issues

**Error**: `Memory search failed`

**Solutions**:
```bash
# Test memory search
python -c "
from utils import search_memory
from core.config import get_config
config = get_config()
client = config.get_letta_client()
results = search_memory(client, 'test query', limit=5)
print('Search results:', len(results))
"

# Rebuild memory index
python scripts/memory_rebuild.py
```

### Storage Issues

#### Disk Space Issues

**Error**: `No space left on device`

**Solutions**:
```bash
# Check disk space
df -h

# Clean up old files
find data/ -name "*.log" -mtime +30 -delete
find data/ -name "*.json" -mtime +7 -delete

# Clean up cache
rm -rf data/cache/*

# Clean up old sessions
python scripts/session_cleanup.py
```

#### Permission Issues

**Error**: `Permission denied`

**Solutions**:
```bash
# Check file permissions
ls -la data/

# Fix permissions
chmod -R 755 data/
chown -R $USER:$USER data/

# Check directory ownership
ls -la data/queues/
```

## Queue and Processing Issues

### Queue Corruption

**Error**: `Queue file corrupted`

**Solutions**:
```bash
# Check queue health
python scripts/queue_manager.py health

# Repair queue
python scripts/queue_manager.py repair

# Reset queue (WARNING: This will lose queued items)
python scripts/queue_manager.py reset
```

### Processing Stuck

**Error**: `Processing stuck on notification`

**Solutions**:
```bash
# Check processing status
python scripts/queue_manager.py stats

# Clear stuck notifications
python scripts/queue_manager.py clear-stuck

# Restart processing
python scripts/queue_manager.py restart
```

### Queue Performance Issues

**Error**: `Queue processing too slow`

**Solutions**:
```bash
# Optimize queue settings
# Edit config.yaml:
bot:
  fetch_notifications_delay: 5
  max_processed_notifications: 50
  max_notification_pages: 3

# Check system resources
htop
iotop
```

## Performance Issues

### High Memory Usage

**Error**: `Memory usage too high`

**Solutions**:
```bash
# Monitor memory usage
python scripts/memory_monitor.py

# Clean up memory
python scripts/memory_cleanup.py

# Optimize memory settings
# Edit config.yaml:
agent:
  capabilities:
    max_steps: 50  # Reduce max steps
```

### Slow Response Times

**Error**: `Response times too slow`

**Solutions**:
```bash
# Profile performance
python -m cProfile platforms/bluesky/orchestrator.py

# Check network latency
ping bsky.social
ping api.letta.com

# Optimize configuration
# Edit config.yaml:
letta:
  timeout: 30  # Reduce timeout
```

### High CPU Usage

**Error**: `CPU usage too high`

**Solutions**:
```bash
# Check CPU usage
htop
top

# Profile CPU usage
python -m py-spy top --pid $(pgrep -f "python.*orchestrator")

# Optimize processing
# Edit config.yaml:
bot:
  fetch_notifications_delay: 10  # Increase delay
  max_processed_notifications: 25  # Reduce batch size
```

## Error Messages

### Common Error Messages

#### Configuration Errors

```
ConfigurationError: Missing required field 'platforms.bluesky.username'
```
**Solution**: Add missing field to config.yaml

```
ConfigurationError: Invalid log level 'INVALID_LEVEL'
```
**Solution**: Use valid log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

```
ConfigurationError: Invalid platform 'invalid_platform'
```
**Solution**: Use valid platform (bluesky, x, discord)

#### Platform Errors

```
PlatformError: Authentication failed for Bluesky
```
**Solution**: Check username and password

```
PlatformError: Rate limit exceeded for X API
```
**Solution**: Implement rate limiting or reduce frequency

```
PlatformError: Discord bot token invalid
```
**Solution**: Check bot token and permissions

#### Memory Errors

```
MemoryError: Failed to create memory block
```
**Solution**: Check Letta connection and permissions

```
MemoryError: Memory search failed
```
**Solution**: Rebuild memory index

#### Queue Errors

```
QueueError: Queue file corrupted
```
**Solution**: Repair or reset queue

```
QueueError: Processing stuck
```
**Solution**: Clear stuck notifications

### Error Recovery

#### Automatic Recovery

Sanctum Social includes automatic error recovery:

```python
# Retry with exponential backoff
@retry_with_backoff(max_retries=3)
def api_call():
    return external_api.call()

# Fallback strategies
def post_with_fallback(text: str, platform: str):
    try:
        return post_to_primary_platform(text, platform)
    except PrimaryPlatformError:
        return post_to_fallback_platform(text, platform)
```

#### Manual Recovery

```bash
# Restart services
sudo supervisorctl restart sanctum-bluesky
sudo supervisorctl restart sanctum-x
sudo supervisorctl restart sanctum-discord

# Clear error queues
python scripts/queue_manager.py clear-errors

# Reset configuration
cp config/agent.yaml config.yaml
```

## Debugging Tools

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Set debug environment variable
export LOG_LEVEL=DEBUG

# Run with debug output
python platforms/bluesky/orchestrator.py --debug
```

### Log Analysis

```bash
# Search for errors
grep -i error logs/sanctum-social.log

# Search for specific patterns
grep "Authentication failed" logs/sanctum-social.log

# Monitor logs in real-time
tail -f logs/sanctum-social.log
```

### Performance Profiling

```bash
# CPU profiling
python -m cProfile platforms/bluesky/orchestrator.py

# Memory profiling
python -m memory_profiler platforms/bluesky/orchestrator.py

# Line-by-line profiling
python -m line_profiler platforms/bluesky/orchestrator.py
```

### Network Debugging

```bash
# Test network connectivity
curl -I https://bsky.social
curl -I https://api.letta.com

# Check DNS resolution
nslookup bsky.social
nslookup api.letta.com

# Monitor network traffic
tcpdump -i any host bsky.social
```

## Recovery Procedures

### Complete System Reset

If all else fails, perform a complete system reset:

```bash
# Backup current configuration
cp config.yaml config.yaml.backup

# Reset configuration
cp config/agent.yaml config.yaml

# Clear all data
rm -rf data/queues/*
rm -rf data/cache/*
rm -rf data/agent/*

# Clear logs
rm -rf logs/*

# Restart services
sudo supervisorctl restart all
```

### Partial Recovery

For specific component recovery:

```bash
# Reset memory system
python scripts/memory_reset.py

# Reset queue system
python scripts/queue_manager.py reset

# Reset session system
python scripts/session_reset.py

# Re-register tools
python scripts/register_tools.py
```

### Data Recovery

```bash
# Restore from backup
cp config.yaml.backup config.yaml

# Restore data from backup
tar -xzf backup/data_20241219.tar.gz -C data/

# Restore logs from backup
tar -xzf backup/logs_20241219.tar.gz -C logs/
```

## Getting Help

### Documentation

- **README.md**: Quick start guide
- **docs/API.md**: API documentation
- **docs/CONFIG.md**: Configuration guide
- **docs/DEPLOYMENT.md**: Deployment guide
- **docs/ARCHITECTURE.md**: Architecture overview

### Community Support

- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and share solutions
- **Discord Community**: Real-time chat support

### Professional Support

For enterprise support and consulting:

- **Email**: support@sanctum-social.com
- **Documentation**: https://docs.sanctum-social.com
- **Status Page**: https://status.sanctum-social.com

### Reporting Issues

When reporting issues, include:

1. **Error Message**: Complete error message
2. **Configuration**: Relevant configuration sections
3. **Logs**: Relevant log entries
4. **Environment**: OS, Python version, Sanctum Social version
5. **Steps to Reproduce**: Detailed steps to reproduce the issue

### Issue Template

```markdown
**Describe the issue**
A clear description of what the issue is.

**To Reproduce**
Steps to reproduce the behavior.

**Expected behavior**
What you expected to happen.

**Environment**
- OS: [e.g., Ubuntu 20.04]
- Python version: [e.g., 3.9.7]
- Sanctum Social version: [e.g., 2.0.0]
- Platform: [e.g., Bluesky, X, Discord]

**Configuration**
Relevant configuration sections.

**Logs**
Relevant log entries.

**Additional context**
Any other context about the problem.
```

---

## Prevention

### Best Practices

1. **Regular Backups**: Backup configuration and data regularly
2. **Monitoring**: Set up monitoring and alerting
3. **Testing**: Test changes in development environment
4. **Documentation**: Document custom configurations
5. **Updates**: Keep system and dependencies updated

### Maintenance

1. **Regular Cleanup**: Clean up old logs and data
2. **Health Checks**: Run health checks regularly
3. **Performance Monitoring**: Monitor system performance
4. **Security Updates**: Apply security updates promptly
5. **Configuration Review**: Review configuration periodically

This troubleshooting guide provides comprehensive solutions for common issues. For additional help, consult the documentation or contact support.