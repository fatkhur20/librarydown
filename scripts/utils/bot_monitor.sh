#!/bin/bash
# Bot Monitor and Auto-Restart Script for Termux
# This script monitors the Telegram bot and restarts it if it crashes

BOT_PID_FILE="/tmp/librarydown_bot.pid"
LOG_FILE="/root/librarydown/logs/bot_monitor.log"
BOT_DIR="/root/librarydown"

# Create logs directory if it doesn't exist
mkdir -p "$BOT_DIR/logs"

# Function to start the bot
start_bot() {
    echo "$(date): Starting LibraryDown Telegram Bot..." >> "$LOG_FILE"
    
    # Activate virtual environment and start bot in background
    cd "$BOT_DIR"
    source venv/bin/activate
    python3 -m src.bot_cookie_manager > /dev/null 2>&1 &
    
    # Save the PID
    echo $! > "$BOT_PID_FILE"
    
    echo "$(date): Bot started with PID $(cat $BOT_PID_FILE)" >> "$LOG_FILE"
}

# Function to check if bot is running
is_bot_running() {
    if [ -f "$BOT_PID_FILE" ]; then
        PID=$(cat "$BOT_PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
            # PID file exists but process is not running
            rm -f "$BOT_PID_FILE"
            return 1
        fi
    else
        return 1
    fi
}

# Main monitoring loop
echo "$(date): Bot monitor started" >> "$LOG_FILE"

while true; do
    if is_bot_running; then
        # Bot is running, continue monitoring
        sleep 30
    else
        # Bot is not running, restart it
        echo "$(date): Bot is not running, restarting..." >> "$LOG_FILE"
        start_bot
        
        # Wait a bit before checking again
        sleep 10
    fi
    
    # Check if we should exit (optional signal file)
    if [ -f "/tmp/stop_bot_monitor" ]; then
        echo "$(date): Stop signal received, exiting monitor" >> "$LOG_FILE"
        break
    fi
done