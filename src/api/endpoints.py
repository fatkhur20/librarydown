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
from src.utils.logging.logger import log_api_call, log_download_event, log_error
from src.utils.logging.monitor import monitor
from src.config.monitoring_config import monitoring_settings
from src.utils.version_checker import version_checker
from src.utils.user_features import QualityOption, FormatOption, quality_selector, format_converter, playlist_handler, user_preferences

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
    start_time = datetime.utcnow()
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    log_api_call("/api/v1/download", "POST", client_ip, 200)
    
    if not download_request.url:
        log_error("Missing URL in download request", context={"client_ip": client_ip})
        raise HTTPException(status_code=400, detail="URL is required")
    
    url = str(download_request.url)
    platform = detect_platform(url)
    
    if platform == "unknown":
        log_error(f"Unsupported platform detected: {url}", context={
            "client_ip": client_ip,
            "platform": platform,
            "user_agent": user_agent
        })
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
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    try:
        # Queue the task with quality parameter
        task = download_media_task.delay(url, download_request.quality)
        
        # Update history with task ID
        history.task_id = task.id
        db.add(history)
        db.commit()
        
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000  # Convert to milliseconds
        logger.info(f"[API] Created download task {task.id} for {platform}: {url} (quality: {download_request.quality}) took {duration:.2f}ms")
        log_download_event(url, client_ip, "QUEUED", duration=duration)
        
        return {
            "task_id": task.id,
            "status": "queued",
            "platform": platform
        }
        
    except Exception as e:
        db.rollback()
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000  # Convert to milliseconds
        logger.error(f"[API] Failed to create download task: {e}")
        log_error(f"Failed to create download task: {e}", exception=e, 
                  context={"url": url, "client_ip": client_ip, "duration_ms": duration})
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
    start_time = datetime.utcnow()
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    log_api_call("/api/v1/download", "GET", client_ip, 200)
    
    url_str = str(url)
    platform = detect_platform(url_str)
    
    if platform == "unknown":
        log_error(f"Unsupported platform detected: {url_str}", context={
            "client_ip": client_ip,
            "platform": platform,
            "user_agent": user_agent
        })
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
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    try:
        task = download_media_task.delay(url_str, quality)
        history.task_id = task.id
        db.add(history)
        db.commit()
        
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000  # Convert to milliseconds
        logger.info(f"[API] Created download task {task.id} for {platform}: {url_str} (quality: {quality}) took {duration:.2f}ms")
        log_download_event(url_str, client_ip, "QUEUED", duration=duration)
        
        return {
            "task_id": task.id,
            "status": "queued",
            "platform": platform
        }
        
    except Exception as e:
        db.rollback()
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000  # Convert to milliseconds
        logger.error(f"[API] Failed to create download task: {e}")
        log_error(f"Failed to create download task: {e}", exception=e, 
                  context={"url": url_str, "client_ip": client_ip, "duration_ms": duration})
        raise HTTPException(status_code=500, detail=f"Failed to queue download: {str(e)}")

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """
    Retrieves the status and result of a download task.
    Also updates the database with the latest status.
    """
    start_time = datetime.utcnow()
    
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
    
    except ValueError as e:
        status = "FAILURE"
        result = {
            "status": "FAILURE",
            "error": "Could not decode task result. The worker likely crashed."
        }
        log_error(f"Could not decode task result: {e}", exception=e, 
                  context={"task_id": task_id})
    
    duration = (datetime.utcnow() - start_time).total_seconds() * 1000  # Convert to milliseconds
    logger.info(f"[API] Status check for task {task_id}: {status} took {duration:.2f}ms")
    log_api_call(f"/api/v1/status/{task_id}", "GET", task_id, 200, duration)
    
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
    start_time = datetime.utcnow()
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    log_api_call("/api/v1/download-sync", "GET", client_ip, 200)
    
    from src.utils.security import security_validator
    
    url_str = str(url)
    
    # Validate URL security
    is_valid, error = security_validator.validate_url(url_str)
    if not is_valid:
        log_error(f"Invalid URL provided: {url_str}", context={
            "client_ip": client_ip,
            "error": error
        })
        raise HTTPException(status_code=400, detail=f"Invalid URL: {error}")
    
    platform = detect_platform(url_str)
    
    if platform == "unknown":
        log_error(f"Unsupported platform detected: {url_str}", context={
            "client_ip": client_ip,
            "platform": platform,
            "user_agent": user_agent
        })
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
        ip_address=client_ip,
        user_agent=user_agent
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
            log_error(f"Sync download not implemented for platform: {platform}", context={
                "client_ip": client_ip,
                "platform": platform,
                "url": url_str
            })
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
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000  # Convert to milliseconds
                log_download_event(url_str, client_ip, "SUCCESS", 
                                  file_size=os.path.getsize(latest_file) if os.path.exists(latest_file) else None,
                                  duration=duration)
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
                            duration = (datetime.utcnow() - start_time).total_seconds() * 1000  # Convert to milliseconds
                            log_download_event(url_str, client_ip, "SUCCESS", 
                                              file_size=os.path.getsize(local_file_path) if os.path.exists(local_file_path) else None,
                                              duration=duration)
                            return FileResponse(
                                path=local_file_path,
                                filename=filename,
                                media_type='video/mp4' if filename.endswith('.mp4') else 'audio/mpeg' if filename.endswith('.m4a') else 'application/octet-stream'
                            )
        
        # If no file could be found/returned, return metadata
        logger.warning(f"[API] Could not find downloaded file, returning metadata instead")
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000  # Convert to milliseconds
        log_download_event(url_str, client_ip, "PARTIAL_SUCCESS", duration=duration)
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
        
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000  # Convert to milliseconds
        logger.error(f"[API] Sync download failed: {e}")
        log_error(f"Sync download failed: {e}", exception=e, 
                  context={"url": url_str, "client_ip": client_ip, "duration_ms": duration})
        log_download_event(url_str, client_ip, "FAILED", duration=duration)
        raise HTTPException(status_code=500, detail=f"Sync download failed: {str(e)}")


