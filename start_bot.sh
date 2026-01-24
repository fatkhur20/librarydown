#!/bin/bash

# LibraryDown Telegram Bot Startup Script
# This script starts the Telegram bot for direct video downloads

set -e

echo "🚀 Starting LibraryDown Telegram Bot..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running in virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_status "Activating virtual environment..."
    if [ -d "venv" ]; then
        source venv/bin/activate
        print_success "Virtual environment activated"
    else
        print_error "Virtual environment not found. Please run setup first."
        exit 1
    fi
fi

# Check if required environment variables are set
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
    else
        print_error "TELEGRAM_BOT_TOKEN environment variable not set and .env file not found"
        exit 1
    fi
fi

# Check if bot token is set
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" = "your_bot_token_here" ]; then
    print_error "TELEGRAM_BOT_TOKEN is not properly configured in .env file"
    print_warning "Please update your .env file with a valid bot token from @BotFather"
    exit 1
fi

print_status "Starting Telegram bot..."
print_status "Bot will listen for video download requests..."

# Start the bot
python -u src/bot_downloader.py

print_success "Telegram bot started successfully!"
print_status "Bot is now listening for messages..."
print_status "Send /start to your bot to begin using it"