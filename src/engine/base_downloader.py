from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BaseDownloader(ABC):
    """
    Abstract base class for a platform-specific downloader.
    It can be initialized with a session_manager for browser-based tasks,
    or without one for direct API calls.
    """

    def __init__(self, session_manager: Any = None):
        self.session_manager = session_manager

    @abstractmethod
    async def download(self, url: str, quality: str = "720p") -> Dict[str, Any]:
        """
        The main method to download content from a given URL.
        
        Args:
            url: The URL to download
            quality: Desired video quality (default: 720p)
        """
        raise NotImplementedError

    @abstractmethod
    async def get_formats(self, url: str) -> Dict[str, Any]:
        """
        Get available formats for a video without downloading.
        
        Args:
            url: The URL to get formats for
            
        Returns:
            Dict containing video metadata and available formats
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def platform(self) -> str:
        """
        Returns the name of the platform (e.g., 'tiktok', 'instagram').
        """
        raise NotImplementedError
