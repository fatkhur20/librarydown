from typing import Any, Dict, Optional
from src.engine.base_downloader import BaseDownloader
from loguru import logger


class TwitchDownloader(BaseDownloader):
    @property
    def platform(self) -> str:
        return "twitch"
    
    async def get_formats(self, url: str) -> Dict[str, Any]:
        """Twitch downloader requires valid VOD/clip IDs
        
        Args:
            url: Twitch video or clip URL
            
        Raises:
            NotImplementedError: Twitch requires valid video/clip IDs and may have authentication requirements
        """
        raise NotImplementedError(
            "Twitch downloader requires valid VOD or clip IDs and may need authentication. "
            "\n\nAlternative solutions:"
            "\n1. Use third-party services:"
            "\n   - TwitchDown: https://twitchdown.com/"
            "\n   - Clipr: https://clipr.xyz/"
            "\n   - Twitch Leecher: https://github.com/Franiac/TwitchLeecher"
            "\n\n2. Browser extensions:"
            "\n   - Twitch Video Downloader"
            "\n   - Video DownloadHelper"
            "\n\n3. Command-line tools:"
            "\n   - twitch-dl: pip install twitch-dl && twitch-dl download <video_id>"
            "\n   - streamlink: streamlink <twitch_url> best -o output.mp4"
            "\n   - yt-dlp: yt-dlp <twitch_url>"
            "\n\n4. Desktop applications:"
            "\n   - TwitchLeecher (Windows)"
            "\n   - 4K Video Downloader"
            "\n\nNote: "
            "\n- VODs may expire after 14-60 days depending on subscription"
            "\n- Subscriber-only content requires authentication"
            "\n- Some clips may be deleted by creators"
            "\n\nTwitch support will be improved in future versions with proper authentication handling."
        )
    
    async def download(self, url: str, quality: str = "720p") -> Dict[str, Any]:
        """Twitch downloader requires valid VOD/clip IDs
        
        Args:
            url: Twitch video or clip URL
            quality: Desired video quality
            
        Raises:
            NotImplementedError: Twitch requires valid video/clip IDs and may have authentication requirements
        """
        raise NotImplementedError(
            "Twitch downloader requires valid VOD or clip IDs and may need authentication. "
            "\n\nAlternative solutions:"
            "\n1. Use third-party services:"
            "\n   - TwitchDown: https://twitchdown.com/"
            "\n   - Clipr: https://clipr.xyz/"
            "\n   - Twitch Leecher: https://github.com/Franiac/TwitchLeecher"
            "\n\n2. Browser extensions:"
            "\n   - Twitch Video Downloader"
            "\n   - Video DownloadHelper"
            "\n\n3. Command-line tools:"
            "\n   - twitch-dl: pip install twitch-dl && twitch-dl download <video_id>"
            "\n   - streamlink: streamlink <twitch_url> best -o output.mp4"
            "\n   - yt-dlp: yt-dlp <twitch_url>"
            "\n\n4. Desktop applications:"
            "\n   - TwitchLeecher (Windows)"
            "\n   - 4K Video Downloader"
            "\n\nNote: "
            "\n- VODs may expire after 14-60 days depending on subscription"
            "\n- Subscriber-only content requires authentication"
            "\n- Some clips may be deleted by creators"
            "\n\nTwitch support will be improved in future versions with proper authentication handling."
        )

    @property
    def platform(self) -> str:
        return "twitch"
    
    async def get_formats(self, url: str) -> Dict[str, Any]:
        """Get available formats for a Twitch video/clip without downloading
        
        Args:
            url: Twitch video or clip URL
            
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
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    raise ValueError("Failed to extract Twitch video information")
                
                # Extract metadata
                video_id = info.get('id')
                title = info.get('title')
                thumbnail = info.get('thumbnail')
                duration = info.get('duration', 0)
                
                # Process available formats
                formats = []
                seen_heights = set()
                seen_audio = False
                
                # Twitch provides multiple quality options
                for fmt in info.get('formats', []):
                    height = fmt.get('height')
                    vcodec = fmt.get('vcodec', 'unknown')
                    acodec = fmt.get('acodec', 'none')
                    ext = fmt.get('ext', 'mp4')
                    filesize = fmt.get('filesize')
                    format_note = fmt.get('format_note', '')
                    
                    # Include video formats with height info
                    if height and vcodec and vcodec != 'none':
                        # Skip duplicate heights
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
                    
                    # Include audio-only formats
                    elif not seen_audio and vcodec == 'none' and acodec and acodec != 'none':
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
                
                # Sort by height descending
                formats.sort(key=lambda x: (x['height'] if x['height'] else -1), reverse=True)
                
                logger.info(f"[{self.platform}] Found {len(formats)} formats")
                
                return {
                    'platform': 'twitch',
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
        """Download Twitch video/clip using yt-dlp library
        
        Args:
            url: Twitch video or clip URL
            quality: Desired video quality (e.g., "720p", "1080p", "audio")
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
            
            with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                logger.info(f"[{self.platform}] Extracting video information...")
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    raise ValueError("Failed to extract video information")
                
                # Get video metadata
                video_id = info.get('id')
                title = info.get('title')
                uploader = info.get('uploader')
                uploader_id = info.get('uploader_id') or info.get('channel_id')
                description = info.get('description', '')
                thumbnail = info.get('thumbnail')
                view_count = info.get('view_count', 0)
                duration = info.get('duration', 0)
                timestamp = info.get('timestamp')
            
            # Prepare download list
            downloads = []
            
            if is_audio_only:
                # Only download audio
                downloads.append({
                    'type': 'audio',
                    'opts': {
                        'format': 'bestaudio/best',
                        'quiet': True,
                        'no_warnings': True,
                        'outtmpl': os.path.join(settings.MEDIA_FOLDER, f'{video_id}_audio.%(ext)s'),
                    }
                })
            else:
                # Download both video and audio
                max_height = int(quality.replace('p', '')) if quality != 'audio' else 720
                
                # 1. Video with audio merged
                downloads.append({
                    'type': 'video',
                    'opts': {
                        'format': f'best[height<={max_height}]/best',
                        'quiet': True,
                        'no_warnings': True,
                        'outtmpl': os.path.join(settings.MEDIA_FOLDER, f'{video_id}_{max_height}p.%(ext)s'),
                    }
                })
                
                # 2. Audio-only
                downloads.append({
                    'type': 'audio',
                    'opts': {
                        'format': 'bestaudio/best',
                        'quiet': True,
                        'no_warnings': True,
                        'outtmpl': os.path.join(settings.MEDIA_FOLDER, f'{video_id}_audio.%(ext)s'),
                    }
                })
            
            # Download all formats
            downloaded_files = []
            for download_info in downloads:
                logger.info(f"[{self.platform}] Downloading {download_info['type']}...")
                with yt_dlp.YoutubeDL(download_info['opts']) as ydl:
                    ydl.download([url])
                downloaded_files.append(download_info['type'])
            
            # Build response with all downloaded files
            media_data = []
            
            # Check for video file
            if not is_audio_only:
                video_filename = f"{video_id}_{max_height}p.mp4"
                video_filepath = os.path.join(settings.MEDIA_FOLDER, video_filename)
                if os.path.exists(video_filepath):
                    file_size_mb = os.path.getsize(video_filepath) / (1024 * 1024)
                    logger.info(f"[{self.platform}] Video download complete: {file_size_mb:.2f} MB")
                    media_data.append({
                        'quality': f"{max_height}p",
                        'format_id': 'video+audio',
                        'ext': 'mp4',
                        'url': f"{settings.API_BASE_URL}/{settings.MEDIA_FOLDER}/{video_filename}",
                        'downloaded': True,
                        'height': max_height,
                        'type': 'video'
                    })
            
            # Check for audio file  
            for ext in ['m4a', 'mp3', 'webm']:
                audio_filename = f"{video_id}_audio.{ext}"
                audio_filepath = os.path.join(settings.MEDIA_FOLDER, audio_filename)
                if os.path.exists(audio_filepath):
                    file_size_mb = os.path.getsize(audio_filepath) / (1024 * 1024)
                    logger.info(f"[{self.platform}] Audio download complete: {file_size_mb:.2f} MB")
                    media_data.append({
                        'quality': 'audio',
                        'format_id': 'audio',
                        'ext': ext,
                        'url': f"{settings.API_BASE_URL}/{settings.MEDIA_FOLDER}/{audio_filename}",
                        'downloaded': True,
                        'height': None,
                        'type': 'audio'
                    })
                    break
            
            # Return structured data
            data = {
                "platform": "twitch",
                "id": video_id,
                "title": title,
                "caption": description,
                "created_at": timestamp,
                "duration": duration,
                "author": {
                    "username": uploader,
                    "channel_id": uploader_id,
                    "profile_url": f"https://www.twitch.tv/{uploader_id}" if uploader_id else None,
                },
                "statistics": {
                    "views": view_count,
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
