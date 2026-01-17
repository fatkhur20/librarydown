#!/bin/bash

##############################################################################
# LibraryDown - Full Deployment Script for Alibaba Cloud Linux
# Optimized for 1GB RAM VPS
##############################################################################

set -e  # Exit on error

echo "=========================================="
echo "  LibraryDown Deployment Script"
echo "  Full Deploy: FastAPI + Celery + Redis"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
APP_DIR="/opt/librarydown"
APP_USER="librarydown"
PYTHON_VERSION="3.11"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then 
        log_error "Please run as root"
        exit 1
    fi
    log_info "Running as root ✓"
}

check_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
        log_info "Detected OS: $PRETTY_NAME"
    else
        log_error "Cannot detect OS"
        exit 1
    fi
}

install_dependencies() {
    log_info "Installing system dependencies..."
    
    # Skip system update to avoid conflicts, install directly
    log_info "Installing required packages..."
    
    # Install Python 3.11 and dev tools
    log_info "Installing Python 3.11..."
    yum install -y python3.11 python3.11-pip python3.11-devel --skip-broken || log_warn "Python installation had warnings"
    yum install -y gcc gcc-c++ make --skip-broken || log_warn "Dev tools installation had warnings"
    
    # Install Redis
    log_info "Installing Redis..."
    yum install -y redis --skip-broken || log_warn "Redis installation had warnings"
    
    # Install FFmpeg
    log_info "Installing FFmpeg..."
    yum install -y epel-release --skip-broken || log_warn "EPEL installation had warnings"
    yum install -y ffmpeg ffmpeg-devel --skip-broken || log_warn "FFmpeg installation had warnings"
    
    # Install Nginx
    log_info "Installing Nginx..."
    yum install -y nginx --skip-broken || log_warn "Nginx installation had warnings"
    
    # Install git
    log_info "Installing git..."
    yum install -y git --skip-broken || log_warn "Git installation had warnings"
    
    log_info "System dependencies installed ✓"
}

create_app_user() {
    log_info "Creating application user..."
    
    if id "$APP_USER" &>/dev/null; then
        log_warn "User $APP_USER already exists"
    else
        useradd -r -s /bin/bash -d $APP_DIR $APP_USER
        log_info "User $APP_USER created ✓"
    fi
}

