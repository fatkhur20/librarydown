# LibraryDown API Documentation

LibraryDown is a universal social media video downloader API that supports multiple platforms including TikTok, YouTube, Instagram, Twitter, and many more.

## Base URL

```
https://your-librarydown-instance.com/api/v1
```

Or for local development:
```
http://localhost:8001/api/v1
```

## Authentication

The API does not require authentication for basic operations, but rate limiting is applied per IP address.

## Rate Limits

- Standard endpoints: 10 requests per minute
- Download-sync endpoint: 5 requests per minute
- Format checking: 20 requests per minute

## Supported Platforms

- **TikTok** (tiktok.com, vt.tiktok.com)
- **YouTube** (youtube.com, youtu.be)
- **Instagram** (instagram.com)
- **Twitter/X** (twitter.com, x.com)
- **Reddit** (reddit.com, redd.it)
- **SoundCloud** (soundcloud.com)
- **Dailymotion** (dailymotion.com, dai.ly)
- **Twitch** (twitch.tv)
- **Vimeo** (vimeo.com)
- **Facebook** (facebook.com, fb.watch)
- **Bilibili** (bilibili.com)
- **LinkedIn** (linkedin.com)
- **Pinterest** (pinterest.com)

## Endpoints

### 1. Submit Download Task (POST)

Submit a URL for asynchronous download.

#### Endpoint
```
POST /api/v1/download
```

#### Headers
```
Content-Type: application/json
```

#### Request Body
```json
{
  "url": "https://www.youtube.com/watch?v=example",
  "quality": "720p"
}
```

#### Parameters
- `url` (required): The video URL to download
- `quality` (optional): Video quality (default: "720p")
  - Video: "144p", "240p", "360p", "480p", "720p", "1080p", "1440p", "2160p"
  - Audio: "audio" (downloads audio-only format)

#### Response
```json
{
  "task_id": "c5d8b9a2-1f3e-4d6c-8b9a-2f3e4d6c8b9a",
  "status": "queued",
  "platform": "youtube"
}
```

#### Example
```bash
curl -X POST http://localhost:8001/api/v1/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "quality": "720p"}'
```

---

### 2. Submit Download Task (GET)

Submit a URL for asynchronous download using query parameters.

#### Endpoint
```
GET /api/v1/download?url={URL}&quality={QUALITY}
```

#### Query Parameters
- `url` (required): The video URL to download
- `quality` (optional): Video quality (default: "720p")

#### Response
```json
{
  "task_id": "c5d8b9a2-1f3e-4d6c-8b9a-2f3e4d6c8b9a",
  "status": "queued",
  "platform": "tiktok"
}
```

#### Example
```bash
curl "http://localhost:8001/api/v1/download?url=https://vt.tiktok.com/ZS593uwQc/&quality=720p"
```

---

### 3. Check Task Status

Check the status of a download task.

#### Endpoint
```
GET /api/v1/status/{task_id}
```

#### Path Parameter
- `task_id` (required): The task ID returned from the download submission

#### Response
```json
{
  "task_id": "c5d8b9a2-1f3e-4d6c-8b9a-2f3e4d6c8b9a",
  "status": "SUCCESS",
  "result": {
    "status": "SUCCESS",
    "data": {
      "title": "Example Video Title",
      "author": {
        "username": "example_user"
      },
      "duration": 120,
      "media": {
        "video": [
          {
            "url": "https://...",
            "format": "mp4",
            "quality": "720p"
          }
        ]
      }
    }
  }
}
```

Possible statuses:
- `PENDING`: Task is waiting to be processed
- `PROGRESS`: Task is currently being processed
- `SUCCESS`: Task completed successfully
- `FAILURE`: Task failed to complete
- `RETRY`: Task is being retried

---

### 4. Synchronous Download

Download media directly in a single request and receive the file.

#### Endpoint
```
GET /api/v1/download-sync?url={URL}&quality={QUALITY}
```

#### Query Parameters
- `url` (required): The video URL to download
- `quality` (optional): Video quality (default: "720p")

#### Response
Returns the media file directly (video/mp4, audio/mpeg, or application/octet-stream)

#### Example
```bash
curl -O "http://localhost:8001/api/v1/download-sync?url=https://youtube.com/watch?v=xxx&quality=720p"
```

**Note**: This endpoint may take longer to respond as it waits for the download to complete.

---

### 5. Get Available Formats

Get all available formats/resolutions for a video without downloading.

#### Endpoint
```
GET /api/v1/formats?url={URL}
```

