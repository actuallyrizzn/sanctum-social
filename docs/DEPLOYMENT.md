# Sanctum Social Deployment Guide

This guide provides comprehensive instructions for deploying Sanctum Social in various environments, from development to production.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Deployment](#development-deployment)
- [Production Deployment](#production-deployment)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Scaling](#scaling)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Python**: 3.8 or higher
- **Memory**: Minimum 2GB RAM (4GB+ recommended for production)
- **Storage**: 10GB+ free space for logs, data, and cache
- **Network**: Stable internet connection for API access

### External Services

- **Letta Cloud**: Account and project setup
- **Social Media Accounts**: Bluesky, X (Twitter), Discord accounts
- **API Keys**: Platform-specific API credentials

### Required Accounts

1. **Letta Cloud** ([app.letta.com](https://app.letta.com))
   - Create account and project
   - Generate API key
   - Note project ID

2. **Bluesky** ([bsky.app](https://bsky.app))
   - Create account
   - Generate app password
   - Note handle

3. **X (Twitter)** ([developer.x.com](https://developer.x.com)) - Optional
   - Create developer account
   - Create app with "Read and write" permissions
   - Generate OAuth 1.0a tokens

4. **Discord** ([discord.com/developers](https://discord.com/developers)) - Optional
   - Create application
   - Generate bot token
   - Note guild ID

## Development Deployment

### Local Development Setup

#### 1. Clone Repository

```bash
git clone https://github.com/actuallyrizzn/sanctum-social.git
cd sanctum-social
```

#### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-test.txt
```

#### 4. Configure Environment

```bash
# Copy configuration template
cp config/agent.yaml config.yaml

# Edit configuration with your credentials
nano config.yaml
```

#### 5. Test Configuration

```bash
python scripts/test_config.py
```

#### 6. Register Tools

```bash
# Register platform-specific tools
python scripts/register_tools.py
python scripts/register_x_tools.py  # If using X
python scripts/register_discord_tools.py  # If using Discord
```

#### 7. Run Tests

```bash
python -m pytest tests/ -v
```

#### 8. Start Development Server

```bash
# Run on Bluesky
python platforms/bluesky/orchestrator.py --test

# Run on X (if configured)
python platforms/x/orchestrator.py --test

# Run on Discord (if configured)
python platforms/discord/orchestrator.py --test
```

### Development Environment Variables

Create a `.env` file for development:

```bash
# Letta Configuration
LETTA_API_KEY=your-letta-api-key
LETTA_PROJECT_ID=your-project-id
LETTA_AGENT_ID=your-agent-id

# Bluesky Configuration
BSKY_USERNAME=your-handle.bsky.social
BSKY_PASSWORD=your-app-password
PDS_URI=https://bsky.social

# X Configuration (Optional)
X_API_KEY=your-x-api-key
X_CONSUMER_KEY=your-consumer-key
X_CONSUMER_SECRET=your-consumer-secret
X_ACCESS_TOKEN=your-access-token
X_ACCESS_TOKEN_SECRET=your-access-token-secret
X_USER_ID=your-x-user-id

# Discord Configuration (Optional)
DISCORD_BOT_TOKEN=your-discord-bot-token
DISCORD_GUILD_ID=your-guild-id

# Logging
LOG_LEVEL=DEBUG
```

## Production Deployment

### System Preparation

#### 1. Create Dedicated User

```bash
sudo useradd -m -s /bin/bash sanctum
sudo usermod -aG sudo sanctum
```

#### 2. Install System Dependencies

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.9 python3.9-venv python3-pip git nginx supervisor

# CentOS/RHEL
sudo yum install python39 python39-pip git nginx supervisor
```

#### 3. Create Application Directory

```bash
sudo mkdir -p /opt/sanctum-social
sudo chown sanctum:sanctum /opt/sanctum-social
```

#### 4. Deploy Application

```bash
cd /opt/sanctum-social
sudo -u sanctum git clone https://github.com/actuallyrizzn/sanctum-social.git .
sudo -u sanctum python3.9 -m venv venv
sudo -u sanctum ./venv/bin/pip install -r requirements.txt
```

#### 5. Configure Application

```bash
sudo -u sanctum cp config/agent.yaml config.yaml
sudo -u sanctum nano config.yaml  # Edit with production credentials
```

#### 6. Set Up Logging

```bash
sudo mkdir -p /var/log/sanctum-social
sudo chown sanctum:sanctum /var/log/sanctum-social
```

### Process Management

#### Supervisor Configuration

Create `/etc/supervisor/conf.d/sanctum-social.conf`:

```ini
[program:sanctum-bluesky]
command=/opt/sanctum-social/venv/bin/python platforms/bluesky/orchestrator.py
directory=/opt/sanctum-social
user=sanctum
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/sanctum-social/bluesky.log
environment=PATH="/opt/sanctum-social/venv/bin"

[program:sanctum-x]
command=/opt/sanctum-social/venv/bin/python platforms/x/orchestrator.py
directory=/opt/sanctum-social
user=sanctum
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/sanctum-social/x.log
environment=PATH="/opt/sanctum-social/venv/bin"

[program:sanctum-discord]
command=/opt/sanctum-social/venv/bin/python platforms/discord/orchestrator.py
directory=/opt/sanctum-social
user=sanctum
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/sanctum-social/discord.log
environment=PATH="/opt/sanctum-social/venv/bin"
```

#### Start Services

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start sanctum-bluesky
sudo supervisorctl start sanctum-x
sudo supervisorctl start sanctum-discord
```

### Web Interface (Optional)

#### Nginx Configuration

Create `/etc/nginx/sites-available/sanctum-social`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/sanctum-social/static/;
    }
}
```

#### Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/sanctum-social /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Docker Deployment

### Docker Compose Setup

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  sanctum-bluesky:
    build: .
    container_name: sanctum-bluesky
    environment:
      - LETTA_API_KEY=${LETTA_API_KEY}
      - LETTA_PROJECT_ID=${LETTA_PROJECT_ID}
      - LETTA_AGENT_ID=${LETTA_AGENT_ID}
      - BSKY_USERNAME=${BSKY_USERNAME}
      - BSKY_PASSWORD=${BSKY_PASSWORD}
      - PDS_URI=${PDS_URI}
      - LOG_LEVEL=INFO
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    command: python platforms/bluesky/orchestrator.py

  sanctum-x:
    build: .
    container_name: sanctum-x
    environment:
      - LETTA_API_KEY=${LETTA_API_KEY}
      - LETTA_PROJECT_ID=${LETTA_PROJECT_ID}
      - LETTA_AGENT_ID=${LETTA_AGENT_ID}
      - X_API_KEY=${X_API_KEY}
      - X_CONSUMER_KEY=${X_CONSUMER_KEY}
      - X_CONSUMER_SECRET=${X_CONSUMER_SECRET}
      - X_ACCESS_TOKEN=${X_ACCESS_TOKEN}
      - X_ACCESS_TOKEN_SECRET=${X_ACCESS_TOKEN_SECRET}
      - X_USER_ID=${X_USER_ID}
      - LOG_LEVEL=INFO
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    command: python platforms/x/orchestrator.py

  sanctum-discord:
    build: .
    container_name: sanctum-discord
    environment:
      - LETTA_API_KEY=${LETTA_API_KEY}
      - LETTA_PROJECT_ID=${LETTA_PROJECT_ID}
      - LETTA_AGENT_ID=${LETTA_AGENT_ID}
      - DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
      - DISCORD_GUILD_ID=${DISCORD_GUILD_ID}
      - LOG_LEVEL=INFO
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    command: python platforms/discord/orchestrator.py

  nginx:
    image: nginx:alpine
    container_name: sanctum-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - sanctum-bluesky
      - sanctum-x
      - sanctum-discord
    restart: unless-stopped
```

### Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 sanctum && chown -R sanctum:sanctum /app
USER sanctum

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "platforms/bluesky/orchestrator.py"]
```

### Environment File

Create `.env`:

```bash
LETTA_API_KEY=your-letta-api-key
LETTA_PROJECT_ID=your-project-id
LETTA_AGENT_ID=your-agent-id
BSKY_USERNAME=your-handle.bsky.social
BSKY_PASSWORD=your-app-password
PDS_URI=https://bsky.social
X_API_KEY=your-x-api-key
X_CONSUMER_KEY=your-consumer-key
X_CONSUMER_SECRET=your-consumer-secret
X_ACCESS_TOKEN=your-access-token
X_ACCESS_TOKEN_SECRET=your-access-token-secret
X_USER_ID=your-x-user-id
DISCORD_BOT_TOKEN=your-discord-bot-token
DISCORD_GUILD_ID=your-guild-id
```

### Deploy with Docker

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Cloud Deployment

### AWS Deployment

#### EC2 Instance

1. **Launch EC2 Instance**
   - AMI: Ubuntu 20.04 LTS
   - Instance Type: t3.medium or larger
   - Security Group: Allow SSH (22), HTTP (80), HTTPS (443)

2. **Install Dependencies**

```bash
sudo apt update
sudo apt install python3.9 python3.9-venv python3-pip git nginx supervisor
```

3. **Deploy Application**

```bash
cd /opt
sudo git clone https://github.com/actuallyrizzn/sanctum-social.git
sudo chown -R ubuntu:ubuntu sanctum-social
cd sanctum-social
python3.9 -m venv venv
./venv/bin/pip install -r requirements.txt
```

4. **Configure Services**

```bash
# Copy configuration
cp config/agent.yaml config.yaml
nano config.yaml  # Edit with your credentials

# Set up supervisor
sudo cp deployment/supervisor.conf /etc/supervisor/conf.d/sanctum-social.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start sanctum-bluesky
```

#### AWS Lambda (Serverless)

Create `lambda_handler.py`:

```python
import json
import os
from platforms.bluesky.orchestrator import process_notifications

def lambda_handler(event, context):
    try:
        # Process notifications
        processed = process_notifications()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Processed {processed} notifications',
                'success': True
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': str(e),
                'success': False
            })
        }
```

### Google Cloud Platform

#### Compute Engine

1. **Create VM Instance**
   - Machine Type: e2-medium or larger
   - Boot Disk: Ubuntu 20.04 LTS
   - Firewall: Allow HTTP and HTTPS traffic

2. **Deploy Application**

```bash
# Install dependencies
sudo apt update
sudo apt install python3.9 python3.9-venv python3-pip git

# Clone and setup
git clone https://github.com/actuallyrizzn/sanctum-social.git
cd sanctum-social
python3.9 -m venv venv
./venv/bin/pip install -r requirements.txt
```

3. **Configure Services**

```bash
# Set up systemd service
sudo cp deployment/sanctum-social.service /etc/systemd/system/
sudo systemctl enable sanctum-social
sudo systemctl start sanctum-social
```

### Azure Deployment

#### App Service

1. **Create App Service**
   - Runtime: Python 3.9
   - Operating System: Linux
   - Pricing Tier: Basic or higher

2. **Deploy Application**

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login and deploy
az login
az webapp up --name sanctum-social --resource-group myResourceGroup
```

## Monitoring and Maintenance

### Health Checks

#### Application Health Check

Create `health_check.py`:

```python
#!/usr/bin/env python3
import requests
import sys
from core.config import get_config

def check_health():
    """Check application health."""
    try:
        config = get_config()
        
        # Check configuration
        if not config.get('letta.api_key'):
            return False, "Missing Letta API key"
        
        # Check platform configurations
        platforms = ['bluesky', 'x', 'discord']
        for platform in platforms:
            if config.is_platform_enabled(platform):
                platform_config = config.get_platform_config(platform)
                if not platform_config:
                    return False, f"Missing {platform} configuration"
        
        return True, "All checks passed"
        
    except Exception as e:
        return False, f"Health check failed: {str(e)}"

if __name__ == "__main__":
    healthy, message = check_health()
    if healthy:
        print("OK: " + message)
        sys.exit(0)
    else:
        print("ERROR: " + message)
        sys.exit(1)
```

#### System Health Check

Create `system_health.py`:

```python
#!/usr/bin/env python3
import psutil
import os
import sys

def check_system_health():
    """Check system health."""
    issues = []
    
    # Check disk space
    disk_usage = psutil.disk_usage('/')
    if disk_usage.percent > 90:
        issues.append(f"Disk usage high: {disk_usage.percent}%")
    
    # Check memory usage
    memory = psutil.virtual_memory()
    if memory.percent > 90:
        issues.append(f"Memory usage high: {memory.percent}%")
    
    # Check CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    if cpu_percent > 90:
        issues.append(f"CPU usage high: {cpu_percent}%")
    
    return issues

if __name__ == "__main__":
    issues = check_system_health()
    if issues:
        print("WARNING: " + "; ".join(issues))
        sys.exit(1)
    else:
        print("OK: System health good")
        sys.exit(0)
```

### Logging Configuration

#### Log Rotation

Create `/etc/logrotate.d/sanctum-social`:

```
/var/log/sanctum-social/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 sanctum sanctum
    postrotate
        supervisorctl restart sanctum-bluesky
        supervisorctl restart sanctum-x
        supervisorctl restart sanctum-discord
    endscript
}
```

#### Log Monitoring

```bash
# Monitor logs in real-time
tail -f /var/log/sanctum-social/bluesky.log

# Search for errors
grep -i error /var/log/sanctum-social/*.log

# Check log sizes
du -h /var/log/sanctum-social/
```

### Backup Strategy

#### Data Backup Script

Create `backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/opt/backups/sanctum-social"
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/opt/sanctum-social"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup configuration
cp $APP_DIR/config.yaml $BACKUP_DIR/config_$DATE.yaml

# Backup data directory
tar -czf $BACKUP_DIR/data_$DATE.tar.gz -C $APP_DIR data/

# Backup logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz -C /var/log sanctum-social/

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.yaml" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

#### Automated Backup

```bash
# Add to crontab
crontab -e

# Add this line for daily backups at 2 AM
0 2 * * * /opt/sanctum-social/scripts/backup.sh
```

## Scaling

### Horizontal Scaling

#### Load Balancer Configuration

Create `nginx-load-balancer.conf`:

```nginx
upstream sanctum_backend {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://sanctum_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Multiple Instances

```bash
# Start multiple instances on different ports
python platforms/bluesky/orchestrator.py --port 8001 &
python platforms/bluesky/orchestrator.py --port 8002 &
python platforms/bluesky/orchestrator.py --port 8003 &
```

### Vertical Scaling

#### Resource Monitoring

```bash
# Monitor resource usage
htop
iotop
nethogs

# Check specific process
ps aux | grep python
```

#### Performance Tuning

```python
# config.yaml optimizations
platforms:
  bluesky:
    max_concurrent_requests: 10
    request_timeout: 30
    retry_attempts: 3
  
  x:
    rate_limit_delay: 1.0
    max_tweets_per_hour: 100
  
  discord:
    message_rate_limit: 5
    max_messages_per_minute: 50
```

## Security Considerations

### Credential Management

#### Environment Variables

```bash
# Use environment variables for sensitive data
export LETTA_API_KEY="your-api-key"
export BSKY_PASSWORD="your-password"
```

#### Secret Management

```bash
# Use AWS Secrets Manager
aws secretsmanager create-secret \
    --name "sanctum-social/credentials" \
    --secret-string '{"letta_api_key":"your-key","bsky_password":"your-password"}'
```

### Network Security

#### Firewall Configuration

```bash
# UFW firewall rules
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

#### SSL/TLS Configuration

```bash
# Let's Encrypt SSL certificate
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Application Security

#### Input Validation

```python
# Validate user input
from pydantic import BaseModel, validator

class PostRequest(BaseModel):
    text: str
    
    @validator('text')
    def validate_text(cls, v):
        if len(v) > 300:
            raise ValueError('Text too long')
        return v
```

#### Rate Limiting

```python
# Implement rate limiting
from functools import wraps
import time

def rate_limit(calls_per_minute=60):
    def decorator(func):
        calls = []
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            calls[:] = [call for call in calls if now - call < 60]
            
            if len(calls) >= calls_per_minute:
                raise Exception("Rate limit exceeded")
            
            calls.append(now)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
```

## Troubleshooting

### Common Issues

#### Configuration Errors

```bash
# Test configuration
python scripts/test_config.py

# Check configuration syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

#### Platform Connection Issues

```bash
# Test Bluesky connection
python -c "from platforms.bluesky.utils import default_login; print(default_login())"

# Test X connection
python -c "from platforms.x.orchestrator import create_x_client; print(create_x_client())"

# Test Discord connection
python -c "from platforms.discord.orchestrator import create_discord_client; print(create_discord_client())"
```

#### Memory Issues

```bash
# Check memory usage
python scripts/memory_monitor.py

# Clean up old memory blocks
python scripts/memory_cleanup.py
```

#### Queue Issues

```bash
# Check queue health
python scripts/queue_manager.py health

# Repair queue
python scripts/queue_manager.py repair

# Get queue statistics
python scripts/queue_manager.py stats
```

### Debug Mode

#### Enable Debug Logging

```bash
# Set debug environment variable
export LOG_LEVEL=DEBUG

# Run with debug output
python platforms/bluesky/orchestrator.py --debug
```

#### Verbose Output

```bash
# Run with verbose output
python platforms/bluesky/orchestrator.py --verbose

# Check specific platform
python platforms/bluesky/orchestrator.py --test --verbose
```

### Performance Issues

#### Profiling

```bash
# Install profiling tools
pip install py-spy memory-profiler

# Profile CPU usage
py-spy top --pid $(pgrep -f "python.*orchestrator")

# Profile memory usage
python -m memory_profiler platforms/bluesky/orchestrator.py
```

#### Database Optimization

```bash
# Optimize SQLite databases
sqlite3 data/queues/bluesky/notifications.db "VACUUM;"
sqlite3 data/queues/x/notifications.db "VACUUM;"
```

---

## Support

For deployment issues and support:

- **Documentation**: Check the `docs/` directory
- **Issues**: Report issues on GitHub
- **Community**: Join discussions on GitHub Discussions
- **Contact**: Reach out to maintainers for support

This deployment guide provides comprehensive instructions for deploying Sanctum Social in various environments. Choose the deployment method that best fits your needs and infrastructure requirements.