from src.workers.celery_app import celery_app
from src.engine.platforms.tiktok import TikTokDownloader
from src.engine.platforms.youtube import YouTubeDownloader
from src.engine.platforms.instagram import InstagramDownloader
from src.engine.platforms.twitter import TwitterDownloader
from src.engine.platforms.reddit import RedditDownloader
from src.engine.platforms.soundcloud import SoundCloudDownloader
from src.engine.platforms.dailymotion import DailymotionDownloader
from src.engine.platforms.twitch import TwitchDownloader
from src.engine.platforms.vimeo import VimeoDownloader
from src.engine.platforms.facebook import FacebookDownloader
from src.engine.platforms.bilibili import BilibiliDownloader
from src.engine.platforms.linkedin import LinkedInDownloader
from src.engine.platforms.pinterest import PinterestDownloader
from src.core.config import settings
from loguru import logger
import asyncio
from httpx import RequestError

def get_downloader(url: str):
    """Return appropriate downloader based on URL"""
    url_lower = url.lower()
    
    if "tiktok.com" in url_lower or "vt.tiktok.com" in url_lower:
        return TikTokDownloader()
    elif "youtube.com" in url_lower or "youtu.be" in url_lower:
        return YouTubeDownloader()
    elif "instagram.com" in url_lower:
        return InstagramDownloader()
    elif "twitter.com" in url_lower or "x.com" in url_lower or "t.co" in url_lower:
        return TwitterDownloader()
    elif "reddit.com" in url_lower or "redd.it" in url_lower:
        return RedditDownloader()
    elif "soundcloud.com" in url_lower:
        return SoundCloudDownloader()
    elif "dailymotion.com" in url_lower or "dai.ly" in url_lower:
        return DailymotionDownloader()
    elif "twitch.tv" in url_lower:
        return TwitchDownloader()
    elif "vimeo.com" in url_lower:
        return VimeoDownloader()
    elif "facebook.com" in url_lower or "fb.watch" in url_lower:
        return FacebookDownloader()
    elif "bilibili.com" in url_lower or "b23.tv" in url_lower:
        return BilibiliDownloader()
    elif "linkedin.com" in url_lower:
        return LinkedInDownloader()
    elif "pinterest.com" in url_lower or "pin.it" in url_lower:
        return PinterestDownloader()
    else:
        raise ValueError(f"No downloader found for URL: {url}. Supported platforms: TikTok, YouTube, Instagram, Twitter/X, Reddit, SoundCloud, Dailymotion, Twitch, Vimeo, Facebook, Bilibili, LinkedIn, Pinterest")

def detect_platform(url: str) -> str:
    """Detect platform from URL"""
    url_lower = url.lower()
    
    if "tiktok.com" in url_lower or "vt.tiktok.com" in url_lower:
        return "tiktok"
    elif "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "youtube"
    elif "instagram.com" in url_lower:
        return "instagram"
    elif "twitter.com" in url_lower or "x.com" in url_lower:
        return "twitter"
    elif "reddit.com" in url_lower or "redd.it" in url_lower:
        return "reddit"
    elif "soundcloud.com" in url_lower:
        return "soundcloud"
    elif "dailymotion.com" in url_lower or "dai.ly" in url_lower:
        return "dailymotion"
    elif "twitch.tv" in url_lower:
        return "twitch"
    elif "vimeo.com" in url_lower:
        return "vimeo"
    elif "facebook.com" in url_lower or "fb.watch" in url_lower:
        return "facebook"
    elif "bilibili.com" in url_lower or "b23.tv" in url_lower:
        return "bilibili"
    elif "linkedin.com" in url_lower:
        return "linkedin"
    elif "pinterest.com" in url_lower or "pin.it" in url_lower:
        return "pinterest"
    else:
        return "unknown"

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
    platform = detect_platform(url)
    
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
        
        downloader = get_downloader(url)
        
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

