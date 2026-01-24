# LibraryDown Quick Reference Card

## Bot Commands
- `/start` - Welcome message
- `/upload_yt` - Upload YouTube cookies
- `/upload_ig` - Upload Instagram cookies  
- `/upload_tiktok` - Upload TikTok cookies
- `/upload_general` - Upload general cookies
- `/status` - Check service status

## Essential Commands

### Start Bot
```bash
cd /root/librarydown
source venv/bin/activate
python3 -m src.bot_cookie_manager
```

### Monitor Bot
```bash
bash bot_monitor.sh
```

### Test System
```bash
cd /root/librarydown
source venv/bin/activate
python3 comprehensive_test.py
```

### Backup System
```bash
bash /root/librarydown-backup.sh backup
```

### Check Status
```bash
bash /root/librarydown-backup.sh info
```

## Troubleshooting

### Bot Not Working?
1. Check if process is running: `pgrep -f bot_cookie_manager`
2. Check logs: `cat /root/librarydown/logs/bot_monitor.log`
3. Verify token/ID in `.env` file

### Cookie Upload Failing?
- Confirm Netscape format
- Check file extension (.txt)
- Verify you're the authorized user

### Services Down?
- API: http://localhost:8001/docs
- API Checker: http://localhost:8000/stats

## Important Locations
- Config: `/root/librarydown/.env`
- Cookies: `/opt/librarydown/cookies/`
- Logs: `/root/librarydown/logs/`
- Backup: `/root/backups/`
- Bot: `/root/librarydown/src/bot_cookie_manager.py`