#### Query Parameter
- `url` (required): The video URL to check formats for

#### Response
```json
{
  "formats": [
    {
      "format_id": "137",
      "format_note": "720p",
      "ext": "mp4",
      "resolution": "1280x720",
      "filesize": 12345678,
      "vcodec": "avc1.640028",
      "acodec": "none",
      "video_only": true
    },
    {
      "format_id": "140",
      "format_note": "audio only",
      "ext": "m4a",
      "filesize": 2345678,
      "vcodec": "none",
      "acodec": "mp4a.40.2",
      "audio_only": true
    }
  ],
  "title": "Example Video Title",
  "duration": 120
}
```

---

### 6. Get Download History

Retrieve download history with optional filtering.

#### Endpoint
```
GET /api/v1/history?skip={SKIP}&limit={LIMIT}&platform={PLATFORM}
```

#### Query Parameters
- `skip` (optional): Number of records to skip (default: 0, max: 100)
- `limit` (optional): Maximum number of records to return (default: 50, max: 100)
- `platform` (optional): Filter by platform (tiktok, youtube, instagram, etc.)

#### Response
```json
[
  {
    "id": 1,
    "task_id": "c5d8b9a2-1f3e-4d6c-8b9a-2f3e4d6c8b9a",
    "url": "https://www.youtube.com/watch?v=example",
    "platform": "YOUTUBE",
    "status": "SUCCESS",
    "title": "Example Video Title",
    "author": "example_user",
    "duration": 120,
    "created_at": "2023-10-15T10:30:00Z",
    "updated_at": "2023-10-15T10:32:00Z",
    "completed_at": "2023-10-15T10:31:30Z"
  }
]
```

---

### 7. Health Check

Check if the service is running properly.

#### Endpoint
```
GET /api/v1/health
```

#### Response
```json
{
  "status": "healthy",
  "service": "LibraryDown API",
  "version": "2.0.0",
  "timestamp": "2023-10-15T10:30:00Z",
  "system_stats": {
    "cpu_percent": 15.2,
    "memory_percent": 45.8,
    "disk_usage": 62.1,
    "uptime_seconds": 3600
  }
}
```

---

### 8. System Metrics

Get system metrics and statistics.

#### Endpoint
```
GET /api/v1/metrics
```

#### Response
```json
{
  "downloads": {
    "total": 150,
    "successful": 142,
    "recent_24h": 23,
    "success_rate": 94.67
  },
  "cache": {
    "enabled": true,
    "hits": 1200,
    "misses": 80,
    "hit_rate": 93.75
  },
  "system": {
    "cpu_percent": 15.2,
    "memory_percent": 45.8,
    "disk_usage": 62.1,
    "uptime_seconds": 3600
  },
  "timestamp": "2023-10-15T10:30:00Z",
  "response_time_ms": 15.2
}
```

---

### 9. Get Quality Options

Get available quality options for downloads.

#### Endpoint
```
GET /api/v1/qualities?platform={PLATFORM}
```

#### Query Parameters
- `platform` (optional): Get qualities for specific platform

#### Response
```json
{
  "platform": "youtube",
  "qualities": ["144p", "240p", "360p", "480p", "720p", "1080p", "audio"],
  "timestamp": "2023-10-15T10:30:00Z"
}
```

Or for all qualities:
```json
{
  "all_qualities": ["audio", "144p", "240p", "360p", "480p", "720p", "1080p", "1440p", "2160p", "best", "worst"],
  "timestamp": "2020-10-15T10:30:00Z"
}
```

---

### 10. Convert Media Format

Convert media file to different format.

#### Endpoint
```
POST /api/v1/convert
```

#### Request Body
```json
{
  "input_file": "video.mp4",
  "target_format": "mp3"
}
```

#### Parameters
- `input_file` (required): Path to input file in media folder
- `target_format` (required): Target format ("mp3", "mp4", "m4a", "webm", "flv", "avi", "mov", "wmv", "mkv")

#### Response
```json
{
  "status": "converted",
  "input_file": "video.mp4",
  "output_file": "video.mp3",
  "target_format": "mp3",
  "timestamp": "2023-10-15T10:30:00Z",
  "response_time_ms": 1250.5
}
```

---

### 11. Get Playlist Information

Get information about a playlist.

#### Endpoint
```
GET /api/v1/playlist-info?url={PLAYLIST_URL}
```

#### Query Parameters
- `url` (required): The playlist URL

