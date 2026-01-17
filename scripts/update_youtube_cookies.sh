#!/bin/bash

# Update YouTube Cookies Script
# Dijalankan setiap kali cookies perlu diupdate

set -e

echo "========================================"
echo "Updating YouTube Cookies"
echo "========================================"
echo ""

# Find cookies file
COOKIES_SOURCE=""

if [ -f "/root/Downloads/youtube_cookies.txt" ]; then
    COOKIES_SOURCE="/root/Downloads/youtube_cookies.txt"
elif [ -f "/root/youtube_cookies.txt" ]; then
    COOKIES_SOURCE="/root/youtube_cookies.txt"
elif [ -f "./youtube_cookies.txt" ]; then
    COOKIES_SOURCE="./youtube_cookies.txt"
else
    echo "❌ ERROR: youtube_cookies.txt not found!"
    echo ""
    echo "Please upload your youtube_cookies.txt to one of:"
    echo "  - /root/Downloads/"
    echo "  - /root/"
    echo "  - Current directory"
    echo ""
    exit 1
fi

echo "✓ Found cookies at: $COOKIES_SOURCE"
echo ""

# Create cookies directory if not exists
echo "[1/4] Creating cookies directory..."
mkdir -p /opt/librarydown/src/cookies
chmod 755 /opt/librarydown/src/cookies

# Copy cookies file
echo "[2/4] Copying cookies file..."
cp "$COOKIES_SOURCE" /opt/librarydown/src/cookies/youtube_cookies.txt
chmod 644 /opt/librarydown/src/cookies/youtube_cookies.txt

# Verify
echo "[3/4] Verifying file..."
if [ -f "/opt/librarydown/src/cookies/youtube_cookies.txt" ]; then
    FILE_SIZE=$(stat -f%z /opt/librarydown/src/cookies/youtube_cookies.txt 2>/dev/null || stat -c%s /opt/librarydown/src/cookies/youtube_cookies.txt)
    echo "✓ Cookies file installed ($FILE_SIZE bytes)"
    ls -lh /opt/librarydown/src/cookies/youtube_cookies.txt
else
    echo "❌ Failed to copy cookies file"
    exit 1
fi

# Restart worker
echo ""
echo "[4/4] Restarting worker..."
systemctl restart librarydown-worker

sleep 2

# Check status
echo ""
echo "Checking worker status..."
if systemctl is-active --quiet librarydown-worker; then
    echo "✓ Worker is running"
else
    echo "⚠️  Worker may have issues, checking logs..."
    journalctl -u librarydown-worker -n 20 --no-pager
fi

echo ""
echo "========================================"
echo "✓ YouTube Cookies Updated!"
echo "========================================"
echo ""
echo "Test download with:"
echo "curl -X POST http://localhost:8001/api/download \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"url\": \"https://youtube.com/watch?v=dQw4w9WgXcQ\"}'"
echo ""
echo "Monitor logs:"
echo "journalctl -u librarydown-worker -f"
echo ""
