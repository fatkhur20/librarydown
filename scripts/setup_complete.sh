#!/bin/bash

# LibraryDown Complete Setup Script
# Full deployment + cookies installation

set -e

echo "========================================"
echo "LibraryDown Complete Setup"
echo "========================================"
echo ""

# Check if this is initial setup or update
if [ -d "/opt/librarydown" ]; then
    echo "📦 Detected existing installation"
    SETUP_MODE="update"
else
    echo "🆕 Fresh installation mode"
    SETUP_MODE="fresh"
fi

if [ "$SETUP_MODE" == "fresh" ]; then
    # ========================================
    # FRESH INSTALLATION
    # ========================================
    
    echo ""
    echo "[STEP 1/10] Installing system dependencies..."
    yum install -y python3 python3-pip redis git

    echo ""
    echo "[STEP 2/10] Installing ffmpeg..."
    if ! command -v ffmpeg &> /dev/null; then
        cd /tmp
        wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
        tar xvf ffmpeg-release-amd64-static.tar.xz
        cd ffmpeg-*-static
        cp ffmpeg ffprobe /usr/local/bin/
        chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe
        cd /
        rm -rf /tmp/ffmpeg*
        echo "  ✓ ffmpeg installed"
    else
        echo "  ✓ ffmpeg already installed"
    fi

    echo ""
    echo "[STEP 3/10] Cloning repository..."
    if [ ! -d "/opt/librarydown" ]; then
        git clone https://github.com/yourusername/librarydown.git /opt/librarydown || cp -r /root/librarydown /opt/librarydown
    fi

    echo ""
    echo "[STEP 4/10] Setting up Python virtual environment..."
    cd /opt/librarydown
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt

    echo ""
    echo "[STEP 5/10] Creating directories..."
    mkdir -p /opt/librarydown/src/cookies
    mkdir -p /opt/librarydown/media
    chmod 755 /opt/librarydown/src/cookies
    chmod 755 /opt/librarydown/media

    echo ""
    echo "[STEP 6/10] Configuring systemd services..."
    
    # API Service
    cat > /etc/systemd/system/librarydown-api.service <<'EOF'
[Unit]
Description=LibraryDown API Server
After=network.target redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/librarydown
EnvironmentFile=/opt/librarydown/.env
Environment="PATH=/usr/local/bin:/opt/librarydown/venv/bin:/usr/bin:/bin"
ExecStart=/opt/librarydown/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

# Resource limits
MemoryLimit=300M
CPUQuota=80%

# Logging
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # Worker Service
    cat > /etc/systemd/system/librarydown-worker.service <<'EOF'
[Unit]
Description=LibraryDown Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/librarydown
EnvironmentFile=/opt/librarydown/.env
Environment="PATH=/usr/local/bin:/opt/librarydown/venv/bin:/usr/bin:/bin"
ExecStart=/opt/librarydown/venv/bin/celery -A src.workers.celery_app worker --loglevel=info --concurrency=2
Restart=always
RestartSec=10

# Resource limits
MemoryLimit=250M
CPUQuota=80%

# Logging
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    echo ""
    echo "[STEP 7/10] Configuring Redis..."
    systemctl enable redis
    systemctl start redis
    redis-cli CONFIG SET save ""
    redis-cli CONFIG SET stop-writes-on-bgsave-error no

    systemctl daemon-reload
    systemctl enable librarydown-api
    systemctl enable librarydown-worker
fi

# ========================================
# COOKIES INSTALLATION (FRESH + UPDATE)
# ========================================

echo ""
echo "[STEP 8/10] Installing cookies files..."