@router.get("/health", summary="Health check endpoint")
async def health_check():
    """
    Simple health check endpoint for monitoring.
    Returns 200 OK if service is running properly.
    """
    try:
        from src.core.config import settings
        
        response = {
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.VERSION,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if monitoring_settings.MONITORING_ENABLED:
            try:
                system_stats = monitor.get_system_stats()
                response["system_stats"] = {
                    "cpu_percent": system_stats.get("cpu_percent"),
                    "memory_percent": system_stats.get("memory_percent"),
                    "disk_usage": system_stats.get("disk_usage"),
                    "uptime_seconds": system_stats.get("uptime_seconds")
                }
            except Exception as e:
                logger.warning(f"Failed to get system stats for health check: {e}")
                response["system_stats"] = "unavailable"
        
        return response
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

@router.get("/metrics", summary="System metrics")
async def get_metrics(db: Session = Depends(get_db)):
    """
    Get system metrics and statistics.
    """
    start_time = datetime.utcnow()
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
        
        # Get system stats if monitoring is enabled
        system_stats = {}
        if monitoring_settings.MONITORING_ENABLED:
            system_stats = monitor.get_system_stats()
        
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000  # Convert to milliseconds
        log_api_call("/api/v1/metrics", "GET", "system", 200, duration)
        
        return {
            "downloads": {
                "total": total_downloads,
                "successful": successful_downloads,
                "recent_24h": recent_downloads,
                "success_rate": round(successful_downloads/total_downloads*100, 2) if total_downloads > 0 else 0
            },
            "cache": cache_stats,
            "system": system_stats,
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": duration
        }
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000  # Convert to milliseconds
        logger.error(f"Metrics endpoint error: {e}")
        log_error(f"Metrics endpoint error: {e}", exception=e, context={"duration_ms": duration})
        raise HTTPException(status_code=500, detail="Unable to fetch metrics")

@router.get("/version", summary="Get version information")
async def get_version_info():
    """
    Get current version and check for updates.
    """
    start_time = datetime.utcnow()
    
    try:
        system_info = version_checker.get_system_info()
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000  # Convert to milliseconds
        log_api_call("/api/v1/version", "GET", "system", 200, duration)
        
        return {
            "version_info": system_info,
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": duration
        }
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000  # Convert to milliseconds
        logger.error(f"Version endpoint error: {e}")
        log_error(f"Version endpoint error: {e}", exception=e, context={"duration_ms": duration})
        raise HTTPException(status_code=500, detail="Unable to fetch version info")

@router.post("/update", summary="Update the system")
async def update_system(request: Request):
    """
    Update the system to the latest version.
    """
    client_ip = request.client.host if request.client else None
    start_time = datetime.utcnow()
    
    log_api_call("/api/v1/update", "POST", client_ip, 200)
    
    try:
        # Check if update is available first
        update_available, latest_version, update_msg = version_checker.is_update_available()
        
        if not update_available:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.info(f"No update needed: {update_msg}")
            return {
                "status": "no_update_needed",
                "message": update_msg,
                "latest_version": latest_version,
                "timestamp": datetime.utcnow().isoformat(),
                "response_time_ms": duration
            }
        
        # Perform update
        success, message = version_checker.update_system()
        
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        if success:
            logger.info(f"Update completed: {message}")
            log_api_call("/api/v1/update", "POST", client_ip, 200, duration)
            return {
                "status": "updated",
                "message": message,
                "previous_version": version_checker.current_version,
                "timestamp": datetime.utcnow().isoformat(),
                "response_time_ms": duration
            }
        else:
            logger.error(f"Update failed: {message}")
            log_error(f"Update failed: {message}", context={"client_ip": client_ip, "duration_ms": duration})
            return {
                "status": "failed",
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "response_time_ms": duration
            }
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000  # Convert to milliseconds
        logger.error(f"Update endpoint error: {e}")
        log_error(f"Update endpoint error: {e}", exception=e, context={"client_ip": client_ip, "duration_ms": duration})
        raise HTTPException(status_code=500, detail="Unable to perform update")

@router.get("/qualities", summary="Get available quality options")
async def get_quality_options(platform: Optional[str] = None):
    """
    Get available quality options for a platform.
    If no platform is specified, returns all available options.
    """
    start_time = datetime.utcnow()
    
    try:
        if platform:
            qualities = quality_selector.get_quality_options(platform)
            result = {
                "platform": platform,
                "qualities": [q.value for q in qualities],
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            result = {
                "all_qualities": [q.value for q in QualityOption],
                "timestamp": datetime.utcnow().isoformat()
            }
        
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        log_api_call("/api/v1/qualities", "GET", "system", 200, duration)
        return result
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.error(f"Qualities endpoint error: {e}")
        log_error(f"Qualities endpoint error: {e}", exception=e, context={"duration_ms": duration})
        raise HTTPException(status_code=500, detail="Unable to fetch quality options")

@router.post("/convert", summary="Convert media format")
async def convert_media(
    input_file: str,
    target_format: FormatOption
):
    """
    Convert media file to target format.
    Input file should be a path to an existing file in the media folder.
    """
    start_time = datetime.utcnow()
    
    try:
        # Validate input file path to prevent directory traversal
        is_valid, error = security_validator.validate_media_path(settings.MEDIA_FOLDER, input_file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)
        
        input_path = os.path.join(settings.MEDIA_FOLDER, input_file)
        if not os.path.exists(input_path):
            raise HTTPException(status_code=404, detail="Input file not found")
        
        # Generate output filename
        file_base, file_ext = os.path.splitext(input_path)
        output_path = f"{file_base}.{target_format.value}"
        
        # Perform conversion
        success = format_converter.convert_file(input_path, output_path, target_format)
        
        if success:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            log_api_call("/api/v1/convert", "POST", "system", 200, duration)
            return {
                "status": "converted",
                "input_file": input_file,
                "output_file": os.path.basename(output_path),
                "target_format": target_format.value,
                "timestamp": datetime.utcnow().isoformat(),
                "response_time_ms": duration
            }
        else:
            raise HTTPException(status_code=500, detail="Conversion failed")
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.error(f"Media conversion error: {e}")
        log_error(f"Media conversion error: {e}", exception=e, context={"duration_ms": duration})
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

@router.get("/playlist-info", summary="Get playlist information")
async def get_playlist_info(url: HttpUrl):
    """
    Get information about a playlist.
    """
    start_time = datetime.utcnow()
    
    try:
        url_str = str(url)
        playlist_info = playlist_handler.get_playlist_info(url_str)
        
        if playlist_info:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            log_api_call("/api/v1/playlist-info", "GET", "system", 200, duration)
            return {
                "playlist": playlist_info.dict(),
                "timestamp": datetime.utcnow().isoformat(),
                "response_time_ms": duration
            }
        else:
            raise HTTPException(status_code=400, detail="URL is not a playlist or could not be processed")
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.error(f"Playlist info error: {e}")
        log_error(f"Playlist info error: {e}", exception=e, context={"duration_ms": duration})
        raise HTTPException(status_code=500, detail=f"Could not get playlist info: {str(e)}")

@router.get("/preferences", summary="Get user preferences")
async def get_user_preferences():
    """
    Get current user preferences.
    """
    start_time = datetime.utcnow()
    
    try:
        prefs = user_preferences.get_user_quality_options()
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        log_api_call("/api/v1/preferences", "GET", "system", 200, duration)
        return {
            "preferences": prefs,
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": duration
        }
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.error(f"User preferences error: {e}")
        log_error(f"User preferences error: {e}", exception=e, context={"duration_ms": duration})
        raise HTTPException(status_code=500, detail="Unable to fetch user preferences")

@router.get("/formats", response_model=FormatsResponse, summary="Get available video formats")
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

