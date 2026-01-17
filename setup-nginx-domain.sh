#!/bin/bash

# Nginx Configuration for Dual API - Domain Based
# Domain: vortex-xx.biz.id
# - api.vortex-xx.biz.id → API Checker (port 8000)
# - apdl.vortex-xx.biz.id → LibraryDown (port 8001)

echo "=========================================="
echo "  Setup Nginx - Domain Based Routing"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root"
    exit 1
fi

echo "[1/4] Creating Nginx configuration..."

cat > /etc/nginx/conf.d/dual-api.conf <<'EOF'
# ============================================
# Dual API Configuration - Domain Based
# ============================================

# ===== API CHECKER =====
server {
    listen 80;
    server_name api.vortex-xx.biz.id;
    
    client_max_body_size 100M;
    
    # Proxy to API Checker (port 8000)
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
        proxy_pass http://127.0.0.1:8000/stats;
    }
}

# ===== LIBRARYDOWN =====
server {
    listen 80;
    server_name apdl.vortex-xx.biz.id;
    
    client_max_body_size 100M;
    
    # Proxy to LibraryDown (port 8001)
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

# ===== FALLBACK (IP Direct Access) =====
server {
    listen 80 default_server;
    server_name _;
    
    location / {
        return 200 '{
  "message": "Dual API Server - vortex-xx.biz.id",
  "apis": {
    "checker": "http://api.vortex-xx.biz.id",
    "downloader": "http://apdl.vortex-xx.biz.id"
  },
  "docs": {
    "checker": "http://api.vortex-xx.biz.id/docs",
    "downloader": "http://apdl.vortex-xx.biz.id/docs"
  }
}';
        add_header Content-Type application/json;
    }
}
EOF

echo "✓ Nginx config created: /etc/nginx/conf.d/dual-api.conf"

echo ""
echo "[2/4] Backing up old configs..."
mkdir -p /etc/nginx/conf.d/backup
mv /etc/nginx/conf.d/*.conf.default /etc/nginx/conf.d/backup/ 2>/dev/null || true
echo "✓ Old configs backed up"

echo ""
echo "[3/4] Testing Nginx configuration..."
if nginx -t 2>&1 | grep -q "test is successful"; then
    echo "✓ Nginx config test passed"
else
    echo "✗ Nginx config test failed!"
    nginx -t
    exit 1
fi

echo ""
echo "[4/4] Reloading Nginx..."
systemctl reload nginx
echo "✓ Nginx reloaded"

echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "Your APIs are now accessible via:"
echo "  - API Checker: http://api.vortex-xx.biz.id"
echo "  - LibraryDown: http://apdl.vortex-xx.biz.id"
echo ""
echo "Documentation:"
echo "  - API Checker Docs: http://api.vortex-xx.biz.id/docs"
echo "  - LibraryDown Docs: http://apdl.vortex-xx.biz.id/docs"
echo ""
echo "IMPORTANT: Make sure DNS A Records are set:"
echo "  - api.vortex-xx.biz.id → YOUR_VPS_IP"
echo "  - apdl.vortex-xx.biz.id → YOUR_VPS_IP"
echo ""
echo "To enable HTTPS (recommended):"
echo "  yum install -y certbot python3-certbot-nginx"
echo "  certbot --nginx -d api.vortex-xx.biz.id -d apdl.vortex-xx.biz.id"
echo ""
