#!/bin/bash

# Copy Code Updates from Local to Production
# Untuk sync perubahan code ke VPS tanpa full redeploy

set -e

echo "========================================"
echo "Updating LibraryDown Code"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "src/main.py" ]; then
    echo "❌ ERROR: Must run from librarydown root directory"
    exit 1
fi

echo "[1/5] Copying updated code to production..."

# Copy main source files
echo "  - Copying src/ directory..."
cp -r src/* /opt/librarydown/src/

# Copy requirements if changed
if [ -f "requirements.txt" ]; then
    echo "  - Copying requirements.txt..."
    cp requirements.txt /opt/librarydown/
fi

# Copy .env if provided
if [ -f ".env" ] && [ ! -f "/opt/librarydown/.env" ]; then
    echo "  - Copying .env..."
    cp .env /opt/librarydown/
fi

echo "✓ Code copied successfully"
echo ""

# Update dependencies if requirements changed
echo "[2/5] Checking dependencies..."
cd /opt/librarydown
source venv/bin/activate
pip install -r requirements.txt --quiet
echo "✓ Dependencies up to date"
echo ""

# Restart services
echo "[3/5] Restarting API service..."
systemctl restart librarydown-api
sleep 2

echo "[4/5] Restarting Worker service..."
systemctl restart librarydown-worker
sleep 2

# Check status
echo "[5/5] Checking service status..."
echo ""

if systemctl is-active --quiet librarydown-api; then
    echo "✓ API is running"
else
    echo "❌ API has issues"
    journalctl -u librarydown-api -n 10 --no-pager
fi

if systemctl is-active --quiet librarydown-worker; then
    echo "✓ Worker is running"
else
    echo "❌ Worker has issues"
    journalctl -u librarydown-worker -n 10 --no-pager
fi

echo ""
echo "========================================"
echo "✓ Update Complete!"
echo "========================================"
echo ""
echo "Monitor logs:"
echo "  API:    journalctl -u librarydown-api -f"
echo "  Worker: journalctl -u librarydown-worker -f"
echo ""
