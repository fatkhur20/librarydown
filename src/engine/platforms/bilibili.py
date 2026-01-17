from typing import Any, Dict, Optional
from src.engine.base_downloader import BaseDownloader
from loguru import logger


class BilibiliDownloader(BaseDownloader):
    @property
    def platform(self) -> str:
        return "bilibili"
    
    async def get_formats(self, url: str) -> Dict[str, Any]:
        """Bilibili downloader is currently not available due to region restrictions
        
        Args:
            url: Bilibili video URL
            
        Raises:
            NotImplementedError: Bilibili support is blocked by region/environment restrictions
        """
        raise NotImplementedError(
            "Bilibili downloader is currently not available due to region restrictions (HTTP 412 Precondition Failed). "
            "\n\nAlternative solutions:"
            "\n1. Use specialized Bilibili downloaders:"
            "\n   - BBDown: https://github.com/nilaoda/BBDown"
            "\n   - Bilibili-Evolved: https://github.com/the1812/Bilibili-Evolved"
            "\n   - BiliDuang: https://github.com/kuresaru/BiliDuang"
            "\n\n2. Browser extensions:"
            "\n   - Bilibili Downloader Helper"
            "\n   - 哔哩哔哩助手 (Bilibili Helper)"
            "\n\n3. Command-line tools:"
            "\n   - you-get: you-get <bilibili_url>"
            "\n   - yt-dlp with proxy: yt-dlp --proxy <proxy> <bilibili_url>"
            "\n\n4. Web services:"
            "\n   - SaveFrom.net (limited support)"
            "\n\nNote: Bilibili requires region-specific access and may need VPN or proxy. "
            "Full support will be added when deployed in appropriate environment."
        )
    
    async def download(self, url: str, quality: str = "720p") -> Dict[str, Any]:
        """Bilibili downloader is currently not available due to region restrictions
        
        Args:
            url: Bilibili video URL
            quality: Desired video quality
            
        Raises:
            NotImplementedError: Bilibili support is blocked by region/environment restrictions
        """
        raise NotImplementedError(
            "Bilibili downloader is currently not available due to region restrictions (HTTP 412 Precondition Failed). "
            "\n\nAlternative solutions:"
            "\n1. Use specialized Bilibili downloaders:"
            "\n   - BBDown: https://github.com/nilaoda/BBDown"
            "\n   - Bilibili-Evolved: https://github.com/the1812/Bilibili-Evolved"
            "\n   - BiliDuang: https://github.com/kuresaru/BiliDuang"
            "\n\n2. Browser extensions:"
            "\n   - Bilibili Downloader Helper"
            "\n   - 哔哩哔哩助手 (Bilibili Helper)"
            "\n\n3. Command-line tools:"
            "\n   - you-get: you-get <bilibili_url>"
            "\n   - yt-dlp with proxy: yt-dlp --proxy <proxy> <bilibili_url>"
            "\n\n4. Web services:"
            "\n   - SaveFrom.net (limited support)"
            "\n\nNote: Bilibili requires region-specific access and may need VPN or proxy. "
            "Full support will be added when deployed in appropriate environment."
        )
