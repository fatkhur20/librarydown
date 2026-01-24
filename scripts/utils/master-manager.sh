#!/bin/bash
# LibraryDown Master Manager
# Single script for all LibraryDown operations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIBRARYDOWN_DIR="/root/librarydown"
APICHECKER_DIR="/root/apichecker"
APICHECKER_SERVICE_ENABLED=false

show_header() {
    echo "=========================================="
    echo "    LibraryDown Master Management Suite    "
    echo "=========================================="
    echo ""
}

show_usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Installation:"
    echo "  setup         - Fresh installation (dependencies + services + start)"
    echo "  install       - Install dependencies only"
    echo "  services      - Install systemd services only"
    echo ""
    echo "Management:"
    echo "  start         - Start all services (auto-detect environment)"
    echo "  stop          - Stop all services"
    echo "  restart       - Restart all services"
    echo "  status        - Show service status"
    echo ""
    echo "Bot & Cookies:"
    echo "  bot-config    - Configure Telegram bot settings"
    echo "  bot-start     - Start only the Telegram bot"
    echo "  bot-stop      - Stop the Telegram bot"
    echo "  upload-test   - Test cookie upload functionality"
    echo ""
    echo "Monitoring:"
    echo "  monitor       - Monitor services continuously"
    echo "  check         - Run system diagnostics"
    echo "  logs          - Show recent logs"
    echo ""
    echo "Maintenance:"
    echo "  backup        - Backup configuration and cookies"
    echo "  restore       - Restore from backup"
    echo "  clean         - Clean old backups and logs"
    echo "  update        - Update system to latest version"
    echo ""
}

# Install dependencies
install_deps() {
    echo "[INSTALLING] Dependencies..."
    
    cd "$LIBRARYDOWN_DIR"
    
    # Remove old venv if it exists with old Python version
    if [ -d "venv" ]; then
        VENV_PYTHON_VERSION=$(venv/bin/python3 --version 2>&1 | grep -oP '\d+\.\d+')
        if [[ "$VENV_PYTHON_VERSION" < "3.10" ]]; then
            echo "[INFO] Removing old virtual environment (Python $VENV_PYTHON_VERSION)..."
            rm -rf venv
        fi
    fi
    
    # Check if virtual environment exists, create if not
    if [ ! -d "venv" ]; then
        echo "[INFO] Creating virtual environment with Python 3.13..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install/update requirements using global PyPI (not Aliyun mirror)
    echo "[INFO] Upgrading pip..."
    pip3 install --upgrade pip --index-url https://pypi.org/simple
    
    echo "[INFO] Installing requirements from PyPI..."
    pip3 install -r requirements.txt --index-url https://pypi.org/simple
    
    # Install telegram python library if not present
    if ! python3 -c "import telegram" >/dev/null 2>&1; then
        pip3 install python-telegram-bot --index-url https://pypi.org/simple
    fi
    
    echo "[SUCCESS] Dependencies installed"
}

# Create cookie directories
create_dirs() {
    echo "[CREATING] Cookie directories..."
    sudo mkdir -p /opt/librarydown/cookies
    sudo chown root:root /opt/librarydown
    sudo chown root:root /opt/librarydown/cookies
    sudo chmod 755 /opt/librarydown
    sudo chmod 755 /opt/librarydown/cookies
    echo "[SUCCESS] Cookie directories created"
}

# Install systemd services
install_services() {
    echo "[INSTALLING] Systemd services..."
    
    # Check if service files exist
    if [ ! -f "$LIBRARYDOWN_DIR/librarydown-api.service" ]; then
        echo "[INFO] Systemd service files not found, will use manual mode instead"
        echo "[INFO] Services will be started using nohup in background"
        return 0
    fi
    
    # Check if systemd is available
    if ! command -v systemctl >/dev/null 2>&1; then
        echo "[INFO] Systemd not available, will use manual mode instead"
        return 0
    fi
    
    # Copy LibraryDown service files to systemd directory
    sudo cp "$LIBRARYDOWN_DIR/librarydown-api.service" /etc/systemd/system/
    sudo cp "$LIBRARYDOWN_DIR/librarydown-worker.service" /etc/systemd/system/
    sudo cp "$LIBRARYDOWN_DIR/librarydown-bot.service" /etc/systemd/system/
    
    # Copy API Checker service if the directory and file exist
    if [ -d "$APICHECKER_DIR" ]; then
        if [ -f "$APICHECKER_DIR/apichecker-optimize.service" ]; then
            sudo cp "$APICHECKER_DIR/apichecker-optimize.service" /etc/systemd/system/apichecker-api.service
            APICHECKER_SERVICE_ENABLED=true
        else
            echo "[WARNING] API Checker service file not found, skipping..."
            APICHECKER_SERVICE_ENABLED=false
        fi
    else
        echo "[WARNING] API Checker directory not found, skipping..."
        APICHECKER_SERVICE_ENABLED=false
    fi
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable services based on what's available
    if [ "$APICHECKER_SERVICE_ENABLED" = true ]; then
        sudo systemctl enable librarydown-api librarydown-worker librarydown-bot apichecker-api
    else
        sudo systemctl enable librarydown-api librarydown-worker librarydown-bot
    fi
    
    echo "[SUCCESS] Services installed and enabled"
}

