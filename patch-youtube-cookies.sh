#!/bin/bash

# Patch script to add YouTube cookies support to youtube.py

set -e

echo "=========================================="
echo "  YouTube Cookies Support - Patch Script"
echo "=========================================="
echo ""

YOUTUBE_PY="/opt/librarydown/src/engine/platforms/youtube.py"

# Check if file exists
if [ ! -f "$YOUTUBE_PY" ]; then
    echo "ERROR: File not found: $YOUTUBE_PY"
    exit 1
fi

# Backup original file
echo "[1/4] Backing up original file..."
cp "$YOUTUBE_PY" "${YOUTUBE_PY}.backup.$(date +%Y%m%d_%H%M%S)"
echo "✓ Backup created"

# Patch 1: Add cookies to get_formats function (around line 31)
echo "[2/4] Patching get_formats function..."
sed -i "/^            ydl_opts = {$/,/^            }$/ {
    /^            }$/a\\
\\
            # Add cookies file if exists\\
            cookies_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'cookies', 'youtube_cookies.txt')\\
            if os.path.exists(cookies_path):\\
                ydl_opts['cookiefile'] = cookies_path\\
                logger.info(f\"[{self.platform}] Using cookies from: {cookies_path}\")
}" "$YOUTUBE_PY"
echo "✓ get_formats patched"

# Patch 2: Add cookies to download function metadata extraction (around line 157)
echo "[3/4] Patching download function (metadata)..."
sed -i "/^            ydl_opts_info = {$/,/^            }$/ {
    /^            }$/a\\
\\
            # Add cookies file if exists\\
            cookies_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'cookies', 'youtube_cookies.txt')\\
            if os.path.exists(cookies_path):\\
                ydl_opts_info['cookiefile'] = cookies_path\\
                logger.info(f\"[{self.platform}] Using cookies for download\")
}" "$YOUTUBE_PY"
echo "✓ Metadata extraction patched"

# Patch 3: Add cookies to actual download loop (around line 218)
echo "[4/4] Patching download loop..."
sed -i "/logger.info(f\"\[{self.platform}\] Downloading {download_info\['type'\]}...\")$/a\\
\\
                # Add cookies to download options\\
                if os.path.exists(cookies_path):\\
                    download_info['opts']['cookiefile'] = cookies_path
" "$YOUTUBE_PY"
echo "✓ Download loop patched"

echo ""
echo "=========================================="
echo "  Patch Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Restart services:"
echo "     systemctl restart librarydown-worker"
echo "     systemctl restart librarydown-api"
echo ""
echo "  2. Test YouTube download"
echo ""
echo "Note: Original file backed up at:"
echo "  ${YOUTUBE_PY}.backup.*"
echo ""
