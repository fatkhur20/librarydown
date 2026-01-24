# 🚀 Deploy LibraryDown dengan Domain/Subdomain

Panduan deploy **LibraryDown** di VPS yang sama dengan **API Checker** menggunakan **subdomain berbeda** untuk tiap API.

---

## 🎯 Arsitektur (Domain-Based)

```
VPS (1GB RAM)
├── checker.yourdomain.com  → API Checker (port 8000)
├── downloader.yourdomain.com → LibraryDown (port 8001)
├── Port 8000: API Checker
├── Port 8001: LibraryDown
└── Port 6379: Redis (shared)
```

**Contoh akses setelah deployment:**
- API Checker: `http://checker.yourdomain.com/`
- API Checker Docs: `http://checker.yourdomain.com/docs`
- LibraryDown: `http://downloader.yourdomain.com/`
- LibraryDown Docs: `http://downloader.yourdomain.com/docs`

---

## 📋 Prerequisites

✅ **Domain:** Anda sudah punya domain (misal: `yourdomain.com`)  
✅ **DNS Access:** Bisa buat A Record di DNS provider  
✅ **VPS:** API Checker sudah running di port 8000  
✅ **Root Access:** Login sebagai root

---

## 🚀 Deployment (4 Steps)

### Step 1: Setup DNS Records

Login ke DNS provider Anda (Cloudflare, Namecheap, GoDaddy, dll) dan buat **2 A Records**:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | checker | YOUR_VPS_IP | 300 |
| A | downloader | YOUR_VPS_IP | 300 |

**Contoh:**
- `checker.yourdomain.com` → `47.88.12.34`
- `downloader.yourdomain.com` → `47.88.12.34`

**Tunggu 5-10 menit** untuk DNS propagation.

**Test DNS:**
```bash
# Dari komputer lokal Anda
ping checker.yourdomain.com
ping downloader.yourdomain.com

# Keduanya harus resolve ke IP VPS Anda
```

---

### Step 2: Deploy LibraryDown di VPS

Login ke VPS dan jalankan deploy script:

```bash
ssh root@YOUR_VPS_IP

cd /root/librarydown
chmod +x deploy.sh
./deploy.sh
```

**Script akan:**
- Install dependencies (Python, FFmpeg, Redis, dll)
- Setup LibraryDown di port 8001
- Create systemd services
- Skip Nginx config (kita setup manual)

**Tunggu 10-15 menit hingga selesai.**

**Verifikasi:**
```bash
# Cek services
systemctl status librarydown-api
systemctl status librarydown-worker

# Test API
curl http://localhost:8001/
curl http://localhost:8001/platforms
```

---

### Step 3: Configure Nginx (Domain-Based)

Sekarang kita setup Nginx untuk routing berdasarkan domain.

**Backup config lama:**
```bash
cp /etc/nginx/conf.d/apichecker.conf /etc/nginx/conf.d/apichecker.conf.backup 2>/dev/null || true
```

**Buat config baru:**

```bash
cat > /etc/nginx/conf.d/dual-api-domain.conf <<'EOF'
# Dual API Configuration - Domain Based

# ===== API CHECKER =====
server {
    listen 80;
    server_name checker.yourdomain.com;  # GANTI dengan domain Anda!
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Health check
    location /health {
        access_log off;
        return 200 "API Checker - healthy\n";
        add_header Content-Type text/plain;
    }
}

# ===== LIBRARYDOWN =====
server {
    listen 80;
    server_name downloader.yourdomain.com;  # GANTI dengan domain Anda!
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Long timeout for downloads
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # Media files
    location /media/ {
        alias /opt/librarydown/media/;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }
    
    # Health check
    location /health {
        access_log off;
        return 200 "LibraryDown - healthy\n";
        add_header Content-Type text/plain;
    }
}

# ===== FALLBACK (IP Access) =====
server {
    listen 80 default_server;
    server_name _;
    
    location / {
        return 200 '{"message": "Dual API Server", "apis": {"checker": "http://checker.yourdomain.com", "downloader": "http://downloader.yourdomain.com"}}';
        add_header Content-Type application/json;
    }
}
EOF
```

**⚠️ PENTING:** Edit file tersebut dan ganti `yourdomain.com` dengan domain Anda!

```bash
# Edit config
nano /etc/nginx/conf.d/dual-api-domain.conf

# Ganti:
# - checker.yourdomain.com → checker.namadomainanda.com
# - downloader.yourdomain.com → downloader.namadomainanda.com
```

