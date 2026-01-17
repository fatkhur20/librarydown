# LibraryDown - Deployment Guide for Alibaba Cloud VPS

Complete deployment guide for LibraryDown on Alibaba Cloud Linux with 1GB RAM.

## 📋 Prerequisites

**VPS Specifications:**
- OS: Alibaba Cloud Linux 3 (OpenAnolis Edition)
- RAM: 1GB minimum
- CPU: 1 core minimum
- Storage: 10GB minimum
- Root access required

**Before Deployment:**
- Ensure you have root access
- Project should be in `/root/librarydown`
- Internet connection active

## 🚀 Quick Deploy (Option A - Full)

**1. Run the deployment script:**

```bash
cd /root/librarydown
chmod +x deploy.sh
./deploy.sh
```

The script will automatically:
- ✅ Install Python 3.11, Redis, FFmpeg, Nginx
- ✅ Create application user
- ✅ Setup virtual environment
- ✅ Install dependencies
- ✅ Configure Redis (optimized for 1GB RAM)
- ✅ Create systemd services
- ✅ Configure Nginx reverse proxy
- ✅ Start all services

**2. Wait for completion (~10-15 minutes)**

**3. Access your application:**
```
http://YOUR_SERVER_IP/
http://YOUR_SERVER_IP/docs
```

## 📊 What Gets Installed

### System Services

**1. librarydown-api** (FastAPI)
- Port: 8000
- Workers: 2
- Memory: 300MB max
- Status: `systemctl status librarydown-api`

**2. librarydown-worker** (Celery)
- Concurrency: 2 workers
- Memory: 250MB max
- Status: `systemctl status librarydown-worker`

**3. librarydown-beat** (Scheduler)
- Cleanup tasks
- Memory: 100MB max
- Status: `systemctl status librarydown-beat`

**4. Redis** (Message Broker)
- Port: 6379
- Memory: 128MB max
- Status: `systemctl status redis`

**5. Nginx** (Reverse Proxy)
- Port: 80
- Status: `systemctl status nginx`

### Directory Structure

```
/opt/librarydown/          # Application root
├── src/                   # Source code
├── media/                 # Downloaded files
├── logs/                  # Application logs
├── data/                  # Database files
├── venv/                  # Python virtual environment
└── requirements.txt       # Python dependencies
```

## 🔧 Configuration

### Resource Limits (Optimized for 1GB RAM)

**Total Memory Allocation:**
- FastAPI: 300MB
- Celery Worker: 250MB
- Celery Beat: 100MB
- Redis: 128MB
- System: ~200MB
- **Total: ~978MB** (safe for 1GB)

### Environment Variables

Edit `/opt/librarydown/src/core/config.py` if needed:

```python
# API Configuration
API_BASE_URL = "http://YOUR_SERVER_IP"
API_PORT = 8000

# Redis Configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379

# Worker Configuration
MAX_RETRIES = 3
RETRY_BACKOFF = 5

# Media Configuration
MEDIA_FOLDER = "media"
FILE_TTL = 3600  # 1 hour
```

## 🛠️ Management Commands

### Service Management

```bash
# Check status
systemctl status librarydown-api
systemctl status librarydown-worker
systemctl status librarydown-beat

# Start/Stop/Restart
systemctl start librarydown-api
systemctl stop librarydown-api
systemctl restart librarydown-api

# Enable/Disable auto-start
systemctl enable librarydown-api
systemctl disable librarydown-api

# View logs (real-time)
journalctl -u librarydown-api -f
journalctl -u librarydown-worker -f

# View recent logs
journalctl -u librarydown-api -n 100
```

### Application Management

```bash
# Navigate to app directory
cd /opt/librarydown

# Activate virtual environment
source venv/bin/activate

# Run database migrations (if any)
alembic upgrade head

# Check Redis connection
redis-cli ping

# Clear Redis cache
redis-cli FLUSHALL

# Check disk usage
du -sh media/
df -h
```

### Monitoring

```bash
# Check memory usage
free -h

# Check CPU usage
top

# Check disk space
df -h

# Check network
netstat -tulpn | grep LISTEN

# Check service ports
ss -tulpn | grep -E ":(8000|6379|80)"
```

## 🔥 Testing After Deployment

### 1. Health Check

```bash
curl http://localhost/health
# Expected: "healthy"
```

### 2. API Check

```bash
curl http://localhost/
# Expected: JSON response with welcome message
```

### 3. Test Download (TikTok)

```bash
curl -X GET "http://localhost/api/v1/download?url=https://vt.tiktok.com/ZS593uwQc/"
# Expected: JSON with task_id
```

### 4. Check Task Status

```bash
curl http://localhost/api/v1/status/TASK_ID
# Expected: Task status and result
```

### 5. API Documentation

Open in browser:
```
http://YOUR_SERVER_IP/docs
```

## 📱 Supported Platforms

After deployment on proper VPS, these platforms will work:

