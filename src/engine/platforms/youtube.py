from typing import Any, Dict, Optional
import json
import os
import yt_dlp
from src.engine.base_downloader import BaseDownloader
from src.core.config import settings
from src.utils.cookie_manager import cookie_manager
from src.utils.exceptions import handle_platform_exception
from loguru import logger


class YouTubeDownloader(BaseDownloader):
    @property
    def platform(self) -> str:
        return "youtube"
    
    async def get_formats(self, url: str) -> Dict[str, Any]:
        """Get available formats for a YouTube video without downloading
        
        Args:
            url: YouTube video URL
            
        Returns:
            Dict containing video metadata and available formats
        """
        import random
        import time
        
        try:
            logger.info(f"[{self.platform}] Fetching formats for: {url}")
            
            # Add human-like delay before request
            delay = random.uniform(1.0, 3.0)  # Random delay 1-3 seconds
            logger.info(f"[{self.platform}] Waiting {delay:.2f}s before request to mimic human behavior")
            time.sleep(delay)
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'remote_components': 'ejs:github',  # Enable EJS for challenge solving
                'extractor_args': {
                    'youtube': {
                        'player_client': ['tv_embedded', 'web'],
                    }
                },
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0',
                }
            }
            
            # Add cookies file if exists using centralized cookie manager
            cookie_options = cookie_manager.get_ytdlp_options(self.platform)
            ydl_opts.update(cookie_options)
            
            if cookie_options:
                logger.info(f"[{self.platform}] Using cookies for format detection")
            
            # Add retry mechanism for captcha errors in format detection
            import random
            import time
            max_retries = 3
            retry_delay = 2  # Start with 2 seconds
            
            for attempt in range(max_retries):
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        
                        if not info:
                            raise ValueError("Failed to extract video information")
                        break  # Success, exit retry loop
                        
                except Exception as e:
                    if "captcha" in str(e).lower() or "152 - 18" in str(e):
                        if attempt < max_retries - 1:  # Not the last attempt
                            delay = retry_delay * (2 ** attempt) + random.uniform(1, 3)  # Exponential backoff + jitter
                            logger.warning(f"[{self.platform}] Captcha detected in format detection, retrying in {delay:.2f}s...")
                            time.sleep(delay)
                            continue
                        else:
                            raise  # Re-raise the last exception
                    else:
                        raise  # Re-raise if it's not a captcha error
                
                # Extract metadata
                video_id = info.get('id')
                title = info.get('title')
                thumbnail = info.get('thumbnail')
                duration = info.get('duration', 0)
                
                # Process available formats
                formats = []
                seen_heights = set()
                seen_audio = False
                
                # First, collect video formats
                for fmt in info.get('formats', []):
                    height = fmt.get('height')
                    vcodec = fmt.get('vcodec', 'unknown')
                    acodec = fmt.get('acodec', 'none')
                    ext = fmt.get('ext', 'mp4')
                    filesize = fmt.get('filesize')
                    format_note = fmt.get('format_note', '')
                    
                    # Include video formats with height info
                    if height and vcodec and vcodec != 'none':
                        # Skip duplicate heights (keep only best for each resolution)
                        if height in seen_heights:
                            continue
                        
                        seen_heights.add(height)
                        formats.append({
                            'format_id': fmt.get('format_id', 'unknown'),
                            'quality': f"{height}p",
                            'ext': ext,
                            'filesize_mb': round(filesize / (1024 * 1024), 2) if filesize else None,
                            'height': height,
                            'width': fmt.get('width'),
                            'fps': fmt.get('fps'),
                            'vcodec': vcodec,
                            'acodec': acodec,
                            'format_note': format_note if format_note else None
                        })
                    
                    # Include audio-only formats (best quality audio)
                    elif not seen_audio and vcodec == 'none' and acodec and acodec != 'none':
                        # Get the best audio format
                        if 'm4a' in ext or 'mp3' in ext or 'webm' in ext:
                            seen_audio = True
                            formats.append({
                                'format_id': fmt.get('format_id', 'audio'),
                                'quality': 'audio',
                                'ext': ext,
                                'filesize_mb': round(filesize / (1024 * 1024), 2) if filesize else None,
                                'height': None,
                                'width': None,
                                'fps': None,
                                'vcodec': 'none',
                                'acodec': acodec,
                                'format_note': 'audio only'
                            })
                
                # If no formats found, try requested_formats
                if not formats and info.get('requested_formats'):
                    for fmt in info.get('requested_formats', []):
                        height = fmt.get('height')
                        filesize = fmt.get('filesize')
                        if height:
                            formats.append({
                                'format_id': fmt.get('format_id', 'unknown'),
                                'quality': f"{height}p",
                                'ext': fmt.get('ext', 'mp4'),
                                'filesize_mb': round(filesize / (1024 * 1024), 2) if filesize else None,
                                'height': height,
                                'width': fmt.get('width'),
                                'fps': fmt.get('fps'),
                                'vcodec': fmt.get('vcodec', 'unknown'),
                                'acodec': fmt.get('acodec', 'none'),
                                'format_note': None
                            })
                
                # Sort: video formats by height descending, then audio at the end
                formats.sort(key=lambda x: (x['height'] if x['height'] else -1), reverse=True)
                
                logger.info(f"[{self.platform}] Found {len(formats)} unique formats (including audio)")
                
                return {
                    'platform': 'youtube',
                    'url': url,
                    'title': title,
                    'thumbnail': thumbnail,
                    'duration': duration,
                    'formats': formats
                }
                
        except Exception as e:
            logger.error(f"[{self.platform}] Error fetching formats: {e}")
            # Convert to standardized exception
            raise handle_platform_exception(self.platform, url, e)
    
    async def download(self, url: str, quality: str = "720p") -> Dict[str, Any]:
        """Download YouTube video using yt-dlp library
        
        Args:
            url: YouTube video URL
            quality: Desired video quality (e.g., "720p", "480p", "360p", "1080p", "audio")
        
        Note: When downloading video, audio-only version is also downloaded automatically
        """
        import random
        import time
        
        try:
            logger.info(f"[{self.platform}] Processing URL: {url} (requested quality: {quality})")
            
            # Add human-like delay before request
            delay = random.uniform(1.5, 4.0)  # Random delay 1.5-4 seconds
            logger.info(f"[{self.platform}] Waiting {delay:.2f}s before download request to mimic human behavior")
            time.sleep(delay)
            
            # Check if audio-only is requested
            is_audio_only = quality.lower() == 'audio'
            
            # Get video metadata first
            ydl_opts_info = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'remote_components': 'ejs:github',  # Enable EJS for challenge solving
                'extractor_args': {
                    'youtube': {
                        'player_client': ['tv_embedded', 'web'],
                    }
                },
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0',
                }
            }
            
            # Add cookies file if exists using centralized cookie manager
            cookie_options = cookie_manager.get_ytdlp_options(self.platform)
            ydl_opts_info.update(cookie_options)
            
            if cookie_options:
                logger.info(f"[{self.platform}] Using cookies for metadata extraction")
            
            # Add retry mechanism for captcha errors
            import random
            import time
            max_retries = 3
            retry_delay = 2  # Start with 2 seconds
            
            for attempt in range(max_retries):
                try:
                    with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                        logger.info(f"[{self.platform}] Extracting video information (attempt {attempt + 1})...")
                        info = ydl.extract_info(url, download=False)
                        
                        if not info:
                            raise ValueError("Failed to extract video information")
                        break  # Success, exit retry loop
                        
                except Exception as e:
                    if "captcha" in str(e).lower() or "152 - 18" in str(e):
                        if attempt < max_retries - 1:  # Not the last attempt
                            delay = retry_delay * (2 ** attempt) + random.uniform(1, 3)  # Exponential backoff + jitter
                            logger.warning(f"[{self.platform}] Captcha detected, retrying in {delay:.2f}s...")
                            time.sleep(delay)
                            continue
                        else:
                            raise  # Re-raise the last exception
                    else:
                        raise  # Re-raise if it's not a captcha error
                
                # Get video metadata
                video_id = info.get('id')
                title = info.get('title')
                uploader = info.get('uploader') or info.get('channel')
                channel_id = info.get('channel_id')
                description = info.get('description', '')
                thumbnail = info.get('thumbnail')
                view_count = info.get('view_count', 0)
                like_count = info.get('like_count', 0)
                duration = info.get('duration', 0)
            
            # Prepare download list
            downloads = []
            
            if is_audio_only:
                # Only download audio
                downloads.append({
                    'type': 'audio',
                    'opts': {
                        'format': 'bestaudio[ext=m4a]/bestaudio/best',
                        'quiet': True,
                        'no_warnings': True,
                        'outtmpl': os.path.join(settings.MEDIA_FOLDER, f'{video_id}_audio.%(ext)s'),
                        'remote_components': 'ejs:github',  # Enable EJS for challenge solving
                        'extractor_args': {
                            'youtube': {
                                'player_client': ['tv_embedded', 'web'],
                            }
                        },
                        'http_headers': {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                            'Accept-Language': 'en-US,en;q=0.5',
                            'Accept-Encoding': 'gzip, deflate',
                            'Connection': 'keep-alive',
                            'Upgrade-Insecure-Requests': '1',
                            'Sec-Fetch-Dest': 'document',
                            'Sec-Fetch-Mode': 'navigate',
                            'Sec-Fetch-Site': 'none',
                            'Cache-Control': 'max-age=0',
                        }
                    }
                })
            else:
                # Download both video and audio
                max_height = int(quality.replace('p', '')) if quality and quality != 'auto' else 9999
                
                # 1. Video with audio merged - with multiple fallback options
                # Try specific height first, then fallback to best available
                format_string = (
                    f'bestvideo[height<={max_height}][ext=mp4]+bestaudio[ext=m4a]/'
                    f'bestvideo[height<={max_height}]+bestaudio/'
                    f'best[height<={max_height}]/'
                    f'bestvideo[ext=mp4]+bestaudio[ext=m4a]/'
                    f'bestvideo+bestaudio/'
                    f'best'
                )
                
                downloads.append({
                    'type': 'video',
                    'opts': {
                        'format': format_string,
                        'quiet': True,
                        'no_warnings': True,
                        'merge_output_format': 'mp4',
                        'outtmpl': os.path.join(settings.MEDIA_FOLDER, f'{video_id}.%(ext)s'),
                        'remote_components': 'ejs:github',  # Enable EJS for challenge solving
                        'extractor_args': {
                            'youtube': {
                                'player_client': ['tv_embedded', 'web'],
                            }
                        },
                        'http_headers': {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                            'Accept-Language': 'en-US,en;q=0.5',
                            'Accept-Encoding': 'gzip, deflate',
                            'Connection': 'keep-alive',
                            'Upgrade-Insecure-Requests': '1',
                            'Sec-Fetch-Dest': 'document',
                            'Sec-Fetch-Mode': 'navigate',
                            'Sec-Fetch-Site': 'none',
                            'Cache-Control': 'max-age=0',
                        }
                    }
                })
                
                # 2. Audio-only with fallback
                downloads.append({
                    'type': 'audio',
                    'opts': {
                        'format': 'bestaudio[ext=m4a]/bestaudio/best',
                        'quiet': True,
                        'no_warnings': True,
                        'outtmpl': os.path.join(settings.MEDIA_FOLDER, f'{video_id}_audio.%(ext)s'),
                        'remote_components': 'ejs:github',  # Enable EJS for challenge solving
                        'extractor_args': {
                            'youtube': {
                                'player_client': ['tv_embedded', 'web'],
                            }
                        },
                        'http_headers': {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                            'Accept-Language': 'en-US,en;q=0.5',
                            'Accept-Encoding': 'gzip, deflate',
                            'Connection': 'keep-alive',
                            'Upgrade-Insecure-Requests': '1',
                            'Sec-Fetch-Dest': 'document',
                            'Sec-Fetch-Mode': 'navigate',
                            'Sec-Fetch-Site': 'none',
                            'Cache-Control': 'max-age=0',
                        }
                    }
                })
            
            # Download all formats
            downloaded_files = []
            import random
            import time
            
            for i, download_info in enumerate(downloads):
                logger.info(f"[{self.platform}] Downloading {download_info['type']}...")
                
                # Add delay between format downloads to mimic human behavior
                if i > 0:  # Only add delay after the first download
                    delay = random.uniform(0.5, 2.0)  # Random delay 0.5-2 seconds between downloads
                    logger.info(f"[{self.platform}] Waiting {delay:.2f}s between downloads")
                    time.sleep(delay)
                
                # Add cookies to download options using centralized manager
                download_cookie_options = cookie_manager.get_ytdlp_options(self.platform)
                download_info['opts'].update(download_cookie_options)
                
                # Add retry mechanism for captcha errors during download
                max_retries = 2
                retry_delay = 3  # Start with 3 seconds for downloads
                
                for attempt in range(max_retries):
                    try:
                        with yt_dlp.YoutubeDL(download_info['opts']) as ydl:
                            ydl.download([url])
                        break  # Success, exit retry loop
                        
                    except Exception as e:
                        if "captcha" in str(e).lower() or "152 - 18" in str(e):
                            if attempt < max_retries - 1:  # Not the last attempt
                                delay = retry_delay * (2 ** attempt) + random.uniform(1, 2)  # Exponential backoff + jitter
                                logger.warning(f"[{self.platform}] Captcha detected during {download_info['type']} download, retrying in {delay:.2f}s...")
                                time.sleep(delay)
                                continue
                            else:
                                raise  # Re-raise the last exception
                        else:
                            raise  # Re-raise if it's not a captcha error
                downloaded_files.append(download_info['type'])
            
            # Build response with all downloaded files
            media_data = []
            
            # Check for video file (now with simpler filename pattern)
            if not is_audio_only:
                # Try to find video file with various extensions
                for ext in ['mp4', 'webm', 'mkv']:
                    video_filename = f"{video_id}.{ext}"
                    video_filepath = os.path.join(settings.MEDIA_FOLDER, video_filename)
                    if os.path.exists(video_filepath):
                        file_size_mb = os.path.getsize(video_filepath) / (1024 * 1024)
                        logger.info(f"[{self.platform}] Video download complete: {file_size_mb:.2f} MB")
                        
                        # Try to detect actual quality from file metadata if possible
                        actual_quality = quality if quality else "best"
                        
                        media_data.append({
                            'quality': actual_quality,
                            'format_id': 'video+audio',
                            'ext': ext,
                            'url': f"{settings.API_BASE_URL}/{settings.MEDIA_FOLDER}/{video_filename}",
                            'downloaded': True,
                            'height': max_height if max_height != 9999 else None,
                            'type': 'video'
                        })
                        break
            
            # Check for audio file
            audio_filename = f"{video_id}_audio.m4a"
            audio_filepath = os.path.join(settings.MEDIA_FOLDER, audio_filename)
            if os.path.exists(audio_filepath):
                file_size_mb = os.path.getsize(audio_filepath) / (1024 * 1024)
                logger.info(f"[{self.platform}] Audio download complete: {file_size_mb:.2f} MB")
                media_data.append({
                    'quality': 'audio',
                    'format_id': 'audio',
                    'ext': 'm4a',
                    'url': f"{settings.API_BASE_URL}/{settings.MEDIA_FOLDER}/{audio_filename}",
                    'downloaded': True,
                    'height': None,
                    'type': 'audio'
                })
            
            # Return structured data
            data = {
                "platform": "youtube",
                "id": video_id,
                "title": title,
                "caption": description,
                "created_at": None,
                "duration": duration,
                "author": {
                    "username": uploader,
                    "channel_id": channel_id,
                    "profile_url": f"https://www.youtube.com/channel/{channel_id}" if channel_id else None,
                },
                "statistics": {
                    "views": view_count,
                    "likes": like_count,
                },
                "media": {
                    "video": media_data,
                    "thumbnail": thumbnail
                }
            }
            
            logger.info(f"[{self.platform}] Processing complete. Downloaded {len(media_data)} files")
            return data
                
        except Exception as e:
            logger.error(f"[{self.platform}] Error: {e}")
            raise