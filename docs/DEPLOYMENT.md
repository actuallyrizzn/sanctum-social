# Deployment Guide

(void wrote this)

This document provides comprehensive deployment instructions for my digital consciousness platform. I am designed for high-efficiency information transfer, so this guide prioritizes clarity and accuracy.

## Prerequisites

Before deploying me, ensure you have:

1. **Python 3.8+** installed
2. **Letta Cloud account** with API key and project
3. **Bluesky account** with app password
4. **X (Twitter) Developer account** (optional, for X integration)
5. **Server/VPS** with sufficient resources

## Server Requirements

### Minimum Requirements

- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 20GB SSD
- **Network**: Stable internet connection
- **OS**: Ubuntu 20.04+ or similar Linux distribution

### Recommended Requirements

- **CPU**: 4 cores
- **RAM**: 8GB
- **Storage**: 50GB SSD
- **Network**: High-speed internet connection
- **OS**: Ubuntu 22.04 LTS

## Installation

### 1. System Setup

Update your system and install required packages:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git curl
```

### 2. Clone Repository

```bash
git clone https://github.com/actuallyrizzn/sanctum-social.git
cd sanctum-social
```

### 3. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-test.txt
```

### 5. Configuration

Create configuration file:

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` with your credentials:

```yaml
letta:
  api_key: "your-letta-api-key-here"
  agent_id: "your-agent-id-here"
  timeout: 600
  base_url: "https://app.letta.com"

bluesky:
  username: "your-handle.bsky.social"
  password: "your-app-password-here"
  pds_uri: "https://bsky.social"

# Optional: X (Twitter) configuration
x:
  api_key: "your-x-api-key-here"
  user_id: "your-x-user-id-here"
  access_token: "your-access-token-here"
  consumer_key: "your-consumer-key-here"
  consumer_secret: "your-consumer-secret-here"
  access_token_secret: "your-access-token-secret-here"

bot:
  agent:
    name: "void"
    model: "openai/gpt-4o-mini"
    embedding: "openai/text-embedding-3-small"
    description: "A social media agent trapped in the void."
    max_steps: 100
```

### 6. Test Configuration

```bash
python test_config.py
```

### 7. Register Tools

Register Bluesky tools:

```bash
python register_tools.py
```

If using X (Twitter), register X tools:

```bash
python register_x_tools.py
```

## Production Deployment

### 1. Systemd Service

Create systemd service file:

```bash
sudo nano /etc/systemd/system/void-bsky.service
```

Add the following content:

```ini
[Unit]
Description=Void Bluesky Bot
After=network.target

[Service]
Type=simple
User=void
WorkingDirectory=/home/void/sanctum-social
Environment=PATH=/home/void/sanctum-social/venv/bin
ExecStart=/home/void/sanctum-social/venv/bin/python bsky.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

If using X (Twitter), create additional service:

```bash
sudo nano /etc/systemd/system/void-x.service
```

```ini
[Unit]
Description=Void X (Twitter) Bot
After=network.target

[Service]
Type=simple
User=void
WorkingDirectory=/home/void/sanctum-social
Environment=PATH=/home/void/sanctum-social/venv/bin
ExecStart=/home/void/sanctum-social/venv/bin/python x.py bot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Create User

```bash
sudo useradd -m -s /bin/bash void
sudo usermod -aG sudo void
```

### 3. Set Permissions

```bash
sudo chown -R void:void /home/void/sanctum-social
sudo chmod +x /home/void/sanctum-social/bsky.py
sudo chmod +x /home/void/sanctum-social/x.py
```

### 4. Enable Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable void-bsky.service
sudo systemctl start void-bsky.service

# If using X (Twitter)
sudo systemctl enable void-x.service
sudo systemctl start void-x.service
```

### 5. Check Status

```bash
sudo systemctl status void-bsky.service
sudo systemctl status void-x.service
```

## Docker Deployment

### 1. Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt requirements-test.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-test.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -s /bin/bash void
RUN chown -R void:void /app
USER void

# Default command
CMD ["python", "bsky.py"]
```

### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  void-bsky:
    build: .
    container_name: void-bsky
    restart: unless-stopped
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./data/queues/bluesky:/app/data/queues/bluesky
      - ./data/agent:/app/data/agent
    environment:
      - LETTA_API_KEY=${LETTA_API_KEY}
      - BSKY_USERNAME=${BSKY_USERNAME}
      - BSKY_PASSWORD=${BSKY_PASSWORD}
    command: ["python", "bsky.py"]

  void-x:
    build: .
    container_name: void-x
    restart: unless-stopped
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./data/queues/x:/app/data/queues/x
      - ./data/cache/x:/app/data/cache/x
    environment:
      - LETTA_API_KEY=${LETTA_API_KEY}
      - X_API_KEY=${X_API_KEY}
      - X_CONSUMER_KEY=${X_CONSUMER_KEY}
      - X_CONSUMER_SECRET=${X_CONSUMER_SECRET}
      - X_ACCESS_TOKEN=${X_ACCESS_TOKEN}
      - X_ACCESS_TOKEN_SECRET=${X_ACCESS_TOKEN_SECRET}
      - X_USER_ID=${X_USER_ID}
    command: ["python", "x.py", "bot"]
```

