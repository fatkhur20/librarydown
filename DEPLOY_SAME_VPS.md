# 🚀 Deploy LibraryDown di VPS yang Sama dengan API Checker

Panduan untuk deploy **LibraryDown** di VPS yang sudah menjalankan **API Checker**, menggunakan Nginx routing untuk memisahkan kedua API.

---

## 🎯 Arsitektur

```
VPS (1GB RAM)
├── Port 80 (Nginx) → Routing:
│   ├── /api/checker/       → API Checker (port 8000)
│   ├── /api/downloader/    → LibraryDown (port 8001)
│   ├── /docs/checker       → API Checker Docs
│   └── /docs/downloader    → LibraryDown Docs
├── Port 8000: API Checker (sudah jalan)
├── Port 8001: LibraryDown (akan di-deploy)
└── Port 6379: Redis (shared)
```

**Akses setelah deployment:**
- API Checker: `http://YOUR_VPS_IP/api/checker/`
- LibraryDown: `http://YOUR_VPS_IP/api/downloader/`
- Docs Checker: `http://YOUR_VPS_IP/docs/checker`
- Docs Downloader: `http://YOUR_VPS_IP/docs/downloader`

---

## 📋 Prerequisites

✅ API Checker sudah running di port 8000  
✅ Nginx sudah terinstall  
✅ Redis sudah terinstall (jika belum, script akan install)  
✅ Root access ke VPS

---

## 🚀 Deployment Steps

### Step 1: Upload Project ke VPS

```bash
# Login ke VPS
ssh root@YOUR_VPS_IP

# Pastikan project ada di /root/librarydown
cd /root/librarydown
ls -la

# Jika belum ada, upload atau git clone
```

---

### Step 2: Jalankan Deploy Script

```bash
cd /root/librarydown
chmod +x deploy.sh
./deploy.sh
```

**Script akan:**
- ✅ Install dependencies (Python 3.11, FFmpeg, dll)
- ✅ Setup virtual environment
- ✅ Install Python packages
- ✅ Configure Redis (jika belum)
- ✅ Create systemd services di port 8001
- ✅ **SKIP Nginx config** (kita configure manual)
- ✅ Start semua services

**Tunggu 10-15 menit hingga selesai.**

---

### Step 3: Verifikasi LibraryDown Running

```bash
# Cek status services
systemctl status librarydown-api
systemctl status librarydown-worker
systemctl status librarydown-beat

# Semua harus 'active (running)'

# Test API di port 8001
curl http://localhost:8001/
curl http://localhost:8001/platforms

# Harus return JSON response
```

---

### Step 4: Configure Nginx Routing

Sekarang kita akan setup Nginx untuk routing kedua API.

**Backup config Nginx yang ada:**

```bash
cp /etc/nginx/conf.d/apichecker.conf /etc/nginx/conf.d/apichecker.conf.backup
```

**Buat config baru untuk dual API:**

```bash
cat > /etc/nginx/conf.d/dual-api.conf <<'EOF'
# Dual API Configuration - API Checker + LibraryDown

# API Checker backend (port 8000)
upstream apichecker_backend {
    server 127.0.0.1:8000;
}

# LibraryDown backend (port 8001)
upstream librarydown_backend {
    server 127.0.0.1:8001;
}

server {
    listen 80;
    server_name _;
    
    client_max_body_size 100M;
    
    # ===== API CHECKER ROUTES =====
    location /api/checker/ {
        rewrite ^/api/checker/(.*)\$ /\$1 break;
        proxy_pass http://apichecker_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /docs/checker {
        rewrite ^/docs/checker(.*)\$ /docs\$1 break;
        proxy_pass http://apichecker_backend;
        proxy_set_header Host \$host;
    }
    
    # ===== LIBRARYDOWN ROUTES =====
    location /api/downloader/ {
        rewrite ^/api/downloader/(.*)\$ /\$1 break;
        proxy_pass http://librarydown_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Long timeout for downloads
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    location /docs/downloader {
        rewrite ^/docs/downloader(.*)\$ /docs\$1 break;
        proxy_pass http://librarydown_backend;
        proxy_set_header Host \$host;
    }
    
    # LibraryDown media files
    location /media/ {
        alias /opt/librarydown/media/;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }
    
    # ===== ROOT & HEALTH =====
    location = / {
        return 200 '{"message": "Dual API Server", "apis": {"checker": "/api/checker/", "downloader": "/api/downloader/"}, "docs": {"checker": "/docs/checker", "downloader": "/docs/downloader"}}';
        add_header Content-Type application/json;
    }
    
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF
```

**Hapus config lama (jika ada conflict):**

```bash
# Cek config apa saja yang ada
ls -la /etc/nginx/conf.d/

# Backup dan hapus config lama
mv /etc/nginx/conf.d/apichecker.conf /etc/nginx/conf.d/apichecker.conf.disabled
mv /etc/nginx/conf.d/librarydown.conf /etc/nginx/conf.d/librarydown.conf.disabled 2>/dev/null || true
```

**Test dan reload Nginx:**

```bash
# Test config
nginx -t

# Jika OK, reload
systemctl reload nginx
```

---

## ✅ Verification & Testing

### 1. Cek Semua Services Running

```bash
systemctl status apichecker
systemctl status librarydown-api
systemctl status librarydown-worker
systemctl status nginx
```

