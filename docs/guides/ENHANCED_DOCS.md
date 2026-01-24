# LibraryDown - Enhanced Documentation

## Table of Contents
- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Security Features](#security-features)
- [Performance Optimizations](#performance-optimizations)
- [Deployment Guide](#deployment-guide)
- [API Documentation](#api-documentation)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Prerequisites
- Python 3.11+
- Docker and Docker Compose (recommended)
- Redis server
- FFmpeg for media processing

### Installation Options

#### Option 1: Docker Deployment (Recommended)
```bash
# Clone repository
git clone <repository-url>
cd librarydown

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Option 2: Manual Installation
```bash
# Clone repository
git clone <repository-url>
cd librarydown

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start Redis
redis-server &

# Start services
celery -A src.workers.celery_app worker --loglevel=info &
celery -A src.workers.celery_app beat --loglevel=info &
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

## Architecture Overview

### System Components

```
┌─────────────────┐    ┌──────────────┐    ┌────────────────┐
│   FastAPI API   │────│  Celery Task │────│   Redis Cache  │
│     Server      │    │   Workers    │    │   & Broker     │
└─────────────────┘    └──────────────┘    └────────────────┘
         │                       │                   │
         ▼                       ▼                   ▼
┌─────────────────┐    ┌──────────────┐    ┌────────────────┐
│   PostgreSQL    │    │   YouTube    │    │   Media Files  │
│   Database      │    │   Downloader │    │   Storage      │
└─────────────────┘    └──────────────┘    └────────────────┘
```

### Key Modules

- **`src/api/`** - FastAPI REST endpoints and request handling
- **`src/engine/`** - Platform-specific downloaders and core logic
- **`src/workers/`** - Celery task definitions and background processing
- **`src/database/`** - Database models and session management
- **`src/utils/`** - Shared utilities (security, caching, validation)
- **`tests/`** - Unit and integration tests

## Security Features

### Input Validation
- URL format validation and sanitization
- Domain whitelist checking
- Path traversal prevention
- Suspicious pattern detection

### Security Headers
- Content Security Policy (CSP)
- X-Frame-Options protection
- XSS protection headers
- Strict Transport Security

### Rate Limiting
- IP-based rate limiting (10 requests/minute default)
- Configurable limits per endpoint
- Automatic ban for excessive requests

### Data Protection
- Temporary file cleanup
- Cookie file isolation
- Secure media serving
- Database connection encryption

## Performance Optimizations

### Caching Strategy
```python
# Metadata caching (1 hour TTL)
cache_manager.set("video_meta:url_hash", metadata, ttl=3600)

# Format information caching (30 minutes TTL)  
cache_manager.set("formats:url_hash", formats, ttl=1800)

# Download results caching (15 minutes TTL)
cache_manager.set("download_result:task_id", result, ttl=900)
```

### Database Optimizations
- Connection pooling with pre-ping verification
- Query result caching
- Index optimization for frequent queries
- Background cleanup tasks

### Resource Management
- Concurrent download limiting
- Memory usage monitoring
- Temporary file cleanup
- Database connection recycling

## Deployment Guide

### Production Deployment

#### 1. Environment Configuration
```bash
# Create production environment file
cp .env.example .env.production
# Edit .env.production with production values
```

#### 2. Docker Deployment
```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale worker=3
```

#### 3. Reverse Proxy Setup (Nginx)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /media/ {
        alias /path/to/media/;
        expires 1h;
    }
}
```

### Monitoring Setup

#### Health Checks
```bash
# API Health Check
curl http://localhost:8000/health

# Metrics Endpoint
curl http://localhost:8000/metrics
```

#### Log Monitoring
```bash
# View application logs
docker-compose logs -f api worker

# View error logs
docker-compose logs --since 1h api | grep ERROR
```

## API Documentation

### Core Endpoints

#### GET `/health`
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "service": "Universal Social Media Downloader",
  "version": "2.0.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### GET `/metrics`
System metrics and statistics.

**Response:**
```json
{
  "downloads": {
    "total": 1250,
    "successful": 1180,
    "recent_24h": 45,
    "success_rate": 94.4
  },
  "cache": {
    "enabled": true,
    "backend": "redis",
    "connected": true
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### POST `/api/v1/download`
Submit download request (Asynchronous).

**Request:**
```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "quality": "720p"
}
```

**Response:**
```json
{
  "task_id": "abc123-def456",
  "status": "queued",
  "platform": "youtube"
}
```

#### GET `/api/v1/download-sync`
Download media synchronously in one step (NEW FEATURE!).

**Request:**
```
GET /api/v1/download-sync?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&quality=720p
```

**Description:**
- **Single-step download**: Returns the media file directly without requiring a separate status check
- **Synchronous processing**: Waits for download to complete before responding
- **Direct file response**: Returns the downloaded media file as a binary response
- **Timeout consideration**: May take longer to respond for large files or slow connections

**Query Parameters:**
- `url` (required): The URL of the video to download
- `quality` (optional): Desired video quality (e.g., "720p", "480p", "audio")

**Response:**
- Binary file response with appropriate content-type
- Or JSON response with metadata if file cannot be returned directly

**Usage Examples:**
```bash
# Download YouTube video directly
curl -O "http://localhost:8000/api/v1/download-sync?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&quality=720p"

# Download as audio only
curl -O "http://localhost:8000/api/v1/download-sync?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&quality=audio"
```

**Comparison with Async Download:**

| Feature | Async Download (`/download`) | Sync Download (`/download-sync`) |
|---------|------------------------------|----------------------------------|
| Steps | 2-step process | 1-step process |
| Response | Task ID only | Direct file response |
| Speed | Fast initial response | Slower (waits for completion) |
| Large files | Better for large files | May timeout |
| User experience | Requires polling | Direct download |

#### GET `/api/v1/status/{task_id}`
Check download status (for async downloads).

**Response:**
```json
{
  "task_id": "abc123-def456",
  "status": "SUCCESS",
  "result": {
    "platform": "youtube",
    "title": "Video Title",
    "media": {
      "video": [
        {
          "url": "http://example.com/media/video.mp4",
          "quality": "720p"
        }
      ]
    }
  }
}
```

## Monitoring & Maintenance

### Performance Monitoring

#### Key Metrics to Track
- API response times
- Task processing latency
- Cache hit rates
- Database query performance
- Memory and CPU usage

#### Alerting Thresholds
- API response time > 5 seconds
- Task failure rate > 5%
- Cache miss rate > 30%
- Database connection pool utilization > 80%

### Regular Maintenance Tasks

#### Daily
```bash
# Check service status
docker-compose ps

# Review error logs
docker-compose logs --since 24h | grep ERROR

# Check disk space usage
du -sh /path/to/media/
```

#### Weekly
```bash
# Database maintenance
# Run cleanup tasks
curl -X POST http://localhost:8000/api/v1/admin/cleanup

# Update dependencies
docker-compose pull
docker-compose up -d
```

#### Monthly
```bash
# Database optimization
# Vacuum and analyze database
# Review and rotate logs
# Update SSL certificates
```

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check Docker containers
docker-compose ps

# View detailed logs
docker-compose logs api

# Check port conflicts
netstat -tulpn | grep :8000
```

#### Download Failures
```bash
# Check worker logs
docker-compose logs worker

# Verify Redis connectivity
redis-cli ping

# Check media directory permissions
ls -la /path/to/media/
```

#### Performance Issues
```bash
# Check system resources
docker stats

# Monitor cache performance
curl http://localhost:8000/metrics | jq '.cache'

# Review slow database queries
# Enable SQL logging in debug mode
```

### Debug Mode
```bash
# Enable debug logging
export DEBUG=True

# Start with verbose output
docker-compose up --build
```

## Contributing

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run linting
flake8 src/
black src/

# Run type checking
mypy src/
```

### Code Standards
- Follow PEP 8 style guidelines
- Write comprehensive docstrings
- Include unit tests for new features
- Use type hints for function signatures

---

For additional support, please check the [issues](https://github.com/yourusername/librarydown/issues) or contact the development team.