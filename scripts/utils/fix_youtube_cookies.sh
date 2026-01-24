#!/bin/bash

echo "=== Fixing YouTube Cookies Permission Issue ==="

# Create cookies directory
echo "Creating cookies directory..."
mkdir -p /opt/librarydown/src/cookies
chmod 755 /opt/librarydown/src/cookies

# Find and copy youtube_cookies.txt
if [ -f "/root/Downloads/youtube_cookies.txt" ]; then
    echo "Copying cookies from /root/Downloads/..."
    cp /root/Downloads/youtube_cookies.txt /opt/librarydown/src/cookies/
elif [ -f "/root/youtube_cookies.txt" ]; then
    echo "Copying cookies from /root/..."
    cp /root/youtube_cookies.txt /opt/librarydown/src/cookies/
else
    echo "ERROR: youtube_cookies.txt not found!"
    echo "Please upload your youtube_cookies.txt to /root/ or /root/Downloads/"
    exit 1
fi

# Set proper permissions
chmod 644 /opt/librarydown/src/cookies/youtube_cookies.txt
chown root:root /opt/librarydown/src/cookies/youtube_cookies.txt

echo "Verifying file..."
ls -la /opt/librarydown/src/cookies/youtube_cookies.txt

# Restart services
echo "Restarting services..."
systemctl restart librarydown-worker
systemctl restart librarydown-api

sleep 3

echo "Checking worker status..."
systemctl status librarydown-worker --no-pager -l | tail -20

echo ""
echo "=== Fix Complete ==="
echo "Monitor logs with: journalctl -u librarydown-worker -f"
echo "Test with: curl -X POST http://apdl.vortex-xx.biz.id/api/download -H 'Content-Type: application/json' -d '{\"url\": \"https://youtube.com/watch?v=dQw4w9WgXcQ\"}'"
