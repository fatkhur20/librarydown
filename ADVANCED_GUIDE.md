# LibraryDown - Advanced Features Guide

This document covers the advanced features and capabilities of the LibraryDown system with Telegram bot integration.

## Table of Contents
1. [Cookie Validation & Monitoring](#cookie-validation--monitoring)
2. [Batch Operations](#batch-operations)
3. [Performance Optimization](#performance-optimization)
4. [Troubleshooting Guide](#troubleshooting-guide)
5. [Best Practices](#best-practices)

## Cookie Validation & Monitoring

### Scheduled Cookie Checks
The system includes automated cookie validation to ensure cookies remain functional:

- **check_cookies.py** - Validates cookie expiration and format
- **Monitoring script** - Can run periodic checks
- **Telegram alerts** - Notifies when cookies expire

### Running Cookie Validation
```bash
# Check specific cookie file
python3 check_cookies.py /opt/librarydown/cookies/youtube_cookies.txt

# Check all cookies and generate report
python3 check_cookies.py --check-all

# Set up scheduled checks (cron example)
# Run daily at 9 AM to check cookies
0 9 * * * cd /root/librarydown && source venv/bin/activate && python3 check_cookies.py --check-all
```

### Auto-Detection Capabilities
- Platform detection from cookie domains
- Automatic file naming based on platform
- Smart fallback to general cookies

## Batch Operations

### Batch Upload
The batch upload feature allows uploading multiple cookies at once:

```bash
# Upload all cookies from a directory
bash librarydown-batch.sh upload-dir /path/to/cookie/files/

# The system will auto-detect platforms and rename files appropriately
```

### Backup & Restore
```bash
# Backup all cookies
bash librarydown-batch.sh backup-all

# List cookie files
bash librarydown-batch.sh list

# Validate all cookies
bash librarydown-batch.sh validate-all
```

## Performance Optimization

### Termux-Specific Optimizations
- Memory-efficient processes
- Single worker configuration
- Optimized resource limits

### Monitoring Resources
```bash
# Check current memory usage
free -h

# Monitor running processes
ps aux | grep -E "(librarydown|bot|uvicorn|celery)"

# Check logs for performance issues
tail -f /root/librarydown/logs/bot_monitor.log
```

### Logging Strategy
- Structured logging in `/root/librarydown/logs/`
- Monitor logs for debugging
- Alert logs for critical issues

## Troubleshooting Guide

### Common Issues & Solutions

#### Bot Not Responding
1. Check if bot process is running:
   ```bash
   pgrep -f bot_cookie_manager
   ```
2. Check logs:
   ```bash
   tail -n 20 /root/librarydown/logs/bot_monitor.log
   ```
3. Restart bot manually:
   ```bash
   cd /root/librarydown && source venv/bin/activate && python3 -m src.bot_cookie_manager
   ```

#### Cookie Upload Fails
1. Verify cookie format:
   ```bash
   python3 check_cookies.py /path/to/your/cookies.txt
   ```
2. Check file permissions:
   ```bash
   ls -la /opt/librarydown/cookies/
   ```
3. Validate Netscape format (7 tab-separated fields)

#### Services Not Responding
1. Check API status:
   ```bash
   curl -s http://localhost:8001/docs | head -10
   curl -s http://localhost:8000/stats | head -10
   ```
2. Verify processes are running:
   ```bash
   pgrep -f "uvicorn.*8001"  # LibraryDown API
   pgrep -f "uvicorn.*8000"  # API Checker
   ```

#### Memory Issues
1. Monitor usage:
   ```bash
   free -h
   ```
2. Reduce concurrency in `.env`:
   ```
   CELERY_WORKER_CONCURRENCY=1
   MAX_CONCURRENT_DOWNLOADS=1
   ```

### Debug Commands
```bash
# Check overall system status
bash librarydown-monitor.sh status

# Run comprehensive test
python3 comprehensive_test.py

# Check cookie validity
python3 check_cookies.py --check-all

# Monitor services
bash librarydown-monitor.sh watch
```

## Best Practices

### Security
- Keep bot token secret
- Only authorized user ID can interact with bot
- Regular cookie rotation
- Monitor access logs

### Maintenance
- Regular cookie updates (before expiration)
- Periodic backup of cookies
- Monitor system resources
- Update bot when needed

### Usage Tips
- Use specific commands (`/upload_yt`, `/upload_ig`) for precise file naming
- Verify cookie format before upload
- Monitor cookie validity regularly
- Keep backup copies of working cookies

### Performance Tips
- Limit concurrent downloads in Termux
- Monitor memory usage
- Use the monitor script to catch issues early
- Schedule cookie checks during off-peak hours

## Quick Reference

| Feature | Command |
|---------|---------|
| Start bot monitor | `bash bot_monitor.sh` |
| Check cookie validity | `python3 check_cookies.py --check-all` |
| Batch upload | `bash librarydown-batch.sh upload-dir /path/` |
| Backup cookies | `bash librarydown-batch.sh backup-all` |
| System monitoring | `bash librarydown-monitor.sh status` |
| Run tests | `python3 comprehensive_test.py` |

## Support Commands

```bash
# Get system status
bash librarydown-monitor.sh status

# Check all cookies
python3 check_cookies.py --check-all

# Validate specific file
python3 check_cookies.py /opt/librarydown/cookies/youtube_cookies.txt

# List all cookie files
bash librarydown-batch.sh list

# Run full diagnostic
python3 comprehensive_test.py
```