**Disable config lama:**
```bash
mv /etc/nginx/conf.d/apichecker.conf /etc/nginx/conf.d/apichecker.conf.disabled 2>/dev/null || true
mv /etc/nginx/conf.d/librarydown.conf /etc/nginx/conf.d/librarydown.conf.disabled 2>/dev/null || true
```

**Test & reload Nginx:**
```bash
# Test config
nginx -t

# Jika OK, reload
systemctl reload nginx
```

---

### Step 4: Verification & Testing

**Test dari VPS:**
```bash
# Test API Checker
curl -H "Host: checker.yourdomain.com" http://localhost/

# Test LibraryDown
curl -H "Host: downloader.yourdomain.com" http://localhost/platforms
```

**Test dari browser:**

Buka browser dan akses:

✅ **API Checker:**
- Root: `http://checker.yourdomain.com/`
- Docs: `http://checker.yourdomain.com/docs`
- Stats: `http://checker.yourdomain.com/stats`

✅ **LibraryDown:**
- Root: `http://downloader.yourdomain.com/`
- Docs: `http://downloader.yourdomain.com/docs`
- Platforms: `http://downloader.yourdomain.com/platforms`

**Test download:**
```bash
curl "http://downloader.yourdomain.com/download?url=https://vt.tiktok.com/ZS593uwQc/"
```

---

## 🔒 Setup SSL/HTTPS (Optional tapi Recommended)

Setelah HTTP berhasil, install SSL certificate menggunakan Let's Encrypt:

```bash
# Install certbot
yum install -y certbot python3-certbot-nginx

# Get certificates untuk kedua subdomain
certbot --nginx -d checker.yourdomain.com -d downloader.yourdomain.com

# Ikuti prompt:
# - Email address: your-email@example.com
# - Agree to terms: Y
# - Redirect HTTP to HTTPS: Y (recommended)
```

**Certbot akan otomatis:**
- Generate SSL certificates
- Update Nginx config
- Setup auto-renewal

**Setelah SSL terinstall, akses via HTTPS:**
- `https://checker.yourdomain.com/`
- `https://downloader.yourdomain.com/`

**Test auto-renewal:**
```bash
certbot renew --dry-run
```

---

## ✅ Final Verification

```bash
# Check all services
systemctl status apichecker
systemctl status librarydown-api
systemctl status librarydown-worker
systemctl status nginx

# Check memory
free -h

# Check logs
journalctl -u librarydown-api -n 50
journalctl -u librarydown-worker -n 50
```

---

## 🎯 Access URLs (After Setup)

### HTTP:
- 🔧 **API Checker:** `http://checker.yourdomain.com/`
- 🎬 **LibraryDown:** `http://downloader.yourdomain.com/`
- 📘 **Docs Checker:** `http://checker.yourdomain.com/docs`
- 📖 **Docs Downloader:** `http://downloader.yourdomain.com/docs`

### HTTPS (after SSL):
- 🔧 **API Checker:** `https://checker.yourdomain.com/`
- 🎬 **LibraryDown:** `https://downloader.yourdomain.com/`
- 📘 **Docs Checker:** `https://checker.yourdomain.com/docs`
- 📖 **Docs Downloader:** `https://downloader.yourdomain.com/docs`

---

## 📊 API Endpoints

### API Checker (`checker.yourdomain.com`)
```bash
# System stats
curl http://checker.yourdomain.com/stats

# IP check
curl "http://checker.yourdomain.com/check?ip=8.8.8.8&port=53"

# MyIP
curl http://checker.yourdomain.com/myip

# Docs
http://checker.yourdomain.com/docs
```

### LibraryDown (`downloader.yourdomain.com`)
```bash
# List platforms
curl http://downloader.yourdomain.com/platforms

# Download
curl "http://downloader.yourdomain.com/download?url=VIDEO_URL"

# Check status
curl http://downloader.yourdomain.com/status/TASK_ID

# Get formats
curl "http://downloader.yourdomain.com/formats?url=VIDEO_URL"

# Docs
http://downloader.yourdomain.com/docs
```

---

## 🛠️ Management Commands

### View Logs
```bash
# LibraryDown logs
journalctl -u librarydown-api -f
journalctl -u librarydown-worker -f

# API Checker logs
journalctl -u apichecker -f

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Restart Services
```bash
# Restart LibraryDown
systemctl restart librarydown-api
systemctl restart librarydown-worker

