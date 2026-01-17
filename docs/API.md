# LibraryDown API Documentation

## Overview

LibraryDown adalah Universal Social Media Downloader API yang mendukung download konten dari berbagai platform media sosial secara asynchronous.

**Base URL**: `http://localhost:8000` (development)

**API Version**: `v2.0.0`

**Documentation**: 
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Supported Platforms

| Platform | Status | URL Format |
|----------|--------|------------|
| TikTok | ✅ Fully Working | `tiktok.com/@user/video/{id}`, `vt.tiktok.com/{short}` |
| YouTube | ✅ Implemented | `youtube.com/watch?v={id}`, `youtu.be/{id}` |
| Instagram | ⚠️ Placeholder | `instagram.com/p/{shortcode}` |
| Twitter/X | ⚠️ Placeholder | `twitter.com/user/status/{id}`, `x.com/user/status/{id}` |

## Authentication

**None** - API ini bersifat public, tetapi menggunakan **rate limiting** untuk mencegah abuse.

**Rate Limit**: 10 requests per minute per IP address

## Endpoints

### 1. Submit Download Task (POST)

Submit URL untuk di-download.

**Endpoint**: `POST /api/v1/download`

**Request Body**:
```json
{
  "url": "https://vt.tiktok.com/ZS593uwQc/"
}
```

**Response** (200 OK):
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "queued",
  "platform": "tiktok"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid URL or unsupported platform
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

**Example cURL**:
```bash
curl -X POST http://localhost:8000/api/v1/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://vt.tiktok.com/ZS593uwQc/"}'
```

---

### 2. Submit Download Task (GET)

Alternative method untuk submit URL via query parameter.

**Endpoint**: `GET /api/v1/download?url={encoded_url}`

**Query Parameters**:
- `url` (required): URL yang akan di-download

**Response** (200 OK):
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "queued",
  "platform": "tiktok"
}
```

**Example**:
```bash
curl "http://localhost:8000/api/v1/download?url=https%3A%2F%2Fvt.tiktok.com%2FZS593uwQc%2F"
```

---

### 3. Get Task Status

Cek status dan hasil download task.

**Endpoint**: `GET /api/v1/status/{task_id}`

**Path Parameters**:
- `task_id` (required): Task ID dari response download endpoint

**Response** (200 OK):

**Status: PENDING**
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "PENDING",
  "result": null
}
```

**Status: PROGRESS**
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "PROGRESS",
  "result": {
    "status": "Downloading media files...",
    "platform": "tiktok",
    "progress": 60
  }
}
```

**Status: SUCCESS**
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "SUCCESS",
  "result": {
    "status": "SUCCESS",
    "platform": "tiktok",
    "data": {
      "platform": "tiktok",
      "id": "7123456789012345678",
      "content_type": "video",
      "caption": "Video caption here",
      "author": {
        "username": "username",
        "display_name": "Display Name",
        "is_verified": true
      },
      "statistics": {
        "views": 1000000,
        "likes": 50000,
        "comments": 1000,
        "shares": 500
      },
      "media": {
        "video": [
          {
            "quality": "720p",
            "direct_url": "http://localhost:8000/media/7123456789012345678.mp4"
          }
        ],
        "thumbnail": "http://localhost:8000/media/7123456789012345678_thumb.jpeg"
      }
    }
  }
}
```

**Status: FAILURE**
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "FAILURE",
  "result": {
    "status": "FAILURE",
    "error": "Content not available",
    "error_type": "ValueError",
    "platform": "tiktok"
  }
}
```

**Example**:
```bash
curl http://localhost:8000/api/v1/status/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

---

### 4. Get Download History

Retrieve download history dengan pagination dan filtering.

**Endpoint**: `GET /api/v1/history`

**Query Parameters**:
- `skip` (optional, default: 0): Number of records to skip
- `limit` (optional, default: 50, max: 100): Number of records to return
- `platform` (optional): Filter by platform (`tiktok`, `youtube`, `instagram`, `twitter`)

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "url": "https://vt.tiktok.com/ZS593uwQc/",
    "platform": "TIKTOK",
    "status": "SUCCESS",
    "title": "Video caption here",
    "author": "username",
    "duration": 15.5,
    "created_at": "2026-01-16T10:30:00",
    "completed_at": "2026-01-16T10:30:45",
    "error_message": null
  }
]
```

**Example**:
```bash
# Get latest 10 TikTok downloads
curl "http://localhost:8000/api/v1/history?limit=10&platform=tiktok"
```

---

## Task Status Flow

```
PENDING → PROGRESS → SUCCESS
                   ↘ RETRY → SUCCESS
                   ↘ FAILURE
