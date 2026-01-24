# LibraryDown + Telegram Bot Integration Guide

This document explains how to use and maintain the LibraryDown system with Telegram bot integration for cookie management.

## Table of Contents
1. [Overview](#overview)
2. [Setup](#setup)
3. [Bot Commands](#bot-commands)
4. [Troubleshooting](#troubleshooting)
5. [Maintenance](#maintenance)

## Overview

The LibraryDown system consists of:
- **LibraryDown API**: Social media downloader (runs on port 8001)
- **API Checker**: Utility API (runs on port 8000) 
- **Telegram Bot**: Cookie management interface
- **Cookie Management**: Automated cookie deployment system

## Setup

### Prerequisites
- Telegram Bot Token (from @BotFather)
- Your Telegram User ID (from @userinfobot)

### Initial Configuration
1. Edit the .env file:
   ```bash
   nano /root/librarydown/.env
   ```
2. Update TELEGRAM_BOT_TOKEN and TELEGRAM_USER_ID
3. Save the file

### Starting Services
```bash
# Start individual services
cd /root/librarydown
source venv/bin/activate
python3 -m src.bot_cookie_manager  # Bot (run in background)

# Or use the monitor script to keep bot running
bash bot_monitor.sh
```

## Bot Commands

### Available Commands
- `/start` - Show welcome message and available commands
- `/upload_yt` - Upload YouTube cookies
- `/upload_ig` - Upload Instagram cookies
- `/upload_tiktok` - Upload TikTok cookies
- `/upload_general` - Upload general cookies
- `/status` - Check service status

### Using Cookie Upload
1. Send `/upload_yt` (or appropriate command) to the bot
2. Send a Netscape-format cookie file (.txt extension)
3. Bot will validate, deploy, and restart services automatically

### Cookie File Format
Cookie files must be in Netscape format:
```
.domain.com	TRUE	/	FALSE	2147483647	COOKIE_NAME	COOKIE_VALUE
```

## Troubleshooting

### Common Issues

#### Bot Not Responding
- Check if bot process is running: `pgrep -f bot_cookie_manager`
- Check internet connectivity
- Verify bot token is correct
- Check logs: `tail -f /root/librarydown/logs/bot_monitor.log`

#### Cookie Upload Fails
- Verify file is in Netscape format
- Check file isn't corrupted
- Ensure file has .txt extension
- Verify you're authorized (whitelist check)

#### Service Restart Fails
- In Termux, services aren't managed by systemd
- Manual restart required for librarydown services

#### Invalid Cookie Format
- Check cookie file follows Netscape format
- Ensure proper tab separation
- Verify timestamp is numeric

### Debugging Steps
1. Check bot logs: `cat /root/librarydown/logs/bot_monitor.log`
2. Test cookie validation manually:
   ```bash
   cd /root/librarydown
   source venv/bin/activate
   python3 -c "from src.bot_cookie_manager import validate_netscape_cookies; print(validate_netscape_cookies('.example.com	TRUE	/	FALSE	2147483647	test	value'))"
   ```
3. Verify environment variables:
   ```bash
   python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('TELEGRAM_BOT_TOKEN')); print(os.getenv('TELEGRAM_USER_ID'))"
   ```

### Termux-Specific Notes
- No systemd support - services run manually
- Limited memory - single worker processes
- Background processes may stop when Termux goes to sleep
- Use the bot_monitor.sh script to maintain bot availability

## Maintenance

### Regular Tasks
- Monitor bot logs for errors
- Check cookie validity periodically
- Verify services are responsive
- Clean old backup files

### Backup and Recovery
- Create backups using: `bash /root/librarydown-backup.sh backup`
- List backups: `bash /root/librarydown-backup.sh list`
- Restore: `bash /root/librarydown-backup.sh restore <backup-file>`
- Clean old backups: `bash /root/librarydown-backup.sh clean`

### Service Management
- To restart bot: Kill the process and restart manually
- Monitor resource usage: `free -h`
- Check running processes: `ps aux | grep -E "(bot|librarydown|uvicorn|celery)"`

### Security
- Bot only responds to whitelisted user ID
- Cookie files stored securely with 644 permissions
- Validate cookie format before deployment

## Quick Commands Reference

```bash
# Start bot monitor
cd /root/librarydown && bash bot_monitor.sh

# Test bot functionality
cd /root/librarydown && source venv/bin/activate && python3 integration_test.py

# Check service status
python3 -c "
import subprocess
import shutil
has_systemctl = shutil.which('systemctl') is not None
if not has_systemctl:
    api_ps = subprocess.run(['pgrep', '-f', 'uvicorn.*8001'], capture_output=True, text=True)
    worker_ps = subprocess.run(['pgrep', '-f', 'celery.*worker'], capture_output=True, text=True)
    print('API Service:', 'running' if api_ps.returncode == 0 else 'stopped')
    print('Worker Service:', 'running' if worker_ps.returncode == 0 else 'stopped')
"

# Create backup
bash /root/librarydown-backup.sh backup
```

## Support

If you encounter issues:
1. Check the troubleshooting section
2. Verify your bot token and user ID
3. Test with simple cookie format
4. Consult the logs
5. Restart services if needed