# YouTube cookies
if [ -f "/root/Downloads/youtube_cookies.txt" ] || [ -f "/root/youtube_cookies.txt" ]; then
    echo "  📍 YouTube cookies found, installing..."
    YOUTUBE_COOKIES=""
    if [ -f "/root/Downloads/youtube_cookies.txt" ]; then
        YOUTUBE_COOKIES="/root/Downloads/youtube_cookies.txt"
    elif [ -f "/root/youtube_cookies.txt" ]; then
        YOUTUBE_COOKIES="/root/youtube_cookies.txt"
    fi
    
    if [ -n "$YOUTUBE_COOKIES" ]; then
        cp "$YOUTUBE_COOKIES" /opt/librarydown/src/cookies/youtube_cookies.txt
        chmod 644 /opt/librarydown/src/cookies/youtube_cookies.txt
        echo "  ✓ YouTube cookies installed"
    fi
else
    echo "  ⚠️  YouTube cookies not found (optional)"
    echo "     Upload to /root/Downloads/youtube_cookies.txt if needed"
fi

# Instagram cookies
if [ -f "/root/Downloads/instagram_cookies.txt" ] || [ -f "/root/instagram_cookies.txt" ]; then
    echo "  📍 Instagram cookies found, installing..."
    INSTAGRAM_COOKIES=""
    if [ -f "/root/Downloads/instagram_cookies.txt" ]; then
        INSTAGRAM_COOKIES="/root/Downloads/instagram_cookies.txt"
    elif [ -f "/root/instagram_cookies.txt" ]; then
        INSTAGRAM_COOKIES="/root/instagram_cookies.txt"
    fi
    
    if [ -n "$INSTAGRAM_COOKIES" ]; then
        cp "$INSTAGRAM_COOKIES" /opt/librarydown/src/cookies/instagram_cookies.txt
        chmod 644 /opt/librarydown/src/cookies/instagram_cookies.txt
        echo "  ✓ Instagram cookies installed"
    fi
else
    echo "  ⚠️  Instagram cookies not found (optional)"
    echo "     Upload to /root/Downloads/instagram_cookies.txt if needed"
fi

echo ""
echo "[STEP 9/10] Starting services..."
systemctl start librarydown-api
systemctl start librarydown-worker

sleep 3

echo ""
echo "[STEP 10/10] Checking service status..."
API_STATUS=$(systemctl is-active librarydown-api)
WORKER_STATUS=$(systemctl is-active librarydown-worker)
REDIS_STATUS=$(systemctl is-active redis)

echo "  API:    $API_STATUS"
echo "  Worker: $WORKER_STATUS"
echo "  Redis:  $REDIS_STATUS"

echo ""
echo "========================================"
if [ "$API_STATUS" == "active" ] && [ "$WORKER_STATUS" == "active" ] && [ "$REDIS_STATUS" == "active" ]; then
    echo "✅ Setup Complete - All Systems Ready!"
else
    echo "⚠️  Setup Complete with Warnings"
fi
echo "========================================"
echo ""

if [ "$SETUP_MODE" == "fresh" ]; then
    echo "📝 Next Steps:"
    echo ""
    echo "1. Configure environment:"
    echo "   nano /opt/librarydown/.env"
    echo ""
    echo "2. Upload cookies (if not already):"
    echo "   - YouTube:   /root/Downloads/youtube_cookies.txt"
    echo "   - Instagram: /root/Downloads/instagram_cookies.txt"
    echo "   Then run: bash $0"
    echo ""
fi

echo "🔍 Check status:"
echo "   bash /root/librarydown/scripts/health_check.sh"
echo ""
echo "📊 Monitor logs:"
echo "   journalctl -u librarydown-api -f"
echo "   journalctl -u librarydown-worker -f"
echo ""
echo "🧪 Test download:"
echo "   # YouTube"
echo "   curl -X POST http://localhost:8001/download \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"url\": \"https://youtube.com/watch?v=dQw4w9WgXcQ\"}'"
echo ""
echo "   # Instagram"
echo "   curl -X POST http://localhost:8001/download \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"url\": \"https://www.instagram.com/reel/XXX/\"}'"
echo ""
