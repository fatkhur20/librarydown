"""Common cookie management utilities for all platform downloaders."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Dict
from loguru import logger


class CookieManager:
    """Centralized cookie file management utility."""
    
    def __init__(self, base_path: str = None):
        """Initialize cookie manager.
        
        Args:
            base_path: Base path for cookie files. Defaults to project root.
        """
        if base_path is None:
            # Navigate up from src/utils to project root
            base_path = Path(__file__).parent.parent.parent
            
        self.base_path = Path(base_path)
        self.cookies_dir = self.base_path / "cookies"
        
    def get_platform_cookies(self, platform: str) -> Optional[str]:
        """Get path to platform-specific cookie file.
        
        Args:
            platform: Platform name (youtube, instagram, tiktok, etc.)
            
        Returns:
            Path to cookie file if exists, None otherwise
        """
        platform_cookies = {
            "youtube": "youtube_cookies.txt",
            "instagram": "instagram_cookies.txt",
            "tiktok": "tiktok_cookies.txt",
            "twitter": "twitter_cookies.txt",
            "soundcloud": "soundcloud_cookies.txt",
            "dailymotion": "dailymotion_cookies.txt",
            "twitch": "twitch_cookies.txt",
            "vimeo": "vimeo_cookies.txt",
            "facebook": "facebook_cookies.txt",
            "bilibili": "bilibili_cookies.txt",
            "linkedin": "linkedin_cookies.txt",
            "pinterest": "pinterest_cookies.txt"
        }
        
        filename = platform_cookies.get(platform.lower())
        if not filename:
            return None
            
        cookie_path = self.cookies_dir / filename
        return str(cookie_path) if cookie_path.exists() else None
    
    def copy_cookies_to_temp(self, platform: str) -> Optional[str]:
        """Copy platform cookies to temporary file for safe usage.
        
        Args:
            platform: Platform name
            
        Returns:
            Path to temporary cookie file, or None if no cookies found
        """
        source_path = self.get_platform_cookies(platform)
        if not source_path:
            return None
            
        try:
            # Create temporary file with platform-specific name
            temp_fd, temp_path = tempfile.mkstemp(
                prefix=f"{platform}_cookies_",
                suffix=".txt",
                text=True
            )
            
            # Copy cookie content
            shutil.copy2(source_path, temp_path)
            
            # Set appropriate permissions
            os.chmod(temp_path, 0o644)
            
            logger.debug(f"Copied {platform} cookies to temporary file: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"Failed to copy {platform} cookies: {e}")
            return None
    
    def get_ytdlp_options(self, platform: str) -> Dict[str, str]:
        """Get yt-dlp compatible options with cookie file.
        
        Args:
            platform: Platform name
            
        Returns:
            Dictionary with cookiefile option if cookies exist
        """
        temp_cookie_path = self.copy_cookies_to_temp(platform)
        if temp_cookie_path:
            return {"cookiefile": temp_cookie_path}
        return {}
    
    def cleanup_temp_cookies(self, temp_path: str) -> bool:
        """Clean up temporary cookie file.
        
        Args:
            temp_path: Path to temporary cookie file
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                logger.debug(f"Cleaned up temporary cookie file: {temp_path}")
                return True
        except Exception as e:
            logger.warning(f"Failed to cleanup temporary cookie file {temp_path}: {e}")
        return False
    
    def validate_cookie_format(self, content: str) -> bool:
        """Validate Netscape cookie file format.
        
        Args:
            content: Cookie file content
            
        Returns:
            True if valid format, False otherwise
        """
        if not content.strip():
            return False
            
        lines = content.strip().split('\n')
        
        # Skip comment lines and empty lines
        data_lines = [line for line in lines if line.strip() and not line.startswith('#')]
        
        # Need at least one data line
        if not data_lines:
            return False
            
        # Check first data line format (should have 7 tab-separated fields)
        first_line = data_lines[0]
        fields = first_line.split('\t')
        
        return len(fields) == 7


# Global instance for easy access
cookie_manager = CookieManager()