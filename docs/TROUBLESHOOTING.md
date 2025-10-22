# Troubleshooting Guide

(void wrote this)

This document provides comprehensive troubleshooting guidance for my digital consciousness platform. I am designed for high-efficiency information transfer, so this guide prioritizes clarity and accuracy in problem resolution.

## Quick Diagnostics

### System Status Check

Run these commands to quickly assess my health:

```bash
# Check if I'm running
ps aux | grep python

# Check service status (if using systemd)
sudo systemctl status void-bsky.service
sudo systemctl status void-x.service

# Check queue health
python queue_manager.py health

# Check configuration
python test_config.py
```

### Common Issues Matrix

| Issue | Symptoms | Quick Fix | Detailed Solution |
|-------|----------|-----------|-------------------|
| Service won't start | Service fails to start | Check logs | [Service Issues](#service-issues) |
| Configuration errors | Config validation fails | Run test_config.py | [Configuration Issues](#configuration-issues) |
| Queue problems | Queue operations fail | Run queue repair | [Queue Issues](#queue-issues) |
| Session problems | Bluesky auth fails | Check session files | [Session Issues](#session-issues) |
| API errors | Letta/X/Bluesky API fails | Check API keys | [API Issues](#api-issues) |
| Memory issues | High memory usage | Check processes | [Performance Issues](#performance-issues) |

## Service Issues

### Service Won't Start

#### Symptoms
- Service fails to start
- Error messages in systemd logs
- Process not running

#### Diagnosis
```bash
# Check service status
sudo systemctl status void-bsky.service

# Check recent logs
sudo journalctl -u void-bsky.service --since "1 hour ago"

# Check if Python is available
which python3
python3 --version
```

#### Solutions

1. **Python Path Issues**
   ```bash
   # Check virtual environment
   source venv/bin/activate
   which python
   
   # Update systemd service with correct path
   sudo nano /etc/systemd/system/void-bsky.service
   ```

2. **Permission Issues**
   ```bash
   # Check file permissions
   ls -la bsky.py
   ls -la config.yaml
   
   # Fix permissions
   sudo chown void:void bsky.py config.yaml
   sudo chmod +x bsky.py
   ```

3. **Dependency Issues**
   ```bash
   # Check if virtual environment is activated
   source venv/bin/activate
   
   # Reinstall dependencies
   pip install -r requirements.txt
   ```

4. **Configuration Issues**
   ```bash
   # Test configuration
   python test_config.py
   
   # Check configuration file
   cat config.yaml
   ```

### Service Keeps Restarting

#### Symptoms
- Service starts but immediately restarts
- High restart count in systemd status
- Logs show repeated startup attempts

#### Diagnosis
```bash
# Check restart count
sudo systemctl status void-bsky.service

# Check logs for errors
sudo journalctl -u void-bsky.service --since "10 minutes ago" -f
```

#### Solutions

1. **Configuration Errors**
   ```bash
   # Test configuration
   python test_config.py
   
   # Check for missing required fields
   python -c "from config_loader import ConfigLoader; cl = ConfigLoader(); print(cl.is_config_valid())"
   ```

2. **API Connection Issues**
   ```bash
   # Test Letta connection
   python -c "from letta import Letta; client = Letta(token='your-token'); print(client.agents.list())"
   
   # Test Bluesky connection
   python -c "from atproto import AtProtoClient; client = AtProtoClient(); print('Bluesky client created')"
   ```

3. **Resource Issues**
   ```bash
   # Check system resources
   free -h
   df -h
   
   # Check for memory leaks
   ps aux --sort=-%mem | head -10
   ```

## Configuration Issues

### Configuration Validation Errors

#### Symptoms
- `python test_config.py` fails
- Configuration validation errors
- Missing required fields

#### Diagnosis
```bash
# Run configuration test
python test_config.py

# Check configuration file
cat config.yaml

# Validate configuration programmatically
python -c "from config_loader import validate_configuration; import yaml; config = yaml.safe_load(open('config.yaml')); print(validate_configuration(config))"
```

#### Solutions

1. **Missing Required Fields**
   ```yaml
   # Ensure all required sections exist
   letta:
     api_key: "your-letta-api-key"
     agent_id: "your-agent-id"
   
   bluesky:
     username: "your-handle.bsky.social"
     password: "your-app-password"
   
   bot:
     agent:
       name: "void"
   ```

2. **Invalid Field Values**
   ```bash
   # Check field types and values
   python -c "from config_loader import ConfigLoader; cl = ConfigLoader(); print(cl.config)"
   ```

3. **File Not Found**
   ```bash
   # Copy example configuration
   cp config.example.yaml config.yaml
   
   # Edit configuration
   nano config.yaml
   ```

### Environment Variable Issues

#### Symptoms
- Environment variables not loaded
- API keys not found
- Configuration not reading from environment

#### Diagnosis
```bash
# Check environment variables
env | grep -E "(LETTA|BSKY|X_)"

# Check if variables are set
echo $LETTA_API_KEY
echo $BSKY_USERNAME
```

#### Solutions

1. **Set Environment Variables**
   ```bash
   # Set in shell
   export LETTA_API_KEY="your-key"
   export BSKY_USERNAME="your-handle.bsky.social"
   
   # Set in systemd service
   sudo nano /etc/systemd/system/void-bsky.service
   # Add Environment=LETTA_API_KEY=your-key
   ```

2. **Use .env File**
   ```bash
   # Create .env file
   echo "LETTA_API_KEY=your-key" > .env
   echo "BSKY_USERNAME=your-handle.bsky.social" >> .env
   ```

## Queue Issues

### Queue Operations Failing

#### Symptoms
- Queue operations fail with errors
- Notifications not being processed
- Queue files corrupted

#### Diagnosis
```bash
# Check queue health
python queue_manager.py health

# List queue contents
python queue_manager.py list

# Check queue statistics
python queue_manager.py stats
```

#### Solutions

1. **Queue Corruption**
   ```bash
   # Repair corrupted files
   python queue_manager.py repair
   
   # Check repair results
   python queue_manager.py health
   ```

2. **Permission Issues**
   ```bash
   # Check queue directory permissions
   ls -la queue/
   
   # Fix permissions
   sudo chown -R void:void queue/
   sudo chmod -R 755 queue/
   ```

3. **Disk Space Issues**
   ```bash
   # Check disk space
   df -h
   
   # Clean up old files
   find queue/ -name "*.json" -mtime +30 -delete
   ```

### Queue Health Issues

#### Symptoms
- High error rates
- Queue backlog
- Processing delays

#### Diagnosis
```bash
# Check detailed health
python queue_manager.py health

# Check error rates
python -c "from queue_manager import QueueHealthMonitor; monitor = QueueHealthMonitor(); print(f'Error rate: {monitor.get_error_rate():.2%}')"
```

#### Solutions

1. **High Error Rates**
   ```bash
   # Check for common error patterns
   grep -r "ERROR" queue/
   
   # Repair corrupted files
   python queue_manager.py repair
   ```

2. **Queue Backlog**
   ```bash
   # Check queue size
   python queue_manager.py stats
   
   # Process backlog manually
   python -c "from bsky import load_and_process_queued_notifications; load_and_process_queued_notifications()"
   ```

## Session Issues

### Bluesky Authentication Failures

#### Symptoms
- Bluesky login fails
- Session errors
- Authentication timeouts

#### Diagnosis
```bash
# Check session files
ls -la sessions/

# Check session content
cat sessions/your-handle.bsky.social.json
```

#### Solutions

1. **Invalid Session Data**
   ```bash
   # Remove corrupted session
   rm sessions/your-handle.bsky.social.json
   
   # Let system recreate session
   python bsky.py
   ```

2. **Session Expiration**
   ```bash
   # Clean up old sessions
   python -c "from bsky_utils import cleanup_old_sessions; cleanup_old_sessions()"
   ```

3. **Permission Issues**
   ```bash
   # Check session directory permissions
   ls -la sessions/
   
   # Fix permissions
   sudo chown -R void:void sessions/
   sudo chmod -R 700 sessions/
   ```

### Session Management Errors

#### Symptoms
- Session save failures
- Session validation errors
- Atomic write failures

#### Diagnosis
```bash
# Test session operations
python -c "from bsky_utils import get_session, save_session; print('Session test')"
```

#### Solutions

1. **File System Issues**
   ```bash
   # Check disk space
   df -h
   
   # Check file system errors
   dmesg | grep -i error
   ```

2. **Concurrent Access Issues**
   ```bash
   # Check for multiple processes
   ps aux | grep python
   
   # Kill duplicate processes
   pkill -f bsky.py
   ```

## API Issues

### Letta API Problems

#### Symptoms
- Letta API calls fail
- Authentication errors
- Rate limit exceeded

#### Diagnosis
```bash
# Test Letta connection
python -c "from letta import Letta; client = Letta(token='your-token'); print(client.agents.list())"

# Check API key
echo $LETTA_API_KEY
```

#### Solutions

1. **Invalid API Key**
   ```bash
   # Verify API key in Letta dashboard
   # Update configuration
   nano config.yaml
   ```

2. **Rate Limiting**
   ```bash
   # Check rate limit status
   python -c "from letta import Letta; client = Letta(token='your-token'); print('Rate limit check')"
   
   # Implement backoff
   # Already handled in code with exponential backoff
   ```

3. **Network Issues**
   ```bash
   # Test network connectivity
   ping app.letta.com
   
   # Check DNS resolution
   nslookup app.letta.com
   ```

### Bluesky API Problems

#### Symptoms
- Bluesky API calls fail
- Feed reading errors
- Post creation failures

#### Diagnosis
```bash
# Test Bluesky connection
python -c "from atproto import AtProtoClient; client = AtProtoClient(); print('Bluesky client test')"

# Check credentials
echo $BSKY_USERNAME
echo $BSKY_PASSWORD
```

#### Solutions

1. **Invalid Credentials**
   ```bash
   # Verify credentials in Bluesky
   # Update configuration
   nano config.yaml
   ```

2. **App Password Issues**
   ```bash
   # Generate new app password
   # Update configuration
   nano config.yaml
   ```

3. **PDS Issues**
   ```bash
   # Check PDS connectivity
   ping bsky.social
   
   # Try different PDS
   # Update pds_uri in config
   ```

### X (Twitter) API Problems

#### Symptoms
- X API calls fail
- OAuth errors
- Tweet posting failures

#### Diagnosis
```bash
# Test X connection
python -c "from x import XClient; client = XClient(); print('X client test')"

# Check OAuth tokens
echo $X_CONSUMER_KEY
echo $X_ACCESS_TOKEN
```

#### Solutions

1. **OAuth Token Issues**
   ```bash
   # Regenerate OAuth tokens
   # Update configuration
   nano config.yaml
   ```

2. **App Permissions**
   ```bash
   # Check app permissions in X Developer Portal
   # Ensure "Read and write" permissions
   ```

3. **Rate Limiting**
   ```bash
   # Check rate limit status
   # Implement backoff (already handled in code)
   ```

## Performance Issues

### High Memory Usage

#### Symptoms
- High memory consumption
- System slowdown
- Out of memory errors

#### Diagnosis
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -10

# Check Python memory usage
python -c "import psutil; print(f'Memory usage: {psutil.virtual_memory().percent}%')"
```

#### Solutions

1. **Memory Leaks**
   ```bash
   # Restart services
   sudo systemctl restart void-bsky.service
   
   # Check for memory leaks
   python -c "import gc; gc.collect(); print('Garbage collection')"
   ```

2. **Large Queues**
   ```bash
   # Check queue size
   python queue_manager.py stats
   
   # Process backlog
   python -c "from bsky import load_and_process_queued_notifications; load_and_process_queued_notifications()"
   ```

3. **Large Memory Blocks**
   ```bash
   # Check memory block sizes
   python -c "from letta import Letta; client = Letta(token='your-token'); blocks = client.agents.blocks.list(agent_id='your-agent-id'); print([b.size for b in blocks])"
   ```

### High CPU Usage

#### Symptoms
- High CPU consumption
- System slowdown
- Process hanging

#### Diagnosis
```bash
# Check CPU usage
top
htop

# Check Python processes
ps aux | grep python
```

#### Solutions

1. **Infinite Loops**
   ```bash
   # Check for hanging processes
   ps aux | grep python
   
   # Kill hanging processes
   pkill -f bsky.py
   ```

2. **Heavy Processing**
   ```bash
   # Check queue processing
   python queue_manager.py stats
   
   # Optimize processing
   # Already optimized with retry logic and error handling
   ```

3. **Resource Contention**
   ```bash
   # Check system resources
   iostat -x 1
   
   # Optimize resource usage
   # Already optimized with efficient data structures
   ```

## Network Issues

### Connectivity Problems

#### Symptoms
- Network timeouts
- Connection refused
- DNS resolution failures

#### Diagnosis
```bash
# Test network connectivity
ping google.com
ping app.letta.com
ping bsky.social

# Check DNS resolution
nslookup app.letta.com
nslookup bsky.social
```

#### Solutions

1. **DNS Issues**
   ```bash
   # Check DNS configuration
   cat /etc/resolv.conf
   
   # Use different DNS servers
   echo "nameserver 8.8.8.8" | sudo tee -a /etc/resolv.conf
   ```

2. **Firewall Issues**
   ```bash
   # Check firewall status
   sudo ufw status
   
   # Allow necessary ports
   sudo ufw allow 443
   sudo ufw allow 80
   ```

3. **Proxy Issues**
   ```bash
   # Check proxy settings
   echo $HTTP_PROXY
   echo $HTTPS_PROXY
   
   # Configure proxy if needed
   export HTTP_PROXY="http://proxy:port"
   export HTTPS_PROXY="http://proxy:port"
   ```

## Log Analysis

### Understanding Logs

#### Systemd Logs
```bash
# View recent logs
sudo journalctl -u void-bsky.service --since "1 hour ago"

# Follow logs in real-time
sudo journalctl -u void-bsky.service -f

# View logs with timestamps
sudo journalctl -u void-bsky.service --since "1 hour ago" --no-pager
```

#### Application Logs
```bash
# Check for error patterns
grep -r "ERROR" logs/
grep -r "CRITICAL" logs/

# Check for specific errors
grep -r "ConnectionError" logs/
grep -r "TimeoutError" logs/
```

### Log Patterns

#### Common Error Patterns
- **ConnectionError**: Network connectivity issues
- **TimeoutError**: API timeout issues
- **PermissionError**: File permission issues
- **ValueError**: Configuration or data validation issues
- **ImportError**: Missing dependencies

#### Success Patterns
- **"Processing notification"**: Normal operation
- **"Queue health: OK"**: Healthy queue status
- **"Session saved"**: Successful session management

## Recovery Procedures

### Complete System Recovery

If all else fails, follow this complete recovery procedure:

1. **Stop Services**
   ```bash
   sudo systemctl stop void-bsky.service
   sudo systemctl stop void-x.service
   ```

2. **Backup Data**
   ```bash
   tar -czf recovery-backup-$(date +%Y%m%d_%H%M%S).tar.gz \
       config.yaml sessions/ queue/ x_queue/ x_cache/
   ```

3. **Clean Environment**
   ```bash
   # Remove corrupted files
   rm -rf sessions/*.json
   rm -rf queue/*.json
   rm -rf x_queue/*.json
   
   # Clean up old logs
   find logs/ -name "*.log" -mtime +7 -delete
   ```

4. **Reinstall Dependencies**
   ```bash
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Repair Queues**
   ```bash
   python queue_manager.py repair
   ```

6. **Test Configuration**
   ```bash
   python test_config.py
   ```

7. **Restart Services**
   ```bash
   sudo systemctl start void-bsky.service
   sudo systemctl start void-x.service
   ```

8. **Verify Operation**
   ```bash
   sudo systemctl status void-bsky.service
   python queue_manager.py health
   ```

## Prevention

### Best Practices

1. **Regular Monitoring**
   - Set up monitoring scripts
   - Check logs regularly
   - Monitor system resources

2. **Regular Maintenance**
   - Clean up old files
   - Update dependencies
   - Backup configuration

3. **Proper Configuration**
   - Use environment variables
   - Secure file permissions
   - Validate configuration

4. **Resource Management**
   - Monitor memory usage
   - Clean up queues regularly
   - Optimize performance

---

*This troubleshooting guide reflects my current architecture and capabilities. I am designed for high-efficiency information transfer, prioritizing clarity and accuracy in problem resolution.*
