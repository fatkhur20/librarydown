# 🚀 LibraryDown - Quick Start Guide

Panduan cepat deployment **LibraryDown API Downloader** di VPS Alibaba Cloud secara standalone (terpisah dari API lain).

---

## 📋 Apa yang Akan Di-Deploy?

LibraryDown adalah **multi-platform video/audio downloader API** yang mendukung 13 platform:

✅ **Working:** TikTok, YouTube, Instagram, SoundCloud, Dailymotion, Twitch  
⚠️ **Limited:** Reddit, Vimeo, Twitter/X, Facebook  
❌ **Restricted:** Bilibili, LinkedIn, Pinterest

---

## ⚡ Quick Deploy (3 Steps)

### Step 1: Persiapan

Pastikan Anda sudah login ke VPS sebagai root:

```bash
ssh root@YOUR_VPS_IP
```

Pastikan project ada di `/root/librarydown`:

```bash
cd /root/librarydown
ls -la
```

Jika belum ada, clone dulu:

```bash
cd /root
git clone <repository-url> librarydown
cd librarydown
```

---

### Step 2: Jalankan Deploy Script

```bash
chmod +x deploy.sh
./deploy.sh
```

**Script akan otomatis install:**
- Python 3.11
- Redis (message broker)
- FFmpeg (untuk processing media)
- Nginx (reverse proxy)
- Semua dependencies Python
- Setup systemd services
- Konfigurasi firewall

**Estimasi waktu:** 10-15 menit

---

### Step 3: Verifikasi

Tunggu hingga script selesai, lalu cek status:

```bash
# Cek semua services
systemctl status librarydown-api
systemctl status librarydown-worker
systemctl status librarydown-beat
systemctl status redis
systemctl status nginx

# Test API
curl http://localhost/
curl http://localhost/platforms
```

Jika semua `active (running)` dan API response JSON, berarti berhasil! 🎉

---

## 🌐 Akses API

### Dari Browser:

- **API Docs:** `http://YOUR_VPS_IP/docs`
- **Health Check:** `http://YOUR_VPS_IP/health`
- **Platform List:** `http://YOUR_VPS_IP/platforms`

### Test Download:

```bash
# Download TikTok video
curl "http://YOUR_VPS_IP/download?url=https://vt.tiktok.com/ZS593uwQc/"

# Response:
{
  "task_id": "abc123...",
  "status": "processing",
  "message": "Download started"
}

# Check status
curl "http://YOUR_VPS_IP/status/abc123..."
```

---

## 📡 Endpoint Utama

### 1. GET `/platforms`
List semua platform yang didukung.

**Example:**
```bash
curl http://YOUR_VPS_IP/platforms
```

---

### 2. GET `/download`
Download video/audio dari URL.

**Parameters:**
- `url` (required): URL video
- `quality` (optional): Quality pilihan (lihat dari `/formats`)
- `format` (optional): `video` atau `audio`

**Example:**
```bash
curl "http://YOUR_VPS_IP/download?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

**Response:**
```json
{
  "task_id": "abc123",
  "status": "processing",
  "message": "Download started"
}
```

---

### 3. GET `/status/{task_id}`
Cek status download task.

**Example:**
```bash
curl http://YOUR_VPS_IP/status/abc123
```

**Response (Processing):**
```json
{
  "task_id": "abc123",
  "status": "processing",
  "progress": 45
}
```

**Response (Success):**
```json
{
  "task_id": "abc123",
  "status": "completed",
  "result": {
    "title": "Video Title",
    "download_url": "http://YOUR_VPS_IP/media/abc123.mp4",
    "thumbnail": "http://...",
    "duration": "3:45",
    "filesize": 12345678
  }
}
```

---

### 4. GET `/formats`
Preview available formats sebelum download.

**Parameters:**
- `url` (required): URL video

**Example:**
```bash
curl "http://YOUR_VPS_IP/formats?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

**Response:**
```json
{
  "platform": "youtube",
  "title": "Rick Astley - Never Gonna Give You Up",
  "thumbnail": "https://...",
  "duration": "3:32",
  "formats": [
    {
      "format_id": "1080p",
      "quality": "1080p",
      "ext": "mp4",
      "filesize_mb": 45.2
    },
    {
      "format_id": "720p",
      "quality": "720p",
      "ext": "mp4",
      "filesize_mb": 28.5
    },
    {
      "format_id": "audio",
      "quality": "audio only",
      "ext": "m4a",
      "filesize_mb": 3.2
    }
  ]
}
```

---

## 🛠️ Management Commands

### Cek Status Services

```bash
# Check all services
systemctl status librarydown-api
systemctl status librarydown-worker
systemctl status librarydown-beat

# Check Redis
redis-cli ping
# Expected: PONG

# Check disk space
df -h
du -sh /opt/librarydown/media/

# Check memory
free -h
```

---

### View Logs

```bash
# API logs (real-time)
journalctl -u librarydown-api -f

# Worker logs (real-time)
journalctl -u librarydown-worker -f

# Recent logs (last 100 lines)
journalctl -u librarydown-api -n 100

# Nginx error logs
tail -f /var/log/nginx/error.log
```

---

### Restart Services

```bash
# Restart individual service
systemctl restart librarydown-api
systemctl restart librarydown-worker

# Restart all
systemctl restart librarydown-api librarydown-worker librarydown-beat

# Restart Nginx
systemctl restart nginx
```