setup_application() {
    log_info "Setting up application..."
    
    # Create app directory
    mkdir -p $APP_DIR
    
    # Copy files (assuming script is run from project root)
    if [ -d "/root/librarydown" ]; then
        log_info "Copying files from /root/librarydown..."
        cp -r /root/librarydown/* $APP_DIR/
    else
        log_error "Source directory not found!"
        exit 1
    fi
    
    # Create necessary directories
    mkdir -p $APP_DIR/media
    mkdir -p $APP_DIR/logs
    mkdir -p $APP_DIR/data
    
    # Set permissions
    chown -R $APP_USER:$APP_USER $APP_DIR
    chmod -R 755 $APP_DIR
    
    log_info "Application setup complete ✓"
}

setup_python_env() {
    log_info "Setting up Python virtual environment..."
    
    cd $APP_DIR
    
    # Create venv
    sudo -u $APP_USER python3.11 -m venv venv
    
    # Upgrade pip
    sudo -u $APP_USER $APP_DIR/venv/bin/pip install --upgrade pip
    
    # Install dependencies
    log_info "Installing Python dependencies (this may take a few minutes)..."
    sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r requirements.txt
    
    log_info "Python environment ready ✓"
}

configure_redis() {
    log_info "Configuring Redis for low memory..."
    
    # Optimize Redis for 1GB RAM
    cat > /etc/redis.conf <<EOF
# Redis Configuration - Optimized for 1GB RAM
bind 127.0.0.1
port 6379
daemonize yes
pidfile /var/run/redis_6379.pid
loglevel notice
logfile /var/log/redis/redis.log

# Memory optimization
maxmemory 128mb
maxmemory-policy allkeys-lru

# Persistence (minimal)
save 900 1
save 300 10
save 60 10000

# Disable some features to save memory
appendonly no
EOF
    
    # Create log directory
    mkdir -p /var/log/redis
    chown redis:redis /var/log/redis
    
    # Start Redis
    systemctl enable redis
    systemctl restart redis
    
    log_info "Redis configured and started ✓"
}

create_systemd_services() {
    log_info "Creating systemd services..."
    
    # FastAPI Service
    cat > /etc/systemd/system/librarydown-api.service <<EOF
[Unit]
Description=LibraryDown FastAPI Application
After=network.target redis.service

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10

# Resource limits (for 1GB RAM)
MemoryLimit=300M
CPUQuota=80%

[Install]
WantedBy=multi-user.target
EOF
    
    # Celery Worker Service
    cat > /etc/systemd/system/librarydown-worker.service <<EOF
[Unit]
Description=LibraryDown Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/celery -A src.workers.celery_app worker --loglevel=info --concurrency=2
Restart=always
RestartSec=10

# Resource limits
MemoryLimit=250M
CPUQuota=80%

[Install]
WantedBy=multi-user.target
EOF
    
    # Celery Beat Service (for cleanup tasks)
    cat > /etc/systemd/system/librarydown-beat.service <<EOF
[Unit]
Description=LibraryDown Celery Beat Scheduler
After=network.target redis.service

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/celery -A src.workers.celery_app beat --loglevel=info
Restart=always
RestartSec=10

# Resource limits
MemoryLimit=100M

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    
    log_info "Systemd services created ✓"
}

configure_nginx() {
    log_info "Configuring Nginx..."
    
    cat > /etc/nginx/conf.d/librarydown.conf <<EOF
# LibraryDown Nginx Configuration

upstream librarydown_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name _;  # Replace with your domain
    
    client_max_body_size 100M;
    
    # API
    location / {
        proxy_pass http://librarydown_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts for long downloads
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # Media files
    location /media/ {
        alias $APP_DIR/media/;
        expires 1h;
        add_header Cache-Control "public, immutable";
    }
    
    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF
    
    # Test Nginx config
    nginx -t
    
    # Enable and start Nginx
    systemctl enable nginx
    systemctl restart nginx
    
    log_info "Nginx configured and started ✓"
}

configure_firewall() {
    log_info "Configuring firewall..."
    
    # Check if firewalld is installed
    if command -v firewall-cmd &> /dev/null; then
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --reload
        log_info "Firewall configured ✓"
    else
        log_warn "Firewalld not installed, skipping firewall configuration"
    fi
}

start_services() {
    log_info "Starting all services..."
    
    # Enable services
    systemctl enable librarydown-api
    systemctl enable librarydown-worker
    systemctl enable librarydown-beat
    
    # Start services
    systemctl start librarydown-api
    systemctl start librarydown-worker
    systemctl start librarydown-beat
    
    # Wait a bit
    sleep 3
    
    # Check status
    log_info "Checking service status..."
    systemctl status librarydown-api --no-pager || true
    systemctl status librarydown-worker --no-pager || true
    systemctl status librarydown-beat --no-pager || true
    
    log_info "Services started ✓"
}

show_status() {
    echo ""
    echo "=========================================="
    echo "  Deployment Complete!"
    echo "=========================================="
    echo ""
    log_info "Application deployed to: $APP_DIR"
    log_info "Services running:"
    echo "  - librarydown-api (FastAPI)"
    echo "  - librarydown-worker (Celery Worker)"
    echo "  - librarydown-beat (Celery Beat)"
    echo ""
    log_info "Access your application:"
    echo "  - API: http://YOUR_SERVER_IP/"
    echo "  - Docs: http://YOUR_SERVER_IP/docs"
    echo "  - Health: http://YOUR_SERVER_IP/health"
    echo ""
    log_info "Useful commands:"
    echo "  - Check status: systemctl status librarydown-api"
    echo "  - View logs: journalctl -u librarydown-api -f"
    echo "  - Restart: systemctl restart librarydown-api"
    echo ""
    log_info "Memory usage:"
    free -h
    echo ""
}

# Main execution
main() {
    log_info "Starting deployment..."
    
    check_root
    check_os
    
    install_dependencies
    create_app_user
    setup_application
    setup_python_env
    configure_redis
    create_systemd_services
    configure_nginx
    configure_firewall
    start_services
    
    show_status
    
    log_info "Deployment completed successfully! 🎉"
}

# Run main function
main