# Start services based on environment
start_services() {
    echo "[STARTING] All services..."
    
    # Check if systemd is available (not available in Termux)
    if command -v systemctl >/dev/null 2>&1; then
        # Systemd environment
        echo "Starting Redis..."
        sudo systemctl start redis-server
        
        # Start API Checker if available
        if [ -f "/etc/systemd/system/apichecker-api.service" ]; then
            echo "Starting API Checker (port 8000)..."
            sudo systemctl start apichecker-api
        else
            echo "[INFO] API Checker not installed, skipping..."
        fi
        
        echo "Starting LibraryDown API (port 8001)..."
        sudo systemctl start librarydown-api
        
        echo "Starting LibraryDown Worker..."
        sudo systemctl start librarydown-worker
        
        echo "Starting LibraryDown Telegram Bot..."
        sudo systemctl start librarydown-bot
        
        echo ""
        echo "[SUCCESS] All services started via systemd!"
    else
        # Termux environment - start manually
        echo "[INFO] Termux environment detected - starting services manually"
        start_services_manual
    fi
}

start_services_manual() {
    echo "[STARTING] All services in manual mode (for Termux)..."
    
    # Start Redis if available
    if command -v redis-server >/dev/null 2>&1; then
        echo "Starting Redis (if not running)..."
        if ! pgrep -f redis-server > /dev/null; then
            redis-server > /dev/null 2>&1 &
            sleep 1
        fi
    fi
    
    # Start API Checker if directory exists
    if [ -d "/root/apichecker" ]; then
        # Check for port conflict before starting
        if check_port_conflicts 8000 "API Checker"; then
            echo "Starting API Checker (port 8000) in background..."
            cd /root/apichecker
            if [ -d "venv" ]; then
                source venv/bin/activate
            fi
            pkill -f "uvicorn.*8000" 2>/dev/null || true
            nohup uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 1 > /root/apichecker/api_checker.log 2>&1 &
        else
            echo "[SKIPPED] API Checker due to port conflict"
        fi
    else
        echo "[INFO] API Checker directory not found, skipping..."
    fi
    
    # Start LibraryDown API
    # Check for port conflict before starting
    if check_port_conflicts 8001 "LibraryDown API"; then
        echo "Starting LibraryDown API (port 8001) in background..."
        cd /root/librarydown
        if [ -d "venv" ]; then
            source venv/bin/activate
        fi
        pkill -f "uvicorn.*8001" 2>/dev/null || true
        nohup uvicorn src.api.main:app --host 0.0.0.0 --port 8001 --workers 1 > /root/librarydown/api_server.log 2>&1 &
    else
        echo "[SKIPPED] LibraryDown API due to port conflict"
    fi
    
    # Start LibraryDown Worker
    echo "Starting LibraryDown Worker in background..."
    cd /root/librarydown
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    pkill -f "celery.*worker" 2>/dev/null || true
    nohup celery -A src.workers.celery_app worker --loglevel=info --concurrency=1 > /root/librarydown/worker.log 2>&1 &
    
    # Start Telegram Bot with monitor
    echo "Starting LibraryDown Telegram Bot in background..."
    cd /root/librarydown
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    pkill -f "bot_monitor.sh" 2>/dev/null || true
    nohup bash bot_monitor.sh > /root/librarydown/bot_startup.log 2>&1 &
    
    sleep 3
    
    echo "[SUCCESS] Services started in manual mode (conflict-checked)!"
}

