from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from src.api.schemas import DownloadRequest, DownloadResponse, TaskStatusResponse, DownloadHistoryResponse, FormatsResponse
from src.workers.tasks import download_media_task, detect_platform
from src.workers.celery_app import celery_app
from src.database.base import get_db
from src.database.models import DownloadHistory, TaskStatus, PlatformType
from sqlalchemy.orm import Session
from celery.result import AsyncResult
from pydantic import HttpUrl
from datetime import datetime, timedelta
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import List, Optional
import asyncio
import tempfile
import os
from fastapi.responses import FileResponse

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.post("/download", response_model=DownloadResponse, summary="Submit a URL via POST request")
@limiter.limit("10/minute")
async def create_download_task_post(
    request: Request,
    download_request: DownloadRequest,
    db: Session = Depends(get_db)
):
    """
    Accepts a URL in a JSON body and queues it for download.
    
    **Supported platforms:**
    - TikTok (tiktok.com, vt.tiktok.com)
    - YouTube (youtube.com, youtu.be)
    - Instagram (instagram.com)
    - Reddit (reddit.com, redd.it) - Limited support
    - SoundCloud (soundcloud.com) - Audio only
    - Dailymotion (dailymotion.com, dai.ly)
    - Twitch (twitch.tv) - Clips and VODs
    - Vimeo (vimeo.com) - Limited support
    - Facebook (facebook.com, fb.watch) - Limited support
    - Twitter/X (twitter.com, x.com) - Limited support
    - Bilibili (bilibili.com) - Region restricted
    - LinkedIn (linkedin.com) - Not supported
    - Pinterest (pinterest.com) - Not supported
    
    **Quality options:**
    - Video: "144p", "240p", "360p", "480p", "720p", "1080p", "1440p", "2160p" (default: "720p")
    - Audio: "audio" - Download audio-only format (M4A)
    
    **Example:**
    ```json
    {
      "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "quality": "720p"
    }
    ```
    
    For audio-only download:
    ```json
    {
      "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "quality": "audio"
    }
    ```
    """
    if not download_request.url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    url = str(download_request.url)
    platform = detect_platform(url)
    
    if platform == "unknown":
        raise HTTPException(
            status_code=400,
            detail="Unsupported platform. Supported: TikTok, YouTube, Instagram, Reddit, SoundCloud, Dailymotion, Twitch, Vimeo, Facebook, Bilibili, LinkedIn, Pinterest"
        )
    
    # Create download history record
    history = DownloadHistory(
        task_id="",  # Will be updated after task creation
        url=url,
        platform=PlatformType[platform.upper()],
        status=TaskStatus.PENDING,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    try:
        # Queue the task with quality parameter
        task = download_media_task.delay(url, download_request.quality)
        
        # Update history with task ID
        history.task_id = task.id
        db.add(history)
        db.commit()
        
        logger.info(f"[API] Created download task {task.id} for {platform}: {url} (quality: {download_request.quality})")
        
        return {
            "task_id": task.id,
            "status": "queued",
            "platform": platform
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"[API] Failed to create download task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to queue download: {str(e)}")

@router.get("/download", response_model=DownloadResponse, summary="Submit a URL via GET request")
@limiter.limit("10/minute")
async def create_download_task_get(
    request: Request,
    url: HttpUrl,
    quality: Optional[str] = "720p",
    db: Session = Depends(get_db)
):
    """
    Accepts a URL via a query parameter and queues it for download.
    
    **Example:** `/api/v1/download?url=https://vt.tiktok.com/ZS593uwQc/&quality=720p`
    
    **Quality options:**
    - Video: "144p", "240p", "360p", "480p", "720p", "1080p" (default: "720p")
    - Audio: "audio" - Download audio-only format (M4A, YouTube only)
    """
    url_str = str(url)
    platform = detect_platform(url_str)
    
    if platform == "unknown":
        raise HTTPException(
            status_code=400,
            detail="Unsupported platform. Supported: TikTok, YouTube, Instagram, Reddit, SoundCloud, Dailymotion, Twitch, Vimeo, Facebook, Bilibili, LinkedIn, Pinterest"
        )
    
    # Create download history record
    history = DownloadHistory(
        task_id="",
        url=url_str,
        platform=PlatformType[platform.upper()],
        status=TaskStatus.PENDING,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    try:
        task = download_media_task.delay(url_str, quality)
        history.task_id = task.id
        db.add(history)
        db.commit()
        
        logger.info(f"[API] Created download task {task.id} for {platform}: {url_str} (quality: {quality})")
        
        return {
            "task_id": task.id,
            "status": "queued",
            "platform": platform
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"[API] Failed to create download task: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to queue download: {str(e)}")

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """
    Retrieves the status and result of a download task.
    Also updates the database with the latest status.
    """
    task_result = AsyncResult(task_id, app=celery_app)
    
    try:
        status = task_result.status
        result = task_result.result if task_result.ready() else None
        
        # Handle malformed results
        if status == 'FAILURE' and not isinstance(result, dict):
            result = {
                "status": "FAILURE",
                "error": "Worker crashed and left a malformed result. Check worker logs."
            }
        
        # Update database
        history = db.query(DownloadHistory).filter(DownloadHistory.task_id == task_id).first()
        if history:
            # Map Celery status to our TaskStatus enum
            status_map = {
                'PENDING': TaskStatus.PENDING,
                'PROGRESS': TaskStatus.PROGRESS,
                'SUCCESS': TaskStatus.SUCCESS,
                'FAILURE': TaskStatus.FAILURE,
                'RETRY': TaskStatus.RETRY
            }
            
            history.status = status_map.get(status, TaskStatus.PENDING)
            history.updated_at = datetime.utcnow()
            
            if status == 'SUCCESS' and isinstance(result, dict):
                history.completed_at = datetime.utcnow()
                data = result.get('data', {})
                history.title = data.get('title') or data.get('caption', '')[:200]
                history.author = data.get('author', {}).get('username')
                history.duration = data.get('duration')
            
            elif status == 'FAILURE' and isinstance(result, dict):
                history.error_message = result.get('error', str(result))
                history.retry_count = result.get('retry_count', 0)
            
            db.commit()
    
    except ValueError:
        status = "FAILURE"
        result = {
            "status": "FAILURE",
            "error": "Could not decode task result. The worker likely crashed."
        }
    
    response = {
        "task_id": task_id,
        "status": status,
        "result": result
    }
    
    return response

@router.get("/history", response_model=List[DownloadHistoryResponse])
async def get_download_history(
    skip: int = 0,
    limit: int = 50,
    platform: str = None,
    db: Session = Depends(get_db)
):
    """
    Get download history with optional filtering.
    
    Parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return (max 100)
    - platform: Filter by platform (tiktok, youtube, instagram, twitter)
    """
    if limit > 100:
        limit = 100
    
    query = db.query(DownloadHistory).order_by(DownloadHistory.created_at.desc())
    
    if platform:
        try:
            platform_enum = PlatformType[platform.upper()]
            query = query.filter(DownloadHistory.platform == platform_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid platform: {platform}")
    
    history = query.offset(skip).limit(limit).all()
    
    return history

@router.get("/download-sync", summary="Download media synchronously in one step")
@limiter.limit("5/minute")
async def download_sync(
    request: Request,
    url: HttpUrl,
    quality: Optional[str] = "720p",
    db: Session = Depends(get_db)
):
    """
    Synchronous download endpoint that returns the media file directly.
    This is a single-step process unlike the async download which requires polling.
    
    **Usage:**
    `/api/v1/download-sync?url=https://youtube.com/watch?v=xxx&quality=720p`
    
    **Note:** This endpoint may take longer to respond as it waits for the download to complete.
    For large files or slow connections, the async endpoint might be preferred.
    """
    from src.utils.security import security_validator
    
    url_str = str(url)
    
    # Validate URL security
    is_valid, error = security_validator.validate_url(url_str)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid URL: {error}")
    
    platform = detect_platform(url_str)
    
    if platform == "unknown":
        raise HTTPException(
            status_code=400,
            detail="Unsupported platform. Supported: TikTok, YouTube, Instagram, Reddit, SoundCloud, Dailymotion, Twitch, Vimeo, Facebook, Bilibili, LinkedIn, Pinterest"
        )
    
    # Create download history record
    history = DownloadHistory(
        task_id="sync_" + url_str.replace(":", "").replace("/", "_")[:16],  # Use sanitized URL as pseudo-task ID
        url=url_str,
        platform=PlatformType[platform.upper()],
        status=TaskStatus.PENDING,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    try:
        # Get appropriate downloader
        if platform == "youtube":
            from src.engine.platforms.youtube import YouTubeDownloader
            downloader = YouTubeDownloader()
        elif platform == "tiktok":
            from src.engine.platforms.tiktok import TikTokDownloader
            downloader = TikTokDownloader()
        elif platform == "instagram":
            from src.engine.platforms.instagram import InstagramDownloader
            downloader = InstagramDownloader()
        elif platform == "soundcloud":
            from src.engine.platforms.soundcloud import SoundCloudDownloader
            downloader = SoundCloudDownloader()
        elif platform == "dailymotion":
            from src.engine.platforms.dailymotion import DailymotionDownloader
            downloader = DailymotionDownloader()
        elif platform == "twitch":
            from src.engine.platforms.twitch import TwitchDownloader
            downloader = TwitchDownloader()
        elif platform == "reddit":
            from src.engine.platforms.reddit import RedditDownloader
            downloader = RedditDownloader()
        elif platform == "vimeo":
            from src.engine.platforms.vimeo import VimeoDownloader
            downloader = VimeoDownloader()
        elif platform == "facebook":
            from src.engine.platforms.facebook import FacebookDownloader
            downloader = FacebookDownloader()
        elif platform == "bilibili":
            from src.engine.platforms.bilibili import BilibiliDownloader
            downloader = BilibiliDownloader()
        elif platform == "linkedin":
            from src.engine.platforms.linkedin import LinkedInDownloader
            downloader = LinkedInDownloader()
        elif platform == "pinterest":
            from src.engine.platforms.pinterest import PinterestDownloader
            downloader = PinterestDownloader()
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Sync download not yet implemented for {platform}"
            )
        
        # Perform download synchronously
        logger.info(f"[API] Starting synchronous download for {platform}: {url_str} (quality: {quality})")
        
        # Update history status
        history.status = TaskStatus.PROGRESS
        db.add(history)
        db.commit()
        
        # Download the media
        result = await downloader.download(url_str, quality=quality)
        
        # Update history with success
        history.status = TaskStatus.SUCCESS
        history.completed_at = datetime.utcnow()
        data = result if isinstance(result, dict) else {"title": "Downloaded Content"}
        history.title = data.get('title', data.get('caption', ''))[:200]
        history.author = data.get('author', {}).get('username')
        history.duration = data.get('duration')
        db.commit()
        
        # Extract the file path from the result
        video_files = data.get('media', {}).get('video', [])
        if video_files:
            # Look for the actual downloaded file in the media folder
            from src.core.config import settings
            import glob
            
            # Try to find the file that was downloaded based on video ID
            video_id = data.get('id', url_str.split('/')[-1][:20])  # fallback to part of URL
            media_path = settings.MEDIA_FOLDER
            
            # Look for files matching the pattern
            possible_files = []
            for ext in ['.mp4', '.m4a', '.mov', '.avi', '.flv']:
                pattern = os.path.join(media_path, f"{video_id}*{ext}")
                matches = glob.glob(pattern)
                possible_files.extend(matches)
            
            # Also look for common patterns used by downloaders
            if not possible_files:
                for ext in ['.mp4', '.m4a', '.mov', '.avi', '.flv']:
                    pattern = os.path.join(media_path, f"*{video_id[:10]}*{ext}")  # partial match
                    matches = glob.glob(pattern)
                    possible_files.extend(matches)
            
            if possible_files:
                # Use the most recently modified file
                latest_file = max(possible_files, key=os.path.getmtime)
                filename = os.path.basename(latest_file)
                
                logger.info(f"[API] Returning file: {latest_file}")
                return FileResponse(
                    path=latest_file,
                    filename=filename,
                    media_type='video/mp4' if filename.endswith('.mp4') else 'audio/mpeg' if filename.endswith('.m4a') else 'application/octet-stream'
                )
            else:
                # If no specific file found, try to get from the result URLs
                for video_file in video_files:
                    file_url = video_file.get('url', '')
                    if file_url:
                        # Extract filename from URL
                        filename = file_url.split('/')[-1]
                        local_file_path = os.path.join(media_path, filename)
                        
                        if os.path.exists(local_file_path):
                            logger.info(f"[API] Returning file: {local_file_path}")
                            return FileResponse(
                                path=local_file_path,
                                filename=filename,
                                media_type='video/mp4' if filename.endswith('.mp4') else 'audio/mpeg' if filename.endswith('.m4a') else 'application/octet-stream'
                            )
        
        # If no file could be found/returned, return metadata
        logger.warning(f"[API] Could not find downloaded file, returning metadata instead")
        return {
            "status": "completed",
            "platform": platform,
            "title": data.get('title'),
            "result": result,
            "message": "Download completed but file not available for direct serving. Check media folder or use async endpoint for file access."
        }
        
    except Exception as e:
        # Update history with failure
        db.rollback()
        history.status = TaskStatus.FAILURE
        history.error_message = str(e)
        db.add(history)
        db.commit()
        
        logger.error(f"[API] Sync download failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sync download failed: {str(e)}")


@router.get("/health", summary="Health check endpoint")
async def health_check():
    """
    Simple health check endpoint for monitoring.
    Returns 200 OK if service is running properly.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/metrics", summary="System metrics")
async def get_metrics(db: Session = Depends(get_db)):
    """
    Get system metrics and statistics.
    """
    try:
        # Get download statistics
        total_downloads = db.query(DownloadHistory).count()
        successful_downloads = db.query(DownloadHistory).filter(
            DownloadHistory.status == TaskStatus.SUCCESS
        ).count()
        
        # Get recent activity
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recent_downloads = db.query(DownloadHistory).filter(
            DownloadHistory.created_at >= last_24h
        ).count()
        
        # Get cache stats if available
        cache_stats = {}
        try:
            from src.utils.cache import cache_manager
            cache_stats = cache_manager.get_stats()
        except ImportError:
            cache_stats = {"enabled": False}
        
        return {
            "downloads": {
                "total": total_downloads,
                "successful": successful_downloads,
                "recent_24h": recent_downloads,
                "success_rate": round(successful_downloads/total_downloads*100, 2) if total_downloads > 0 else 0
            },
            "cache": cache_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Metrics endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch metrics")
@limiter.limit("20/minute")
async def get_video_formats(
    request: Request,
    url: HttpUrl
):
    """
    Get all available formats/resolutions for a video without downloading.
    
    This is a lightweight endpoint that only fetches metadata and available quality options.
    Use this before calling `/download` to see what quality options are available.
    
    **Example:** `/api/v1/formats?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ`
    
    **Supported platforms:**
    - **YouTube**: Returns multiple resolution options (144p to 2160p) + audio-only option
    - **Instagram**: Returns available resolutions + audio-only option
    - **SoundCloud**: Returns audio formats with bitrate options (audio-only platform)
    - **Dailymotion**: Returns multiple resolution options + audio-only option
    - **Twitch**: Returns available stream qualities + audio-only option
    - **TikTok**: Returns fixed quality (what TikTok provides, usually single quality)
    - **Reddit, Vimeo, Facebook, Twitter/X**: Limited support (environment restrictions)
    - **Bilibili**: Region restricted
    - **LinkedIn, Pinterest**: Not supported
    
    **Response includes:**
    - Video title and metadata
    - List of available formats with quality, file size (MB), codecs
    - Audio-only option (YouTube only)
    """
    try:
        url_str = str(url)
        platform = detect_platform(url_str)
        
        if platform == "unknown":
            raise HTTPException(
                status_code=400,
                detail="Unsupported platform. Supported: TikTok, YouTube, Instagram, Reddit"
            )
        
        logger.info(f"[API] Fetching formats for {platform}: {url_str}")
        
        # Import platform-specific downloader
        if platform == "youtube":
            from src.engine.platforms.youtube import YouTubeDownloader
            downloader = YouTubeDownloader()
        elif platform == "tiktok":
            from src.engine.platforms.tiktok import TikTokDownloader
            downloader = TikTokDownloader()
        elif platform == "instagram":
            from src.engine.platforms.instagram import InstagramDownloader
            downloader = InstagramDownloader()
        elif platform == "soundcloud":
            from src.engine.platforms.soundcloud import SoundCloudDownloader
            downloader = SoundCloudDownloader()
        elif platform == "dailymotion":
            from src.engine.platforms.dailymotion import DailymotionDownloader
            downloader = DailymotionDownloader()
        elif platform == "twitch":
            from src.engine.platforms.twitch import TwitchDownloader
            downloader = TwitchDownloader()
        elif platform == "reddit":
            from src.engine.platforms.reddit import RedditDownloader
            downloader = RedditDownloader()
        elif platform == "vimeo":
            from src.engine.platforms.vimeo import VimeoDownloader
            downloader = VimeoDownloader()
        elif platform == "facebook":
            from src.engine.platforms.facebook import FacebookDownloader
            downloader = FacebookDownloader()
        elif platform == "bilibili":
            from src.engine.platforms.bilibili import BilibiliDownloader
            downloader = BilibiliDownloader()
        elif platform == "linkedin":
            from src.engine.platforms.linkedin import LinkedInDownloader
            downloader = LinkedInDownloader()
        elif platform == "pinterest":
            from src.engine.platforms.pinterest import PinterestDownloader
            downloader = PinterestDownloader()
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Format fetching not yet implemented for {platform}"
            )
        
        # Get formats without downloading
        formats_data = await downloader.get_formats(url_str)
        
        logger.info(f"[API] Found {len(formats_data.get('formats', []))} formats")
        
        return formats_data
        
    except ValueError as e:
        logger.error(f"[API] ValueError while fetching formats: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[API] Error fetching formats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch formats: {str(e)}")

