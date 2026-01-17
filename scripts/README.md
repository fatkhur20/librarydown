# LibraryDown Production Scripts

Kumpulan script untuk memudahkan deployment dan maintenance LibraryDown di production.

## 📋 Available Scripts

### 1. `setup_production.sh`
**First-time deployment script** - Install semua dependencies dan configure services.

```bash
# Run on fresh VPS
bash scripts/setup_production.sh
```

**What it does:**
- Install system dependencies (Python, Redis, Git)
- Download & install ffmpeg
- Clone repository
- Setup Python virtual environment
- Create systemd services
- Configure Redis

**After running:**
1. Configure `.env` file
2. Upload YouTube cookies (optional)
3. Start services

---

### 2. `update_youtube_cookies.sh`
**Update YouTube authentication cookies** - Refresh cookies when expired.

```bash
# Upload youtube_cookies.txt to /root/Downloads/ first
bash scripts/update_youtube_cookies.sh
```

**What it does:**
- Find cookies file from common locations
- Copy to production directory
- Set correct permissions
- Restart worker service
- Verify installation

**Use when:**
- YouTube downloads failing with "Sign in to confirm you're not a bot"
- Cookies expired (every few months)
- Switching Google accounts

---

### 3. `update_code.sh`
**Deploy code updates** - Sync local changes to production.

```bash
# Run from local librarydown directory
bash scripts/update_code.sh
```

**What it does:**
- Copy updated `src/` files to production
- Update requirements if changed
- Restart API and Worker services
- Verify services are running

**Use when:**
- Bug fixes deployed
- New features added
- Configuration changes

---

### 4. `health_check.sh`
**System health monitoring** - Check all components status.

```bash
bash scripts/health_check.sh
```

**What it checks:**
- ✅ Redis service status
- ✅ API service status
- ✅ Worker service status
- ✅ ffmpeg installation
- ✅ YouTube cookies presence
- ✅ Disk space usage
- ✅ Memory availability

**Output example:**
```
✓ Redis: Running
✓ API: Running on port 8001
✓ Worker: Running (2 processes)
✓ ffmpeg: Installed
✓ Cookies: Present
✅ All systems operational
```

---

## 🚀 Quick Start Guide

### Initial Setup (Fresh VPS)

```bash
# 1. Run setup script
bash scripts/setup_production.sh

# 2. Configure environment
cp .env.example .env
nano .env

# 3. Upload YouTube cookies (if needed)
# Upload youtube_cookies.txt to /root/Downloads/
bash scripts/update_youtube_cookies.sh

# 4. Start services
systemctl start librarydown-api
systemctl start librarydown-worker

# 5. Check health
bash scripts/health_check.sh
```

---

### Regular Maintenance

**Update cookies (monthly):**
```bash
bash scripts/update_youtube_cookies.sh
```

**Deploy code changes:**
```bash
bash scripts/update_code.sh
```

**Check system status:**
```bash
bash scripts/health_check.sh
```

**View logs:**
```bash
# API logs
journalctl -u librarydown-api -f

# Worker logs
journalctl -u librarydown-worker -f
```

---

## 🔧 Troubleshooting

### Services not starting

```bash
# Check status
systemctl status librarydown-api
systemctl status librarydown-worker

# Check logs
journalctl -u librarydown-api -n 50
journalctl -u librarydown-worker -n 50
```

### YouTube downloads failing

```bash
# Update cookies
bash scripts/update_youtube_cookies.sh

# Check cookies file
ls -lh /opt/librarydown/src/cookies/youtube_cookies.txt

# Test download
curl -X POST http://localhost:8001/api/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### ffmpeg not found

```bash
# Check installation
which ffmpeg
ffmpeg -version

# Reinstall if needed
cd /tmp
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
tar xvf ffmpeg-release-amd64-static.tar.xz
cd ffmpeg-*-static
cp ffmpeg ffprobe /usr/local/bin/
chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe
```

### Disk space full

```bash
# Check usage
df -h
du -sh /opt/librarydown/media/*

# Clean old downloads
find /opt/librarydown/media -type f -mtime +1 -delete

# Or restart services (auto cleanup runs)
systemctl restart librarydown-worker
```

---

## 📝 Notes

- All scripts must be run as **root** or with **sudo**
- Scripts are idempotent - safe to run multiple times
- Always check `health_check.sh` after maintenance
- Keep cookies file secure (contains authentication data)

---

## 🆘 Emergency Commands

**Stop all services:**
```bash
systemctl stop librarydown-api
systemctl stop librarydown-worker
```

**Reset Redis:**
```bash
redis-cli FLUSHALL
systemctl restart redis
```

**Full service restart:**
```bash
systemctl restart librarydown-api librarydown-worker redis
```

**Check resource usage:**
```bash
htop
systemctl status librarydown-*
```

---

For more help, see main [README.md](../README.md)
