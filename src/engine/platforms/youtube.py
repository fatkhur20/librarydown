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
        try:
            logger.info(f"[{self.platform}] Fetching formats for: {url}")
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
            }
            
            # Add cookies file if exists using centralized cookie manager
            cookie_options = cookie_manager.get_ytdlp_options(self.platform)
            ydl_opts.update(cookie_options)
            
            if cookie_options:
                logger.info(f"[{self.platform}] Using cookies for format detection")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    raise ValueError("Failed to extract video information")
                
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
        try:
            logger.info(f"[{self.platform}] Processing URL: {url} (requested quality: {quality})")
            
            # Check if audio-only is requested
            is_audio_only = quality.lower() == 'audio'
            
            # Get video metadata first
            ydl_opts_info = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
            }
            
            # Add cookies file if exists using centralized cookie manager
            cookie_options = cookie_manager.get_ytdlp_options(self.platform)
            ydl_opts_info.update(cookie_options)
            
            if cookie_options:
                logger.info(f"[{self.platform}] Using cookies for metadata extraction")
            
            with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                logger.info(f"[{self.platform}] Extracting video information...")
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    raise ValueError("Failed to extract video information")
                
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
                    }
                })
            else:
                # Download both video and audio
                max_height = int(quality.replace('p', '')) if quality else 720
                
                # 1. Video with audio merged
                downloads.append({
                    'type': 'video',
                    'opts': {
                        'format': f'bestvideo[height<={max_height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={max_height}]/best',
                        'quiet': True,
                        'no_warnings': True,
                        'merge_output_format': 'mp4',
                        'outtmpl': os.path.join(settings.MEDIA_FOLDER, f'{video_id}_%(height)sp.%(ext)s'),
                    }
                })
                
                # 2. Audio-only
                downloads.append({
                    'type': 'audio',
                    'opts': {
                        'format': 'bestaudio[ext=m4a]/bestaudio/best',
                        'quiet': True,
                        'no_warnings': True,
                        'outtmpl': os.path.join(settings.MEDIA_FOLDER, f'{video_id}_audio.%(ext)s'),
                    }
                })
            
            # Download all formats
            downloaded_files = []
            for download_info in downloads:
                logger.info(f"[{self.platform}] Downloading {download_info['type']}...")
                
                # Add cookies to download options using centralized manager
                download_cookie_options = cookie_manager.get_ytdlp_options(self.platform)
                download_info['opts'].update(download_cookie_options)
                
                with yt_dlp.YoutubeDL(download_info['opts']) as ydl:
                    ydl.download([url])
                downloaded_files.append(download_info['type'])
            
            # Build response with all downloaded files
            media_data = []
            
            # Check for video file
            if not is_audio_only:
                # Find the video file
                for possible_height in [max_height, max_height - 10, max_height + 10]:  # Check nearby heights
                    video_filename = f"{video_id}_{possible_height}p.mp4"
                    video_filepath = os.path.join(settings.MEDIA_FOLDER, video_filename)
                    if os.path.exists(video_filepath):
                        file_size_mb = os.path.getsize(video_filepath) / (1024 * 1024)
                        logger.info(f"[{self.platform}] Video download complete: {file_size_mb:.2f} MB")
                        media_data.append({
                            'quality': f"{possible_height}p",
                            'format_id': 'video+audio',
                            'ext': 'mp4',
                            'url': f"{settings.API_BASE_URL}/{settings.MEDIA_FOLDER}/{video_filename}",
                            'downloaded': True,
                            'height': possible_height,
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
