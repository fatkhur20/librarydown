#!/bin/bash

# Quick Health Check Script
# Cek status semua komponen LibraryDown

echo "========================================"
echo "LibraryDown Health Check"
echo "========================================"
echo ""

# Check Redis
echo "📊 Redis Status:"
if systemctl is-active --quiet redis; then
    echo "  ✓ Running"
    redis-cli ping &>/dev/null && echo "  ✓ Responding to ping" || echo "  ⚠️  Not responding"
else
    echo "  ❌ Not running"
fi
echo ""

# Check API Service
echo "🌐 API Service:"
if systemctl is-active --quiet librarydown-api; then
    echo "  ✓ Running"
    API_PORT=$(curl -s http://localhost:8001/health 2>/dev/null && echo "  ✓ Responding on port 8001" || echo "  ⚠️  Not responding")
else
    echo "  ❌ Not running"
    echo "  Last 5 log lines:"
    journalctl -u librarydown-api -n 5 --no-pager | sed 's/^/    /'
fi
echo ""

# Check Worker Service
echo "👷 Worker Service:"
if systemctl is-active --quiet librarydown-worker; then
    echo "  ✓ Running"
    WORKER_PROCESSES=$(ps aux | grep -c "[c]elery.*worker" || echo "0")
    echo "  ✓ Celery processes: $WORKER_PROCESSES"
else
    echo "  ❌ Not running"
    echo "  Last 5 log lines:"
    journalctl -u librarydown-worker -n 5 --no-pager | sed 's/^/    /'
fi
echo ""

# Check ffmpeg
echo "🎬 ffmpeg:"
if command -v ffmpeg &> /dev/null; then
    FFMPEG_VERSION=$(ffmpeg -version 2>&1 | head -1 | cut -d' ' -f3)
    echo "  ✓ Installed (version $FFMPEG_VERSION)"
else
    echo "  ❌ Not installed"
fi
echo ""

# Check cookies
echo "🍪 YouTube Cookies:"
if [ -f "/opt/librarydown/src/cookies/youtube_cookies.txt" ]; then
    FILE_SIZE=$(stat -c%s /opt/librarydown/src/cookies/youtube_cookies.txt 2>/dev/null || stat -f%z /opt/librarydown/src/cookies/youtube_cookies.txt)
    echo "  ✓ Present ($FILE_SIZE bytes)"
else
    echo "  ⚠️  Not found (YouTube downloads may fail)"
fi
echo ""

# Check disk space
echo "💾 Disk Space:"
MEDIA_DIR="/opt/librarydown/media"
if [ -d "$MEDIA_DIR" ]; then
    DISK_USAGE=$(du -sh "$MEDIA_DIR" 2>/dev/null | cut -f1)
    echo "  Media directory: $DISK_USAGE"
fi
DISK_FREE=$(df -h /opt | tail -1 | awk '{print $4}')
echo "  Free space: $DISK_FREE"
echo ""

# Check memory
echo "🧠 Memory Usage:"
FREE_MEM=$(free -h | awk '/^Mem:/ {print $7}')
echo "  Available: $FREE_MEM"
echo ""

# Summary
echo "========================================"
API_STATUS=$(systemctl is-active librarydown-api)
WORKER_STATUS=$(systemctl is-active librarydown-worker)
REDIS_STATUS=$(systemctl is-active redis)

if [ "$API_STATUS" == "active" ] && [ "$WORKER_STATUS" == "active" ] && [ "$REDIS_STATUS" == "active" ]; then
    echo "✅ All systems operational"
else
    echo "⚠️  Some systems need attention:"
    [ "$REDIS_STATUS" != "active" ] && echo "  - Redis is down"
    [ "$API_STATUS" != "active" ] && echo "  - API is down"
    [ "$WORKER_STATUS" != "active" ] && echo "  - Worker is down"
fi
echo "========================================"
echo ""
