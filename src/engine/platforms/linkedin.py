from typing import Any, Dict, Optional
from src.engine.base_downloader import BaseDownloader
from loguru import logger


class LinkedInDownloader(BaseDownloader):
    @property
    def platform(self) -> str:
        return "linkedin"
    
    async def get_formats(self, url: str) -> Dict[str, Any]:
        """LinkedIn downloader is not supported by yt-dlp
        
        Args:
            url: LinkedIn post URL
            
        Raises:
            NotImplementedError: LinkedIn is not supported by yt-dlp library
        """
        raise NotImplementedError(
            "LinkedIn video downloader is not currently supported. "
            "\n\nAlternative solutions:"
            "\n1. Browser extensions:"
            "\n   - LinkedIn Video Downloader Extension"
            "\n   - Video Downloader Professional"
            "\n\n2. Web services:"
            "\n   - LinkedIn Video Downloader: https://linkedin-video-downloader.com/"
            "\n   - Save LinkedIn Videos: https://savelinkedinvideos.com/"
            "\n\n3. Manual download method:"
            "\n   - Open browser DevTools (F12)"
            "\n   - Go to Network tab"
            "\n   - Play the video"
            "\n   - Filter by 'media' or 'mp4'"
            "\n   - Find and download the video file"
            "\n\nNote: LinkedIn has strict anti-scraping measures. "
            "Professional API access or browser automation required for reliable downloads."
        )
    
    async def download(self, url: str, quality: str = "720p") -> Dict[str, Any]:
        """LinkedIn downloader is not supported by yt-dlp
        
        Args:
            url: LinkedIn post URL
            quality: Desired video quality
            
        Raises:
            NotImplementedError: LinkedIn is not supported by yt-dlp library
        """
        raise NotImplementedError(
            "LinkedIn video downloader is not currently supported. "
            "\n\nAlternative solutions:"
            "\n1. Browser extensions:"
            "\n   - LinkedIn Video Downloader Extension"
            "\n   - Video Downloader Professional"
            "\n\n2. Web services:"
            "\n   - LinkedIn Video Downloader: https://linkedin-video-downloader.com/"
            "\n   - Save LinkedIn Videos: https://savelinkedinvideos.com/"
            "\n\n3. Manual download method:"
            "\n   - Open browser DevTools (F12)"
            "\n   - Go to Network tab"
            "\n   - Play the video"
            "\n   - Filter by 'media' or 'mp4'"
            "\n   - Find and download the video file"
            "\n\nNote: LinkedIn has strict anti-scraping measures. "
            "Professional API access or browser automation required for reliable downloads."
        )