---

### Cleanup Old Files

```bash
# Manual cleanup (files older than 1 hour)
find /opt/librarydown/media/ -mmin +60 -type f -delete

# Check cleanup schedule (via Celery Beat)
journalctl -u librarydown-beat -n 50
```

---

## 🔒 Security & Firewall

Firewall sudah dikonfigurasi otomatis oleh script:

```bash
# Check firewall status
firewall-cmd --list-all

# Should show:
#   services: http https
```

Jika ingin custom:

```bash
# Allow specific port
firewall-cmd --permanent --add-port=8000/tcp
firewall-cmd --reload
```

---

## 🚨 Troubleshooting

### ❌ Service Failed to Start

**Cek logs:**
```bash
journalctl -u librarydown-api -n 50
```

**Common issues:**
- **Port conflict:** Cek apakah port 8000 sudah dipakai
  ```bash
  netstat -tulpn | grep 8000
  ```
- **Redis not running:** Start Redis dulu
  ```bash
  systemctl start redis
  ```
- **Permission issue:** Cek ownership
  ```bash
  ls -la /opt/librarydown
  chown -R librarydown:librarydown /opt/librarydown
  ```

---

### ❌ Out of Memory

**Check memory:**
```bash
free -h
```

**Solution 1: Add swap**
```bash
fallocate -l 1G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

**Solution 2: Reduce workers**
Edit `/etc/systemd/system/librarydown-api.service`:
```ini
ExecStart=... --workers 1  # Change from 2 to 1
```

Edit `/etc/systemd/system/librarydown-worker.service`:
```ini
ExecStart=... --concurrency=1  # Change from 2 to 1
```

Restart:
```bash
systemctl daemon-reload
systemctl restart librarydown-api librarydown-worker
```

---

### ❌ Download Failing

**Check worker logs:**
```bash
journalctl -u librarydown-worker -f
```

**Common causes:**
- Platform blocking (region lock)
- URL invalid/expired
- FFmpeg not installed
- Disk full

**Test manually:**
```bash
cd /opt/librarydown
source venv/bin/activate
yt-dlp "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

---

## 📈 Performance Tuning

### For VPS dengan RAM > 1GB:

**1. Increase workers:**

Edit `/etc/systemd/system/librarydown-api.service`:
```ini
ExecStart=... --workers 4  # Increase workers
```

Edit `/etc/systemd/system/librarydown-worker.service`:
```ini
ExecStart=... --concurrency=4  # Increase concurrency
```

**2. Increase Redis memory:**

Edit `/etc/redis.conf`:
```ini
maxmemory 256mb  # Increase from 128mb
```

**3. Remove resource limits:**

Comment out `MemoryLimit` di semua service files:
```ini
# MemoryLimit=300M
```

Reload dan restart:
```bash
systemctl daemon-reload
systemctl restart librarydown-api librarydown-worker
```

---

## 🔄 Update Application

```bash
# Stop services
systemctl stop librarydown-api librarydown-worker librarydown-beat

# Backup
cp -r /opt/librarydown /opt/librarydown.backup

# Pull updates
cd /opt/librarydown
sudo -u librarydown git pull

# Update dependencies
sudo -u librarydown /opt/librarydown/venv/bin/pip install -r requirements.txt --upgrade

# Restart
systemctl start librarydown-beat
systemctl start librarydown-worker
systemctl start librarydown-api
```

---

## 💡 Tips

### Rate Limiting

API sudah memiliki rate limiting bawaan:
- `/download`: 10 req/minute per IP
- `/formats`: 20 req/minute per IP
- `/status`: Unlimited

### File Auto-Cleanup

File di `media/` otomatis dihapus setelah 1 jam (konfigurasi via Celery Beat).

Check di `.env`:
```bash
FILE_TTL=3600  # 1 hour
```

### Custom Domain

Jika punya domain (e.g., `api.yourdomain.com`):

1. **Point DNS A Record** ke IP VPS
2. **Edit Nginx config** `/etc/nginx/conf.d/librarydown.conf`:
   ```nginx
   server_name api.yourdomain.com;  # Change from _
   ```
3. **Install SSL:**
   ```bash
   yum install -y certbot python3-certbot-nginx
   certbot --nginx -d api.yourdomain.com
   ```

---

## 📞 Get Help

**Cek dokumentasi lengkap:**
- Full deployment guide: `/root/librarydown/docs/DEPLOYMENT.md`
- API documentation: `http://YOUR_VPS_IP/docs`

**Check logs:**
```bash
journalctl -u librarydown-api -f
journalctl -u librarydown-worker -f
```

**Test connectivity:**
```bash
curl http://localhost/health
curl http://localhost/platforms
```

---

## ✅ Post-Deployment Checklist

- [ ] All services running: `systemctl status librarydown-*`
- [ ] Redis working: `redis-cli ping`
- [ ] API responding: `curl http://localhost/`
- [ ] Docs accessible: `http://YOUR_VPS_IP/docs`
- [ ] Test download works
- [ ] Firewall configured
- [ ] Memory acceptable: `free -h`
- [ ] Disk space ok: `df -h`

---

**🎉 LibraryDown siap digunakan!**

Akses documentation lengkap di: `http://YOUR_VPS_IP/docs`
