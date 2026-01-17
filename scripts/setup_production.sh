#!/bin/bash

# LibraryDown Production Setup Script
# Untuk fresh deployment di VPS

set -e

echo "========================================"
echo "LibraryDown Production Setup"
echo "========================================"
echo ""

# 1. Install System Dependencies
echo "[1/7] Installing system dependencies..."
yum install -y python3 python3-pip redis git

# 2. Install ffmpeg
echo "[2/7] Installing ffmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    cd /tmp
    wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
    tar xvf ffmpeg-release-amd64-static.tar.xz
    cd ffmpeg-*-static
    cp ffmpeg ffprobe /usr/local/bin/
    chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe
    cd /
    rm -rf /tmp/ffmpeg*
    echo "✓ ffmpeg installed successfully"
else
    echo "✓ ffmpeg already installed"
fi

# 3. Clone repository
echo "[3/7] Setting up application directory..."
if [ ! -d "/opt/librarydown" ]; then
    git clone https://github.com/yourusername/librarydown.git /opt/librarydown
else
    echo "✓ Directory already exists"
fi

cd /opt/librarydown

# 4. Create virtual environment
echo "[4/7] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 5. Create cookies directory
echo "[5/7] Setting up cookies directory..."
mkdir -p /opt/librarydown/src/cookies
chmod 755 /opt/librarydown/src/cookies

# 6. Setup systemd services
echo "[6/7] Configuring systemd services..."

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

# 7. Configure Redis
echo "[7/7] Configuring Redis..."
systemctl enable redis
systemctl start redis
redis-cli CONFIG SET save ""
redis-cli CONFIG SET stop-writes-on-bgsave-error no

# Reload systemd and enable services
systemctl daemon-reload
systemctl enable librarydown-api
systemctl enable librarydown-worker

echo ""
echo "========================================"
echo "✓ Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and configure:"
echo "   cp /opt/librarydown/.env.example /opt/librarydown/.env"
echo "   nano /opt/librarydown/.env"
echo ""
echo "2. If using YouTube, upload cookies file:"
echo "   Upload youtube_cookies.txt to /root/Downloads/"
echo "   Run: bash /opt/librarydown/scripts/update_youtube_cookies.sh"
echo ""
echo "3. Start services:"
echo "   systemctl start librarydown-api"
echo "   systemctl start librarydown-worker"
echo ""
echo "4. Check status:"
echo "   systemctl status librarydown-api"
echo "   systemctl status librarydown-worker"
echo ""
echo "5. Monitor logs:"
echo "   journalctl -u librarydown-api -f"
echo "   journalctl -u librarydown-worker -f"
echo ""