# Restart API Checker
systemctl restart apichecker

# Reload Nginx
systemctl reload nginx
```

### Check Status
```bash
# All services
systemctl status apichecker librarydown-api librarydown-worker nginx

# Memory usage
free -h
systemctl status apichecker | grep Memory
systemctl status librarydown-api | grep Memory
systemctl status librarydown-worker | grep Memory
```

---

## 🚨 Troubleshooting

### ❌ Domain tidak resolve

```bash
# Test DNS dari VPS
nslookup checker.yourdomain.com
nslookup downloader.yourdomain.com

# Jika tidak resolve:
# 1. Cek DNS records di provider
# 2. Tunggu DNS propagation (5-30 menit)
# 3. Clear DNS cache: systemctl restart systemd-resolved
```

---

### ❌ 502 Bad Gateway

```bash
# Cek service status
systemctl status librarydown-api

# Cek apakah port listening
netstat -tulpn | grep 8001

# Restart service
systemctl restart librarydown-api
```

---

### ❌ SSL Certificate Failed

```bash
# Make sure domain resolve to VPS IP
ping checker.yourdomain.com

# Make sure port 80 and 443 open
firewall-cmd --list-all

# Try again
certbot --nginx -d checker.yourdomain.com -d downloader.yourdomain.com
```

---

### ❌ Wrong API shows up

```bash
# Check Nginx config
nginx -t

# Check which config files are active
ls -la /etc/nginx/conf.d/

# Make sure old configs are disabled
mv /etc/nginx/conf.d/apichecker.conf /etc/nginx/conf.d/apichecker.conf.disabled
mv /etc/nginx/conf.d/librarydown.conf /etc/nginx/conf.d/librarydown.conf.disabled

# Reload
systemctl reload nginx

# Clear browser cache or use incognito
```

---

## 💡 Tips

### Custom Port (Development)

Jika mau test langsung via port tanpa domain:

```bash
# API Checker (port 8000)
curl http://YOUR_VPS_IP:8000/

# LibraryDown (port 8001)
curl http://YOUR_VPS_IP:8001/
```

### Update Domain

Jika ganti domain, edit Nginx config:

```bash
nano /etc/nginx/conf.d/dual-api-domain.conf

# Ganti server_name
# Test dan reload
nginx -t && systemctl reload nginx

# Update SSL
certbot --nginx -d new-domain.com
```

### Monitoring

Setup monitoring untuk kedua API:

```bash
# Create simple health check script
cat > /root/check-apis.sh <<'EOF'
#!/bin/bash
echo "=== API Health Check ==="
echo "API Checker:"
curl -s http://checker.yourdomain.com/health
echo "LibraryDown:"
curl -s http://downloader.yourdomain.com/health
EOF

chmod +x /root/check-apis.sh

# Run every 5 minutes via cron
crontab -e
# Add: */5 * * * * /root/check-apis.sh
```

---

## 📝 Quick Reference

**Config file location:**
```
/etc/nginx/conf.d/dual-api-domain.conf
```

**Service names:**
```
apichecker
librarydown-api
librarydown-worker
librarydown-beat
nginx
redis
```

**Important directories:**
```
/opt/apichecker/         # API Checker
/opt/librarydown/        # LibraryDown
/opt/librarydown/media/  # Downloaded files
```

**Check everything:**
```bash
systemctl status apichecker librarydown-api librarydown-worker nginx redis
```

---

## ✅ Deployment Checklist

- [ ] DNS A records created (checker + downloader)
- [ ] DNS propagation complete (ping test works)
- [ ] LibraryDown deployed (deploy.sh ran successfully)
- [ ] Nginx configured with domain-based routing
- [ ] Both APIs accessible via subdomain
- [ ] Docs accessible for both APIs
- [ ] SSL certificates installed (optional)
- [ ] All services running and healthy
- [ ] Memory usage acceptable (~880MB total)

---

## 🎉 Done!

Sekarang Anda punya **2 API berbeda dengan subdomain berbeda** di 1 VPS:

- 🔧 **API Checker:** `http://checker.yourdomain.com`
- 🎬 **LibraryDown:** `http://downloader.yourdomain.com`

**Documentation akan tampil correct** karena tiap subdomain route ke backend berbeda! 🚀