# Stop services
stop_services() {
    echo "[STOPPING] All services..."
    
    # Check if systemd is available
    if command -v systemctl >/dev/null 2>&1; then
        # Systemd environment
        if [ -f "/etc/systemd/system/apichecker-api.service" ]; then
            sudo systemctl stop librarydown-bot librarydown-worker librarydown-api apichecker-api
        else
            sudo systemctl stop librarydown-bot librarydown-worker librarydown-api
        fi
    else
        # Termux environment - kill processes
        echo "[TERMUX] Stopping services manually..."
        pkill -f "uvicorn.*8000" 2>/dev/null || true
        pkill -f "uvicorn.*8001" 2>/dev/null || true
        pkill -f "celery.*worker" 2>/dev/null || true
        pkill -f "bot_monitor.sh" 2>/dev/null || true
        pkill -f "bot_cookie_manager" 2>/dev/null || true
    fi
    
    echo "[SUCCESS] All services stopped"
}

# Check if service is running and return status
check_service_status() {
    local service_name=$1
    local port=$2
    local process_pattern=$3
    
    if command -v systemctl >/dev/null 2>&1; then
        # Systemd environment
        if [ -f "/etc/systemd/system/${service_name}.service" ]; then
            if sudo systemctl is-active --quiet "$service_name"; then
                echo "  ✓ Running"
                return 0
            else
                echo "  ✗ Stopped"
                return 1
            fi
        else
            echo "  ⚠️  Not installed"
            return 2
        fi
    else
        # Termux environment - check for processes on port or process pattern
        if [ -n "$port" ]; then
            # Check if port is in use by a process
            if ss -tulnp 2>/dev/null | grep -q ":$port " || pgrep -f "$process_pattern" > /dev/null; then
                echo "  ✓ Running"
                return 0
            else
                echo "  ✗ Stopped"
                return 1
            fi
        else
            # Check process pattern only
            if pgrep -f "$process_pattern" > /dev/null; then
                echo "  ✓ Running"
                return 0
            else
                echo "  ✗ Stopped"
                return 1
            fi
        fi
    fi
}

# Check for port conflicts before starting services
check_port_conflicts() {
    local port=$1
    local service_name=$2
    
    if command -v ss >/dev/null 2>&1; then
        if ss -tulnp 2>/dev/null | grep -q ":$port "; then
            echo "[CONFLICT] Port $port already in use by another process for $service_name"
            ss -tulnp 2>/dev/null | grep ":$port "
            return 1
        fi
    elif command -v netstat >/dev/null 2>&1; then
        if netstat -tulnp 2>/dev/null | grep -q ":$port "; then
            echo "[CONFLICT] Port $port already in use by another process for $service_name"
            netstat -tulnp 2>/dev/null | grep ":$port "
            return 1
        fi
    fi
    return 0
}

# Show service status
show_status() {
    echo "=== Service Status ==="
    echo ""
    
    # Check API Checker status
    if [ -d "/root/apichecker" ]; then
        echo "[API Checker (port 8000)]:"
        check_service_status "apichecker-api" "8000" "uvicorn.*8000"
    else
        echo "[API Checker (port 8000)]:"
        echo "  ⚠️  Directory not found"
    fi
    
    # Check LibraryDown API status
    echo "[LibraryDown API (port 8001)]:"
    check_service_status "librarydown-api" "8001" "uvicorn.*8001"
    
    # Check LibraryDown Worker status
    echo "[LibraryDown Worker]:"
    check_service_status "librarydown-worker" "" "celery.*worker"
    
    # Check LibraryDown Bot status
    echo "[LibraryDown Bot]:"
    check_service_status "librarydown-bot" "" "bot_cookie_manager\|bot_monitor.sh"
    
    echo ""
    echo "=== Resource Usage ==="
    free -h | grep -E "Mem:|Swap:" || true
}

