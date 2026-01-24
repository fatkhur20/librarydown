# LibraryDown Troubleshooting Guide

This guide provides solutions for common issues and troubleshooting steps for the LibraryDown application.

## Table of Contents
1. [General Issues](#general-issues)
2. [API Issues](#api-issues)
3. [Bot Issues](#bot-issues)
4. [Download Issues](#download-issues)
5. [Performance Issues](#performance-issues)
6. [Security Issues](#security-issues)
7. [System Issues](#system-issues)
8. [Development Issues](#development-issues)

## General Issues

### Application won't start
**Symptoms**: 
- Server fails to start
- Error messages during startup

**Solutions**:
1. Check if all required environment variables are set:
   ```bash
   echo $TELEGRAM_BOT_TOKEN
   echo $TELEGRAM_USER_ID
   ```

2. Verify that the `.env` file exists and contains all required variables:
   ```bash
   cat .env
   ```

3. Check if all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

4. Ensure Redis and database services are running:
   ```bash
   systemctl status redis-server
   systemctl status postgresql  # or your database service
   ```

### Environment variables not loaded
**Symptoms**:
- "Bot token not configured" errors
- Missing API keys

**Solutions**:
1. Make sure `.env` file is in the project root directory
2. Verify the format of your `.env` file:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_USER_ID=your_user_id_here
   REDIS_URL=redis://localhost:6379/0
   DATABASE_URL=postgresql://user:password@localhost/dbname
   ```
3. Restart the application after modifying `.env`

## API Issues

### API returns 400 Bad Request
**Common causes**:
- Invalid URL format
- Unsupported platform
- Malformed request body

**Solutions**:
1. Verify the URL is properly formatted with protocol:
   - ❌ `youtube.com/watch?v=xxx` 
   - ✅ `https://youtube.com/watch?v=xxx`

2. Check if the platform is supported:
   ```bash
   curl -X POST http://localhost:8001/api/v1/download \
     -H "Content-Type: application/json" \
     -d '{"url": "https://unsupported-site.com/video"}'
   ```
   This should return a clear unsupported platform message.

### API returns 429 Too Many Requests
**Symptoms**: Rate limit exceeded errors

**Solutions**:
1. Default rate limits:
   - General endpoints: 10 requests per minute
   - Download-sync: 5 requests per minute
   - Format checking: 20 requests per minute

2. Implement exponential backoff in your client:
   ```python
   import time
   
   def make_request_with_backoff(url, max_retries=3):
       for attempt in range(max_retries):
           response = requests.get(url)
           if response.status_code != 429:
               return response
           
           wait_time = (2 ** attempt) + 1  # 1, 3, 7 seconds
           time.sleep(wait_time)
       
       return response
   ```

### Download tasks stuck in PENDING status
**Symptoms**: 
- Status remains PENDING indefinitely
- No progress updates

**Solutions**:
1. Check if Celery workers are running:
   ```bash
   # Check for running workers
   ps aux | grep celery
   
   # Start workers if not running
   celery -A src.workers.celery_app worker --loglevel=info
   ```

2. Check worker logs for errors:
   ```bash
   tail -f logs/worker.log
   ```

3. Verify Redis connection:
   ```bash
   redis-cli ping
   ```

### Synchronous download hangs
**Symptoms**: 
- `/download-sync` endpoint takes too long
- Timeout errors

**Solutions**:
1. For large files, consider using the async endpoints instead
2. Check media folder permissions:
   ```bash
   ls -la media/
   chmod 755 media/
   ```

## Bot Issues

### Bot doesn't respond to messages
**Symptoms**:
- Bot online but ignores messages
- No download responses

**Solutions**:
1. Check bot token validity:
   ```bash
   curl "https://api.telegram.org/botYOUR_TOKEN/getMe"
   ```

2. Verify webhook is not set (using polling method):
   ```bash
   curl "https://api.telegram.org/botYOUR_TOKEN/deleteWebhook"
   ```

3. Check bot logs:
   ```bash
   tail -f logs/bot.log
   ```

### Bot rejects URLs
**Symptoms**:
- "Unsupported platform" for valid URLs
- Security validation errors

**Solutions**:
1. Verify the URL format includes protocol:
   - ❌ `tiktok.com/@username/video/xxx`
   - ✅ `https://tiktok.com/@username/video/xxx`

2. Check security validation:
   ```python
   from src.utils.security import security_validator
   is_valid, error = security_validator.validate_url("your_url_here")
   print(f"Valid: {is_valid}, Error: {error}")
   ```

### Bot download fails with "Worker crashed" 
**Symptoms**:
- Download starts but fails with worker crash message

**Solutions**:
1. Check worker logs for specific errors:
   ```bash
   tail -f logs/worker.log
   ```

2. Restart Celery workers:
   ```bash
   pkill -f celery
   celery -A src.workers.celery_app worker --loglevel=info
   ```

3. Increase worker resources if dealing with large files

## Download Issues

### Downloads fail for specific platforms
**Symptoms**:
- Consistent failures for certain platforms
- Platform-specific errors

**Solutions**:
1. Update yt-dlp to the latest version:
   ```bash
   pip install --upgrade yt-dlp
   ```

2. Check for platform-specific requirements:
   - YouTube: May need cookies for age-restricted content
   - Instagram: Login may be required for private accounts
   - TikTok: Some videos may be region-restricted

3. Add cookies if required:
   - Place cookies in `src/cookies/` directory
   - Use browser extensions like "Get cookies.txt" to export cookies

### Audio-only downloads fail
**Symptoms**:
- Audio quality option doesn't work
- Video downloaded instead of audio

**Solutions**:
1. Verify quality parameter format:
   - ✅ `quality="audio"`
   - ❌ `quality="audio_only"`

2. Check if the platform supports audio-only:
   - SoundCloud: ✅ Supported
   - YouTube: ✅ Supported
   - TikTok: ⚠️ May vary
   - Instagram: ⚠️ Limited support

### Downloaded files not accessible
**Symptoms**:
- Files created but can't be opened
- Corrupted downloads

**Solutions**:
1. Check media folder permissions:
   ```bash
   chmod -R 755 media/
   ```

2. Verify disk space:
   ```bash
   df -h
   ```

3. Check file integrity:
   ```bash
   ls -la media/
   file media/downloaded_file.*
   ```

## Performance Issues

### Slow download speeds
**Symptoms**:
- Downloads taking much longer than expected
- High CPU/memory usage

**Solutions**:
1. Check internet bandwidth:
   ```bash
   curl -s https://speedtest.tele2.net/1KB.zip -o /dev/null
   ```

2. Optimize concurrent downloads:
   - Reduce Celery worker concurrency if system is overloaded
   - Adjust in `src/workers/celery_app.py`

3. Check system resources:
   ```bash
   htop
   free -h
   ```

### High memory usage
**Symptoms**:
- Application consuming too much RAM
- System slowdowns

**Solutions**:
1. Monitor memory usage with the health endpoint:
   ```bash
   curl http://localhost:8001/api/v1/health
   ```

2. Implement periodic cleanup of old files:
   ```bash
   # Remove files older than 7 days
   find media/ -type f -mtime +7 -delete
   ```

3. Adjust caching settings in configuration

### Queue buildup
**Symptoms**:
- Tasks queuing up without processing
- High queue size reported in metrics

**Solutions**:
1. Check if workers are running and healthy:
   ```bash
   celery -A src.workers.celery_app inspect active
   ```

2. Scale up worker count if needed:
   ```bash
   # Start multiple workers
   celery -A src.workers.celery_app worker --concurrency=4
   ```

3. Check for failed tasks:
   ```bash
   celery -A src.workers.celery_app inspect reserved
   ```

## Security Issues

### Rate limiting too restrictive
**Symptoms**:
- Legitimate requests being blocked
- Frequent 429 errors

**Solutions**:
1. Adjust rate limits in configuration:
   - Modify `RATE_LIMIT_PER_MINUTE` in settings
   - Consider implementing sliding window limits

2. Check for accidental repeated requests
3. Verify no automated scripts are making too many requests

### IP blocking issues
**Symptoms**:
- Legitimate users getting blocked
- Access denied errors

**Solutions**:
1. Check firewall status:
   ```python
   from src.utils.firewall import firewall
   print(firewall.get_firewall_stats())
   ```

2. Unblocks IPs if needed:
   ```python
   firewall.unblock_ip("blocked_ip_address")
   ```

3. Adjust security thresholds in security configuration

### Invalid URL errors
**Symptoms**:
- Valid URLs being flagged as invalid
- Security validation blocking legitimate requests

**Solutions**:
1. Check security validation logs
2. Verify URL format includes proper protocol
3. Check for any special characters that might trigger security filters

## System Issues

### Database connection errors
**Symptoms**:
- "Database connection failed" errors
- 500 errors on database-dependent endpoints

**Solutions**:
1. Verify database service is running:
   ```bash
   systemctl status postgresql  # or mysql/mariadb
   ```

2. Check database connection string in `.env`:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/dbname
   ```

3. Test database connection:
   ```bash
   psql -h localhost -U username -d dbname
   ```

### Redis connection errors
**Symptoms**:
- Cache misses consistently high
- Task queuing not working

**Solutions**:
1. Check if Redis is running:
   ```bash
   systemctl status redis-server
   ```

2. Test Redis connection:
   ```bash
   redis-cli ping
   ```

3. Verify Redis URL in `.env`:
   ```
   REDIS_URL=redis://localhost:6379/0
   ```

### Permission errors
**Symptoms**:
- "Permission denied" errors
- Unable to write files

**Solutions**:
1. Set proper permissions:
   ```bash
   chmod -R 755 media/
   chmod -R 755 logs/
   chmod -R 755 data/
   ```

2. Verify the application is running under the correct user

### Disk space issues
**Symptoms**:
- "No space left on device" errors
- Downloads failing mysteriously

**Solutions**:
1. Check available disk space:
   ```bash
   df -h
   ```

2. Clean up old files:
   ```bash
   # Remove files older than 7 days
   find media/ -type f -mtime +7 -delete
   find logs/ -type f -mtime +30 -delete
   ```

3. Set up automatic cleanup scripts

## Development Issues

### Import errors during development
**Symptoms**:
- ModuleNotFoundError for internal packages
- Import errors when running tests

**Solutions**:
1. Add src to Python path:
   ```bash
   export PYTHONPATH="${PYTHONPATH}:/path/to/librarydown/src"
   ```

2. Install in development mode:
   ```bash
   pip install -e .
   ```

3. Verify project structure matches imports

### Test failures
**Symptoms**:
- Unit tests failing unexpectedly
- Integration tests failing

**Solutions**:
1. Run tests with verbose output:
   ```bash
   pytest -v
   ```

2. Check test dependencies:
   ```bash
   pip install pytest pytest-asyncio httpx
   ```

3. Verify test configuration and mocks

### Debugging in development
**Solutions**:
1. Enable debug mode in `.env`:
   ```
   DEBUG=True
   ```

2. Check detailed logs:
   ```bash
   tail -f logs/app.log
   ```

3. Use debugging tools:
   ```python
   import pdb; pdb.set_trace()  # Python debugger
   ```

## Getting Help

If you can't resolve an issue:

1. Check the logs first:
   ```bash
   tail -f logs/app.log
   tail -f logs/worker.log
   tail -f logs/bot.log
   ```

2. Verify your environment matches the [requirements](../requirements.txt)

3. Search the [documentation](api_documentation.md) for specific endpoints

4. If the issue persists, create an issue in the repository with:
   - Detailed error messages
   - Steps to reproduce
   - Environment information (OS, Python version, etc.)
   - Relevant log entries

## Quick Checks

Before deep troubleshooting, verify:

- [ ] `.env` file exists and is properly configured
- [ ] All services (Redis, Database) are running
- [ ] Dependencies are installed (`pip install -r requirements.txt`)
- [ ] Media directory has proper permissions
- [ ] Logs don't show obvious errors
- [ ] Network connectivity is working
- [ ] Disk space is available

For emergency restarts:
```bash
# Restart all services
sudo systemctl restart redis-server
sudo systemctl restart librarydown-api
sudo systemctl restart librarydown-worker
sudo systemctl restart librarydown-bot
```