Semua harus `active (running)`.

---

### 2. Test Routing

```bash
# Test root
curl http://localhost/
# Expected: JSON dengan info kedua API

# Test API Checker
curl http://localhost/api/checker/stats
# Expected: JSON stats dari API Checker

# Test LibraryDown
curl http://localhost/api/downloader/platforms
# Expected: JSON list platform

# Test health
curl http://localhost/health
# Expected: "healthy"
```

---

### 3. Test dari Browser

Buka browser dan akses:

✅ **Root:** `http://YOUR_VPS_IP/`  
✅ **API Checker Stats:** `http://YOUR_VPS_IP/api/checker/stats`  
✅ **LibraryDown Platforms:** `http://YOUR_VPS_IP/api/downloader/platforms`  
✅ **Docs Checker:** `http://YOUR_VPS_IP/docs/checker`  
✅ **Docs Downloader:** `http://YOUR_VPS_IP/docs/downloader`

---

### 4. Test Download

```bash
# Test download via LibraryDown
curl "http://YOUR_VPS_IP/api/downloader/download?url=https://vt.tiktok.com/ZS593uwQc/"

# Expected response:
# {
#   "task_id": "abc123...",
#   "status": "processing"
# }

# Check status
curl "http://YOUR_VPS_IP/api/downloader/status/abc123..."
```

---

## 📊 Memory & Resource Check

```bash
# Check memory usage
free -h

# Check per-service memory
systemctl status apichecker | grep Memory
systemctl status librarydown-api | grep Memory
systemctl status librarydown-worker | grep Memory

# Check CPU
top
```

**Expected memory usage:**
- API Checker: ~200MB
- LibraryDown API: ~300MB
- LibraryDown Worker: ~250MB
- Redis: ~128MB
- System: ~150MB
- **Total: ~1028MB** (dalam batas 1GB VPS)

---

## 🛠️ Management Commands

### View Logs

```bash
# LibraryDown API logs
journalctl -u librarydown-api -f

# LibraryDown Worker logs
journalctl -u librarydown-worker -f

# API Checker logs
journalctl -u apichecker -f

# Nginx logs
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log
```

---

### Restart Services

```bash
# Restart LibraryDown only
systemctl restart librarydown-api
systemctl restart librarydown-worker

# Restart API Checker
systemctl restart apichecker

# Restart Nginx
systemctl reload nginx
```

---

### Cleanup Media Files

```bash
# Manual cleanup (files older than 1 hour)
find /opt/librarydown/media/ -mmin +60 -type f -delete

# Check disk usage
du -sh /opt/librarydown/media/
df -h
```

---

## 🚨 Troubleshooting

### ❌ Nginx Test Failed

```bash
# Check syntax
nginx -t

# Common issue: Escaping \$ in rewrite
# Make sure config file uses single quotes in cat command:
# cat > file <<'EOF'  (with quotes around EOF)
```

---

### ❌ 502 Bad Gateway

```bash
# Check if LibraryDown is running
systemctl status librarydown-api

# Check if port 8001 is listening
netstat -tulpn | grep 8001

# Restart LibraryDown
systemctl restart librarydown-api
```

---

### ❌ Docs Still Shows Wrong API

```bash
# Clear browser cache
# Or use incognito mode

# Verify Nginx config is loaded
nginx -t
systemctl reload nginx

# Check which config files are active
ls -la /etc/nginx/conf.d/
```

---

### ❌ Out of Memory

```bash
# Check memory
free -h

# Add swap if needed
fallocate -l 1G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Or reduce workers
# Edit service files and change --workers or --concurrency to 1
```

---

## 🎯 API Endpoints Summary

### API Checker (`/api/checker/`)
- `GET /api/checker/stats` - System stats
- `GET /api/checker/check?ip=X&port=Y` - Connection check
- `GET /api/checker/myip` - IP info
- `POST /api/checker/sub` - VPN converter
- More: `/docs/checker`

### LibraryDown (`/api/downloader/`)
- `GET /api/downloader/platforms` - List platforms
- `GET /api/downloader/download?url=X` - Download video
- `GET /api/downloader/status/{task_id}` - Check status
- `GET /api/downloader/formats?url=X` - Get formats
- More: `/docs/downloader`

---

## 📝 Quick Reference

**Service Status:**
```bash
systemctl status apichecker librarydown-api librarydown-worker nginx redis
```

**All Logs:**
```bash
journalctl -u apichecker -u librarydown-api -u librarydown-worker -f
```

**Restart All:**
```bash
systemctl restart apichecker librarydown-api librarydown-worker
systemctl reload nginx
```

**Memory Check:**
```bash
free -h && echo "---" && systemctl status apichecker librarydown-api librarydown-worker | grep Memory
```

---

## ✅ Deployment Complete!

Akses kedua API Anda:

- 📘 **API Checker:** `http://YOUR_VPS_IP/api/checker/`
- 🎬 **LibraryDown:** `http://YOUR_VPS_IP/api/downloader/`
- 📖 **Docs Checker:** `http://YOUR_VPS_IP/docs/checker`
- 📖 **Docs Downloader:** `http://YOUR_VPS_IP/docs/downloader`

🎉 **Kedua API sekarang berjalan di 1 VPS!**
