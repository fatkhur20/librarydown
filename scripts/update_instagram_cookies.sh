#!/bin/bash

# Update Instagram Cookies Script
# Dijalankan setiap kali cookies perlu diupdate

set -e

echo "========================================"
echo "Updating Instagram Cookies"
echo "========================================"
echo ""

# Find cookies file
COOKIES_SOURCE=""

if [ -f "/root/Downloads/instagram_cookies.txt" ]; then
    COOKIES_SOURCE="/root/Downloads/instagram_cookies.txt"
elif [ -f "/root/instagram_cookies.txt" ]; then
    COOKIES_SOURCE="/root/instagram_cookies.txt"
elif [ -f "./instagram_cookies.txt" ]; then
    COOKIES_SOURCE="./instagram_cookies.txt"
else
    echo "❌ ERROR: instagram_cookies.txt not found!"
    echo ""
    echo "Please upload your instagram_cookies.txt to one of:"
    echo "  - /root/Downloads/"
    echo "  - /root/"
    echo "  - Current directory"
    echo ""
    echo "How to get Instagram cookies:"
    echo "1. Login to Instagram in your browser"
    echo "2. Install 'Get cookies.txt LOCALLY' extension"
    echo "3. Export cookies for instagram.com"
    echo "4. Upload to VPS"
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
cp "$COOKIES_SOURCE" /opt/librarydown/src/cookies/instagram_cookies.txt
chmod 644 /opt/librarydown/src/cookies/instagram_cookies.txt

# Verify
echo "[3/4] Verifying file..."
if [ -f "/opt/librarydown/src/cookies/instagram_cookies.txt" ]; then
    FILE_SIZE=$(stat -c%s /opt/librarydown/src/cookies/instagram_cookies.txt 2>/dev/null || stat -f%z /opt/librarydown/src/cookies/instagram_cookies.txt)
    echo "✓ Cookies file installed ($FILE_SIZE bytes)"
    ls -lh /opt/librarydown/src/cookies/instagram_cookies.txt
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
echo "✓ Instagram Cookies Updated!"
echo "========================================"
echo ""
echo "Test download with:"
echo "curl -X POST http://localhost:8001/download \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"url\": \"https://www.instagram.com/p/XXXXXXXXX/\"}'"
echo ""
echo "Monitor logs:"
echo "journalctl -u librarydown-worker -f"
echo ""
