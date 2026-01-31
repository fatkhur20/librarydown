from src.workers.celery_app import celery_app
from src.core.platform_registry import PlatformRegistry
from src.core.config import settings
from src.utils.token_refresher import refresh_youtube_tokens
from loguru import logger
import asyncio
from httpx import RequestError

@celery_app.task(bind=True, name="refresh_youtube_tokens_task")
def refresh_youtube_tokens_task(self):
    """
    Celery task to refresh YouTube tokens (PoToken, Visitor Data, Cookies).
    Scheduled to run periodically.
    """
    logger.info("[Task] Starting scheduled YouTube token refresh...")
    try:
        success = asyncio.run(refresh_youtube_tokens())
        if success:
            logger.info("[Task] YouTube token refresh successful")
            return "SUCCESS"
        else:
            logger.error("[Task] YouTube token refresh failed")
            return "FAILURE"
    except Exception as e:
        logger.error(f"[Task] Error in token refresh task: {e}")
        return f"ERROR: {str(e)}"

@celery_app.task(
    bind=True,
    autoretry_for=(RequestError, ConnectionError),
    retry_kwargs={
        'max_retries': settings.MAX_RETRIES,
        'countdown': settings.RETRY_BACKOFF
    },
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def download_media_task(self, url: str, quality: str = "720p"):
    """
    Celery task to download media from a given URL.
    Supports: TikTok, YouTube, Instagram, Twitter/X, Reddit, SoundCloud, Dailymotion, Twitch, Vimeo, Facebook, Bilibili, LinkedIn, Pinterest
    
    Args:
        url: The URL to download
        quality: Desired video quality (default: 720p)
    
    Features:
    - Automatic retry with exponential backoff
    - Progress tracking
    - Error handling
    - Quality selection
    """
    task_id = self.request.id
    platform = PlatformRegistry.detect_platform(url)
    
    logger.info(f"[Task {task_id}] Starting download for {platform}: {url} (quality: {quality})")
    self.update_state(
        state='PROGRESS',
        meta={
            'status': 'Initializing download...',
            'platform': platform,
            'url': url,
            'quality': quality,
            'progress': 10
        }
    )
    
    try:
        # Get appropriate downloader
        self.update_state(
            state='PROGRESS',
            meta={
                'status': f'Fetching content from {platform}...',
                'platform': platform,
                'quality': quality,
                'progress': 30
            }
        )
        
        downloader = PlatformRegistry.get_downloader(url)
        
        # Download media with quality parameter
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'Downloading media files...',
                'platform': platform,
                'quality': quality,
                'progress': 60
            }
        )
        
        # Pass quality to downloader
        data = asyncio.run(downloader.download(url, quality=quality))
        
        # Success
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'Processing complete!',
                'platform': platform,
                'progress': 100
            }
        )
        
        logger.info(f"[Task {task_id}] Download completed successfully")
        return {
            'status': 'SUCCESS',
            'platform': platform,
            'data': data
        }
        
    except ValueError as e:
        # Content not available or unsupported platform
        error_msg = str(e)
        logger.error(f"[Task {task_id}] ValueError: {error_msg}")
        raise
        
    except NotImplementedError as e:
        # Platform not fully implemented
        error_msg = str(e)
        logger.warning(f"[Task {task_id}] NotImplementedError: {error_msg}")
        raise
        
    except RequestError as e:
        # Network error - will auto-retry
        error_msg = f"Network error: {str(e)}"
        logger.error(f"[Task {task_id}] RequestError (attempt {self.request.retries + 1}/{settings.MAX_RETRIES}): {error_msg}")
        raise
        
    except Exception as e:
        # Unexpected error
        error_msg = f"Unexpected error: {str(e)}"
        logger.exception(f"[Task {task_id}] Unexpected exception: {error_msg}")
        raise

