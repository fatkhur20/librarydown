from typing import Any, Dict, Optional, List
import json
import os
import yt_dlp
from src.engine.base_downloader import BaseDownloader
from src.core.config import settings
from loguru import logger


class InstagramDownloader(BaseDownloader):
    @property
    def platform(self) -> str:
        return "instagram"
    
    async def get_formats(self, url: str) -> Dict[str, Any]:
        """Get available formats for Instagram content without downloading
        
        Args:
            url: Instagram post/reel URL
            
        Returns:
            Dict containing video metadata and available formats
        """
        try:
            logger.info(f"[{self.platform}] Fetching formats for: {url}")
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
            }
            
            # Add cookies file if exists (copy to temp to avoid permission issues)
            # Try both possible cookie locations
            cookies_path = '/opt/librarydown/cookies/instagram_cookies.txt'
            if not os.path.exists(cookies_path):
                cookies_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'cookies', 'instagram_cookies.txt')
            
            if os.path.exists(cookies_path):
                import shutil
                import tempfile
                temp_cookies = os.path.join(tempfile.gettempdir(), 'ig_cookies_librarydown.txt')
                shutil.copy2(cookies_path, temp_cookies)
                os.chmod(temp_cookies, 0o644)
                ydl_opts['cookiefile'] = temp_cookies
                logger.info(f"[{self.platform}] Using cookies from: {cookies_path}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    raise ValueError("Failed to extract Instagram data")
                
                # Extract metadata
                title = info.get('title')
                thumbnail = info.get('thumbnail')
                duration = info.get('duration', 0)
                
                formats = []
                
                # Instagram usually provides single quality
                formats.append({
                    'format_id': 'default',
                    'quality': 'highest',
                    'ext': 'mp4',
                    'filesize_mb': None,
                    'height': info.get('height'),
                    'width': info.get('width'),
                    'fps': info.get('fps'),
                    'vcodec': 'h264',
                    'acodec': 'aac',
                    'format_note': 'video + audio'
                })
                
                # Audio-only option
                formats.append({
                    'format_id': 'audio',
                    'quality': 'audio',
                    'ext': 'm4a',
                    'filesize_mb': None,
                    'height': None,
                    'width': None,
                    'fps': None,
                    'vcodec': 'none',
                    'acodec': 'aac',
                    'format_note': 'audio only'
                })
                
                logger.info(f"[{self.platform}] Found {len(formats)} formats")
                
                return {
                    'platform': 'instagram',
                    'url': url,
                    'title': title,
                    'thumbnail': thumbnail,
                    'duration': duration,
                    'formats': formats
                }
                
        except Exception as e:
            logger.error(f"[{self.platform}] Error fetching formats: {e}")
            raise
    
    async def download(self, url: str, quality: str = "720p") -> Dict[str, Any]:
        """
        Download Instagram content using yt-dlp library
        
        Args:
            url: Instagram post/reel URL
            quality: "highest" for best quality, or "audio" for audio-only
        
        Returns:
            Dict with metadata and download URLs
        """
        try:
            logger.info(f"[{self.platform}] Processing URL: {url} (quality: {quality})")
            
            is_audio_only = quality.lower() == 'audio'
            
            # Get metadata first
            ydl_opts_info = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
            }
            
            # Add cookies file if exists (copy to temp to avoid permission issues)
            # Try both possible cookie locations
            cookies_path = '/opt/librarydown/cookies/instagram_cookies.txt'
            if not os.path.exists(cookies_path):
                cookies_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'cookies', 'instagram_cookies.txt')
            
            if os.path.exists(cookies_path):
                import shutil
                import tempfile
                temp_cookies = os.path.join(tempfile.gettempdir(), 'ig_cookies_librarydown.txt')
                shutil.copy2(cookies_path, temp_cookies)
                os.chmod(temp_cookies, 0o644)
                ydl_opts_info['cookiefile'] = temp_cookies
                logger.info(f"[{self.platform}] Using cookies for download from: {cookies_path}")
            
            with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                logger.info(f"[{self.platform}] Extracting metadata...")
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    raise ValueError("Failed to extract Instagram data")
                
                # Get metadata
                video_id = info.get('id')
                title = info.get('title')
                uploader = info.get('uploader')
                uploader_id = info.get('uploader_id')
                description = info.get('description', '')
                thumbnail = info.get('thumbnail')
                view_count = info.get('view_count', 0)
                like_count = info.get('like_count', 0)
                comment_count = info.get('comment_count', 0)
                duration = info.get('duration', 0)
                timestamp = info.get('timestamp')
            
            # Prepare downloads
            downloads = []
            downloaded_media = []
            
            # Prepare cookies path for download opts
            temp_cookies = os.path.join(tempfile.gettempdir(), 'ig_cookies_librarydown.txt')
            
            if is_audio_only:
                # Only download audio
                download_opts = {
                    'format': 'bestaudio/best',
                    'quiet': True,
                    'no_warnings': True,
                    'outtmpl': os.path.join(settings.MEDIA_FOLDER, f'{video_id}_audio.%(ext)s'),
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'm4a',
                    }],
                }
                if os.path.exists(temp_cookies):
                    download_opts['cookiefile'] = temp_cookies
                downloads.append({'type': 'audio', 'opts': download_opts})
            else:
                # Download video
                video_opts = {
                    'format': 'best',
                    'quiet': True,
                    'no_warnings': True,
                    'outtmpl': os.path.join(settings.MEDIA_FOLDER, f'{video_id}.%(ext)s'),
                }
                if os.path.exists(temp_cookies):
                    video_opts['cookiefile'] = temp_cookies
                downloads.append({'type': 'video', 'opts': video_opts})
                
                # Also download audio
                audio_opts = {
                    'format': 'bestaudio/best',
                    'quiet': True,
                    'no_warnings': True,
                    'outtmpl': os.path.join(settings.MEDIA_FOLDER, f'{video_id}_audio.%(ext)s'),
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'm4a',
                    }],
                }
                if os.path.exists(temp_cookies):
                    audio_opts['cookiefile'] = temp_cookies
                downloads.append({'type': 'audio', 'opts': audio_opts})
            
            # Download all formats
            for download_info in downloads:
                logger.info(f"[{self.platform}] Downloading {download_info['type']}...")
                with yt_dlp.YoutubeDL(download_info['opts']) as ydl:
                    ydl.download([url])
            
            # Check downloaded files
            if not is_audio_only:
                # Video file
                video_filename = f"{video_id}.mp4"
                video_filepath = os.path.join(settings.MEDIA_FOLDER, video_filename)
                if os.path.exists(video_filepath):
                    file_size_mb = os.path.getsize(video_filepath) / (1024 * 1024)
                    logger.info(f"[{self.platform}] Video download complete: {file_size_mb:.2f} MB")
                    downloaded_media.append({
                        'quality': 'highest',
                        'format_id': 'video',
                        'ext': 'mp4',
                        'url': f"{settings.API_BASE_URL}/{settings.MEDIA_FOLDER}/{video_filename}",
                        'downloaded': True,
                        'height': info.get('height'),
                        'width': info.get('width'),
                        'type': 'video',
                        'duration': duration
                    })
            
            # Audio file
            audio_filename = f"{video_id}_audio.m4a"
            audio_filepath = os.path.join(settings.MEDIA_FOLDER, audio_filename)
            if os.path.exists(audio_filepath):
                file_size_mb = os.path.getsize(audio_filepath) / (1024 * 1024)
                logger.info(f"[{self.platform}] Audio download complete: {file_size_mb:.2f} MB")
                downloaded_media.append({
                    'quality': 'audio',
                    'format_id': 'audio',
                    'ext': 'm4a',
                    'url': f"{settings.API_BASE_URL}/{settings.MEDIA_FOLDER}/{audio_filename}",
                    'downloaded': True,
                    'height': None,
                    'width': None,
                    'type': 'audio',
                    'duration': duration
                })
            
            # Build response
            result = {
                "platform": "instagram",
                "id": video_id,
                "title": title,
                "caption": description,
                "created_at": timestamp,
                "duration": duration,
                "author": {
                    "username": uploader_id,
                    "display_name": uploader,
                    "profile_url": f"https://www.instagram.com/{uploader_id}" if uploader_id else None,
                    "is_verified": False,
                },
                "statistics": {
                    "likes": like_count,
                    "comments": comment_count,
                    "views": view_count,
                },
                "media": {
                    "video": downloaded_media,
                    "thumbnail": thumbnail
                }
            }
            
            logger.info(f"[{self.platform}] Processing complete. Downloaded {len(downloaded_media)} files")
            return result
                
        except Exception as e:
            logger.error(f"[{self.platform}] Error: {e}")
            raise