# Configure bot
configure_bot() {
    echo "[CONFIGURING] Telegram Bot..."
    
    if [ ! -f "$LIBRARYDOWN_DIR/.env" ]; then
        echo "[ERROR] .env file not found in librarydown directory"
        return 1
    fi
    
    echo ""
    echo "Please provide your Telegram Bot configuration:"
    echo "- Get your bot token from @BotFather on Telegram"
    echo "- Get your user ID from @userinfobot on Telegram"
    echo ""
    
    read -p "Enter your Telegram Bot Token: " bot_token
    read -p "Enter your Telegram User ID: " user_id
    
    # Update .env file
    sed -i "s/YOUR_TELEGRAM_BOT_TOKEN_HERE/$bot_token/g" "$LIBRARYDOWN_DIR/.env"
    sed -i "s/YOUR_TELEGRAM_USER_ID_HERE/$user_id/g" "$LIBRARYDOWN_DIR/.env"
    
    echo "[SUCCESS] Bot configured in .env file"
}

# Start only bot
start_bot() {
    if command -v systemctl >/dev/null 2>&1; then
        sudo systemctl start librarydown-bot
    else
        cd /root/librarydown
        pkill -f "bot_monitor.sh" 2>/dev/null || true
        nohup bash bot_monitor.sh > /root/librarydown/bot_startup.log 2>&1 &
    fi
    echo "[SUCCESS] Telegram Bot started"
}

# Stop only bot
stop_bot() {
    if command -v systemctl >/dev/null 2>&1; then
        sudo systemctl stop librarydown-bot
    else
        pkill -f "bot_monitor.sh\|bot_cookie_manager" 2>/dev/null || true
    fi
    echo "[SUCCESS] Telegram Bot stopped"
}

# Run system check
run_check() {
    echo "[CHECKING] System status..."
    cd "$LIBRARYDOWN_DIR" && source venv/bin/activate && python3 comprehensive_test.py
}

# Show logs
show_logs() {
    echo "[LOGS] Recent bot monitor log:"
    tail -20 /root/librarydown/logs/bot_monitor.log 2>/dev/null || echo "No bot logs found"
    
    echo ""
    echo "[LOGS] Recent monitor log:"
    tail -20 /root/librarydown/logs/monitor.log 2>/dev/null || echo "No monitor logs found"
}

# Run monitor
run_monitor() {
    bash /root/librarydown-monitor.sh watch
}

# Backup system
do_backup() {
    bash /root/librarydown-backup.sh backup
}

# Clean old files
do_clean() {
    bash /root/librarydown-backup.sh clean
    find /root/librarydown/logs -name "*.log" -mtime +7 -delete 2>/dev/null || true
    echo "[SUCCESS] Old logs and backups cleaned"
}

# Update system (placeholder for future updates)
do_update() {
    echo "[UPDATING] Checking for updates..."
    cd "$LIBRARYDOWN_DIR"
    git pull origin main 2>/dev/null || echo "No git repository found"
    echo "[SUCCESS] Update check completed"
}

# Test cookie upload functionality
test_upload() {
    echo "[TESTING] Cookie upload functionality..."
    cd "$LIBRARYDOWN_DIR" && source venv/bin/activate && python3 real_world_test.py
}

case "$1" in
    setup)
        show_header
        install_deps
        create_dirs
        # Create .env file if it doesn't exist
        if [ ! -f ".env" ]; then
            cp .env.example .env
            echo "[INFO] Created .env file from example"
        fi
        install_services
        configure_bot
        start_services
        echo ""
        echo "[COMPLETE] Setup finished!"
        echo "[INFO] All services are now running"
        echo "[INFO] Bot is ready to receive cookies"
        ;;
    install)
        show_header
        install_deps
        # Create .env file if it doesn't exist
        if [ ! -f ".env" ]; then
            cp .env.example .env
            echo "[INFO] Created .env file from example"
        fi
        ;;
    services)
        show_header
        create_dirs
        install_services
        ;;
    start)
        show_header
        start_services
        ;;
    stop)
        show_header
        stop_services
        ;;
    restart)
        show_header
        stop_services
        sleep 2
        start_services
        ;;
    status)
        show_header
        show_status
        ;;
    bot-config)
        show_header
        configure_bot
        ;;
    bot-start)
        show_header
        start_bot
        ;;
    bot-stop)
        show_header
        stop_bot
        ;;
    check)
        show_header
        run_check
        ;;
    monitor)
        show_header
        run_monitor
        ;;
    logs)
        show_header
        show_logs
        ;;
    backup)
        show_header
        do_backup
        ;;
    clean)
        show_header
        do_clean
        ;;
    update)
        show_header
        do_update
        ;;
    upload-test)
        show_header
        test_upload
        ;;
    *)
        show_header
        show_usage
        ;;
esac