```

**Status Descriptions**:
- `PENDING`: Task sedang menunggu di queue
- `PROGRESS`: Task sedang diproses
- `RETRY`: Task gagal dan sedang di-retry (max 3x)
- `SUCCESS`: Task berhasil, media siap di-download
- `FAILURE`: Task gagal setelah semua retry attempts

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message here"
}
```

### Common Error Codes

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad Request - Invalid URL or parameters |
| 404 | Not Found - Task ID tidak ditemukan |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |

### Platform-Specific Errors

**TikTok**:
- "Content not available" - Video private/deleted
- "Could not find data script" - Page structure changed

**YouTube**:
- "Could not find 'ytInitialData'" - Page structure changed
- Video mungkin memerlukan login untuk konten tertentu

**Instagram** (Coming Soon):
- "NotImplementedError" - Feature belum fully implemented

**Twitter/X** (Coming Soon):
- "NotImplementedError" - Requires API credentials

## Rate Limiting

**Default**: 10 requests per minute per IP address

Response headers ketika rate limit aktif:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 5
X-RateLimit-Reset: 1642345678
```

Response ketika limit exceeded (429):
```json
{
  "error": "Rate limit exceeded: 10 per 1 minute"
}
```

## File Management

**Auto-cleanup**: Files otomatis dihapus setelah 24 jam (configurable via `FILE_TTL_HOURS`)

**Download URL Format**: `http://localhost:8000/media/{filename}`

**Supported File Types**:
- Video: `.mp4`
- Image: `.jpeg`, `.jpg`, `.png`
- Audio: `.mp3`

## Best Practices

1. **Polling Status**: Poll status endpoint setiap 2-5 detik untuk task yang sedang berjalan
2. **Error Handling**: Always check `error_type` pada FAILURE response untuk proper error handling
3. **Rate Limiting**: Implement exponential backoff jika mendapat 429 response
4. **Download URLs**: Download file sesegera mungkin karena ada TTL
5. **Task ID Storage**: Simpan task_id untuk tracking dan debugging

## Example Client Implementation

### Python

```python
import requests
import time

API_BASE = "http://localhost:8000/api/v1"

def download_video(url):
    # Submit task
    response = requests.post(f"{API_BASE}/download", json={"url": url})
    task_id = response.json()["task_id"]
    
    print(f"Task created: {task_id}")
    
    # Poll status
    while True:
        status_resp = requests.get(f"{API_BASE}/status/{task_id}")
        data = status_resp.json()
        
        if data["status"] == "SUCCESS":
            print("Download complete!")
            return data["result"]["data"]
        elif data["status"] == "FAILURE":
            print(f"Download failed: {data['result']['error']}")
            return None
        
        print(f"Status: {data['status']}")
        time.sleep(3)

# Usage
result = download_video("https://vt.tiktok.com/ZS593uwQc/")
if result:
    video_url = result["media"]["video"][0]["direct_url"]
    print(f"Video URL: {video_url}")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

const API_BASE = 'http://localhost:8000/api/v1';

async function downloadVideo(url) {
  // Submit task
  const { data: taskData } = await axios.post(`${API_BASE}/download`, { url });
  const taskId = taskData.task_id;
  
  console.log(`Task created: ${taskId}`);
  
  // Poll status
  while (true) {
    const { data: statusData } = await axios.get(`${API_BASE}/status/${taskId}`);
    
    if (statusData.status === 'SUCCESS') {
      console.log('Download complete!');
      return statusData.result.data;
    } else if (statusData.status === 'FAILURE') {
      console.log(`Download failed: ${statusData.result.error}`);
      return null;
    }
    
    console.log(`Status: ${statusData.status}`);
    await new Promise(resolve => setTimeout(resolve, 3000));
  }
}

// Usage
downloadVideo('https://vt.tiktok.com/ZS593uwQc/')
  .then(result => {
    if (result) {
      const videoUrl = result.media.video[0].direct_url;
      console.log(`Video URL: ${videoUrl}`);
    }
  });
```

## Support & Issues

Untuk bug reports atau feature requests, silakan buka issue di repository GitHub.
