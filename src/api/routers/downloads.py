from fastapi import APIRouter, HTTPException, Depends, Request
from src.api.schemas import DownloadRequest, DownloadResponse, TaskStatusResponse, DownloadHistoryResponse
from src.workers.tasks import download_media_task
from src.workers.celery_app import celery_app
from src.database.base import get_db
from src.database.models import DownloadHistory, TaskStatus, PlatformType
from sqlalchemy.orm import Session
from celery.result import AsyncResult
from pydantic import HttpUrl
from datetime import datetime
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import List, Optional
import os
import hashlib
from fastapi.responses import FileResponse
from src.utils.logging.logger import log_api_call, log_download_event, log_error
from src.core.platform_registry import PlatformRegistry

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
    """
    start_time = datetime.utcnow()
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    log_api_call("/api/v1/download", "POST", client_ip, 200)

    if not download_request.url:
        log_error("Missing URL in download request", context={"client_ip": client_ip})
        raise HTTPException(status_code=400, detail="URL is required")

    url = str(download_request.url)
    platform = PlatformRegistry.detect_platform(url)

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
    """
    start_time = datetime.utcnow()
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    log_api_call("/api/v1/download", "GET", client_ip, 200)

    url_str = str(url)
    platform = PlatformRegistry.detect_platform(url_str)

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

    platform = PlatformRegistry.detect_platform(url_str)

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
        task_id="sync_" + hashlib.md5(url_str.encode()).hexdigest()[:24],
        url=url_str,
        platform=PlatformType[platform.upper()],
        status=TaskStatus.PENDING,
        ip_address=client_ip,
        user_agent=user_agent
    )

    try:
        # Get appropriate downloader
        try:
            downloader = PlatformRegistry.get_downloader(url_str)
        except ValueError:
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