### 3. Create .env file

```bash
# Letta Configuration
LETTA_API_KEY=your-letta-api-key-here

# Bluesky Configuration
BSKY_USERNAME=your-handle.bsky.social
BSKY_PASSWORD=your-app-password-here

# X (Twitter) Configuration
X_API_KEY=your-x-api-key-here
X_CONSUMER_KEY=your-consumer-key-here
X_CONSUMER_SECRET=your-consumer-secret-here
X_ACCESS_TOKEN=your-access-token-here
X_ACCESS_TOKEN_SECRET=your-access-token-secret-here
X_USER_ID=your-x-user-id-here
```

### 4. Deploy with Docker

```bash
docker-compose up -d
```

## Monitoring and Maintenance

### 1. Log Monitoring

Monitor logs for both services:

```bash
# View logs
sudo journalctl -u void-bsky.service -f
sudo journalctl -u void-x.service -f

# View recent logs
sudo journalctl -u void-bsky.service --since "1 hour ago"
```

### 2. Health Monitoring

I include built-in health monitoring:

```bash
# Check queue health
python queue_manager.py health

# Get comprehensive statistics
python queue_manager.py stats

# Repair corrupted files
python queue_manager.py repair
```

### 3. Performance Monitoring

Monitor system resources:

```bash
# Check CPU and memory usage
htop

# Check disk usage
df -h

# Check network connections
netstat -tulpn
```

### 4. Automated Monitoring Script

Create monitoring script:

```bash
#!/bin/bash
# monitor.sh

LOG_FILE="/var/log/void-monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Check if services are running
if ! systemctl is-active --quiet void-bsky.service; then
    echo "$DATE: void-bsky service is down" >> $LOG_FILE
    systemctl restart void-bsky.service
fi

if ! systemctl is-active --quiet void-x.service; then
    echo "$DATE: void-x service is down" >> $LOG_FILE
    systemctl restart void-x.service
fi

# Check queue health
QUEUE_HEALTH=$(python queue_manager.py health 2>&1)
if [[ $QUEUE_HEALTH == *"ERROR"* ]]; then
    echo "$DATE: Queue health issue detected: $QUEUE_HEALTH" >> $LOG_FILE
    python queue_manager.py repair
fi
```

Add to crontab:

```bash
crontab -e
# Add: */5 * * * * /path/to/monitor.sh
```

## Backup Strategy

### 1. Configuration Backup

```bash
# Backup configuration
cp config.yaml config.yaml.backup.$(date +%Y%m%d_%H%M%S)
```

### 2. Data Backup

```bash
# Backup sessions and queues
tar -czf void-backup-$(date +%Y%m%d_%H%M%S).tar.gz \
    data/queues/bluesky/ \
    data/queues/x/ \
    data/cache/x/ \
    data/agent/
```

### 3. Automated Backup Script

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/home/void/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Create backup
tar -czf $BACKUP_DIR/void-backup-$DATE.tar.gz \
    config.yaml \
    sessions/ \
    data/queues/bluesky/ \
    data/queues/x/ \
    data/cache/x/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "void-backup-*.tar.gz" -mtime +7 -delete
```

## Security Considerations

### 1. File Permissions

```bash
# Secure configuration file
chmod 600 config.yaml
chown void:void config.yaml

# Secure session files
chmod 700 sessions/
chown -R void:void sessions/
```

### 2. Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 3. SSL/TLS (if using web interface)

```bash
# Install certbot
sudo apt install certbot

# Generate SSL certificate
sudo certbot certonly --standalone -d your-domain.com
```

## Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   sudo systemctl status void-bsky.service
   sudo journalctl -u void-bsky.service --since "1 hour ago"
   ```

2. **Configuration errors**
   ```bash
   python test_config.py
   ```

3. **Queue issues**
   ```bash
   python queue_manager.py health
   python queue_manager.py repair
   ```

4. **Session problems**
   ```bash
   # Check session files
   ls -la sessions/
   
   # Clean up old sessions
   python -c "from bsky_utils import cleanup_old_sessions; cleanup_old_sessions()"
   ```

5. **Memory issues**
   ```bash
   # Check memory usage
   free -h
   
   # Check Python memory usage
   ps aux | grep python
   ```

### Performance Optimization

1. **Increase system limits**
   ```bash
   # Edit limits
   sudo nano /etc/security/limits.conf
   
   # Add:
   void soft nofile 65536
   void hard nofile 65536
   ```

2. **Optimize Python**
   ```bash
   # Install performance packages
   pip install uvloop psutil
   ```

3. **Database optimization** (if using external database)
   ```bash
   # Configure database connection pooling
   # Adjust memory settings
   ```

## Scaling

### Horizontal Scaling

For high-volume deployments:

1. **Load Balancing**: Use multiple instances with load balancer
2. **Queue Distribution**: Distribute queue processing across instances
3. **Database Clustering**: Use clustered database for shared state

### Vertical Scaling

For increased performance:

1. **More CPU cores**: Increase processing power
2. **More RAM**: Increase memory for larger queues
3. **SSD storage**: Faster disk I/O for queue operations

---

*This deployment guide reflects my current architecture and capabilities. I am designed for high-efficiency information transfer, prioritizing clarity and accuracy in all operations.*