#### Response
```json
{
  "playlist": {
    "id": "playlist_id",
    "title": "Playlist Title",
    "uploader": "Uploader Name",
    "entry_count": 12,
    "entries": [
      {
        "id": "video_id",
        "title": "Video Title",
        "duration": 120,
        "uploader": "Uploader Name",
        "url": "https://...",
        "thumbnail": "https://..."
      }
    ]
  },
  "timestamp": "2023-10-15T10:30:00Z",
  "response_time_ms": 850.2
}
```

---

### 12. Get User Preferences

Get current user preferences.

#### Endpoint
```
GET /api/v1/preferences
```

#### Response
```json
{
  "preferences": {
    "default_quality": "720p",
    "default_format": "mp4",
    "available_qualities": ["audio", "144p", "240p", "360p", "480p", "720p", "1080p", "1440p", "2160p", "best", "worst"],
    "available_formats": ["mp4", "mp3", "m4a", "webm", "flv", "avi", "mov", "wmv", "mkv"]
  },
  "timestamp": "2023-10-15T10:30:00Z",
  "response_time_ms": 2.1
}
```

---

### 13. Get Version Information

Get current version and check for updates.

#### Endpoint
```
GET /api/v1/version
```

#### Response
```json
{
  "version_info": {
    "current_version": "2.0.0",
    "latest_version": "2.1.0",
    "update_available": true,
    "update_message": "Update available: 2.0.0 -> 2.1.0",
    "git_branch": "main",
    "git_commit": "abc1234",
    "system": "Linux",
    "release": "5.4.0-109-generic",
    "architecture": "x86_64",
    "python_version": "3.11.0",
    "cpu_count": 4,
    "memory_total_gb": 16.0,
    "disk_total_gb": 500.0,
    "uptime_seconds": 7200
  },
  "timestamp": "2023-10-15T10:30:00Z",
  "response_time_ms": 120.5
}
```

---

### 14. Update System

Update the system to the latest version.

#### Endpoint
```
POST /api/v1/update
```

#### Response
```json
{
  "status": "updated",
  "message": "Update completed successfully",
  "previous_version": "2.0.0",
  "timestamp": "2023-10-15T10:30:00Z",
  "response_time_ms": 15000.0
}
```

## Error Responses

Common error responses:

### 400 Bad Request
```json
{
  "detail": "Error message explaining the issue"
}
```

### 404 Not Found
```json
{
  "detail": "Item not found"
}
```

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded: 10 per 1 minute"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error occurred"
}
```

## Quality Options Guide

| Quality Option | Description |
|----------------|-------------|
| `audio` | Audio-only format (M4A) |
| `144p` | Very low quality video |
| `240p` | Low quality video |
| `360p` | Standard low quality |
| `480p` | Standard definition |
| `720p` | High definition (default) |
| `1080p` | Full high definition |
| `1440p` | Quad high definition |
| `2160p` | 4K ultra high definition |
| `best` | Best available quality |
| `worst` | Worst available quality |

## Format Conversion Options

| Format | Description |
|--------|-------------|
| `mp4` | MPEG-4 video format |
| `mp3` | MP3 audio format |
| `m4a` | Apple lossless audio |
| `webm` | WebM video format |
| `flv` | Flash video format |
| `avi` | Audio Video Interleave |
| `mov` | QuickTime movie format |
| `wmv` | Windows Media Video |
| `mkv` | Matroska video format |

## Best Practices

1. **Use Asynchronous Downloads for Large Files**: For large videos or when you don't need immediate results, use the async `/download` endpoint and poll `/status/{task_id}`.

2. **Use Synchronous Downloads for Small Files**: For quick downloads of smaller files, use `/download-sync` for a single-request experience.

3. **Check Available Formats First**: Use `/formats` endpoint before downloading to see available quality options.

4. **Handle Rate Limits**: Implement exponential backoff when encountering 429 errors.

5. **Validate URLs**: Always ensure URLs are properly formatted before submitting.

6. **Monitor Task Status**: For async downloads, check status periodically but not too frequently to avoid hitting rate limits.

## Troubleshooting

### Common Issues

1. **Unsupported Platform**: Verify the URL is from a supported platform
2. **Rate Limited**: Wait before making additional requests
3. **Invalid URL**: Ensure the URL is properly formatted with protocol (http/https)
4. **Download Failed**: Some videos may be geo-restricted or removed

### Performance Tips

1. **CDN Usage**: The API uses CDN-like optimization for faster media delivery
2. **Caching**: Frequently accessed content is cached for better performance
3. **Queue Management**: Tasks are prioritized to optimize resource usage

For additional support, check the service health endpoint or contact the administrator.