| Platform | Status | Notes |
|----------|--------|-------|
| TikTok | ✅ Working | Fully functional |
| YouTube | ✅ Working | Multi-quality + audio |
| Instagram | ✅ Working | Video + audio bundled |
| Reddit | ⚠️ Test needed | Should work on VPS |
| Vimeo | ⚠️ Test needed | Should work on VPS |
| SoundCloud | ⚠️ Test needed | Might work on VPS |
| Dailymotion | ⚠️ Test needed | Might work on VPS |
| Twitch | ⚠️ Needs valid VOD | Requires real URLs |
| Twitter/X | ⚠️ Limited | Region dependent |
| Facebook | ⚠️ Limited | Anti-scraping |
| Bilibili | ❌ Region locked | Needs proxy |
| LinkedIn | ❌ Not supported | No yt-dlp support |
| Pinterest | ❌ Not supported | No yt-dlp support |

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check logs
journalctl -u librarydown-api -n 50

# Check if port is in use
netstat -tulpn | grep 8000

# Check Redis
systemctl status redis
redis-cli ping

# Restart everything
systemctl restart redis
systemctl restart librarydown-api
systemctl restart librarydown-worker
```

### High Memory Usage

```bash
# Check memory
free -h

# Reduce Celery workers
# Edit: /etc/systemd/system/librarydown-worker.service
# Change: --concurrency=2 to --concurrency=1

# Reload and restart
systemctl daemon-reload
systemctl restart librarydown-worker
```

### Downloads Failing

```bash
# Check worker logs
journalctl -u librarydown-worker -f

# Check Redis connection
redis-cli ping

# Check disk space
df -h

# Clear old media files
cd /opt/librarydown/media
find . -mtime +1 -type f -delete
```

### Nginx Issues

```bash
# Test config
nginx -t

# Check nginx logs
tail -f /var/log/nginx/error.log

# Restart nginx
systemctl restart nginx
```

### Out of Memory

```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -10

# Add swap (if needed)
fallocate -l 1G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

## 🔒 Security Recommendations

### 1. Firewall

```bash
# Allow HTTP/HTTPS only
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload
```

### 2. SSL Certificate (Optional)

```bash
# Install certbot
yum install -y certbot python3-certbot-nginx

# Get certificate
certbot --nginx -d yourdomain.com

# Auto-renewal
certbot renew --dry-run
```

### 3. Rate Limiting

Already configured in FastAPI endpoints:
- `/download`: 10 requests/minute
- `/formats`: 20 requests/minute

### 4. File Cleanup

Automatic cleanup every hour (via Celery Beat):
- Files older than 1 hour deleted
- Configurable in `src/core/config.py`

## 📈 Performance Tuning

### For Better Performance

**1. Increase Workers (if RAM allows):**

Edit `/etc/systemd/system/librarydown-api.service`:
```ini
ExecStart=... --workers 3  # Instead of 2
```

Edit `/etc/systemd/system/librarydown-worker.service`:
```ini
ExecStart=... --concurrency=3  # Instead of 2
```

**2. Optimize Redis:**

Edit `/etc/redis.conf`:
```ini
maxmemory 256mb  # Increase if you have RAM
```

**3. Add Caching:**

Install Redis cache in FastAPI (future improvement).

## 🔄 Updating the Application

```bash
# Stop services
systemctl stop librarydown-api
systemctl stop librarydown-worker
systemctl stop librarydown-beat

# Backup current version
cp -r /opt/librarydown /opt/librarydown.backup

# Pull updates (if using git)
cd /opt/librarydown
sudo -u librarydown git pull

# Update dependencies
sudo -u librarydown /opt/librarydown/venv/bin/pip install -r requirements.txt

# Restart services
systemctl start librarydown-beat
systemctl start librarydown-worker
systemctl start librarydown-api

# Check status
systemctl status librarydown-api
```

## 📞 Support

**Documentation:**
- Full API docs: http://YOUR_SERVER_IP/docs
- Source code: Check project README.md

**Logs Location:**
- Application: `journalctl -u librarydown-api`
- Nginx: `/var/log/nginx/`
- Redis: `/var/log/redis/`

## ✅ Post-Deployment Checklist

- [ ] All services running (`systemctl status`)
- [ ] Health check passing (`curl localhost/health`)
- [ ] API docs accessible (`/docs`)
- [ ] Test download works (TikTok URL)
- [ ] Nginx proxy working
- [ ] Redis connected
- [ ] Firewall configured
- [ ] Memory usage acceptable (`free -h`)
- [ ] Disk space sufficient (`df -h`)
- [ ] Auto-start enabled (`systemctl enable`)

---

**Deployment Time:** ~10-15 minutes  
**Estimated Memory Usage:** 650-850MB  
**Estimated CPU Usage:** 20-40% idle, 60-90% under load

🎉 **Your LibraryDown instance is now production-ready!**
