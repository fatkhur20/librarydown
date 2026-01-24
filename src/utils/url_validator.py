"""URL validation and parsing utilities."""

import re
from urllib.parse import urlparse
from typing import Optional, Tuple
from .exceptions import ValidationError


class URLValidator:
    """Utility class for URL validation and platform detection."""
    
    # Supported platforms and their URL patterns
    SUPPORTED_PLATFORMS = {
        'tiktok': [
            r'tiktok\.com',
            r'vt\.tiktok\.com'
        ],
        'youtube': [
            r'youtube\.com',
            r'youtu\.be'
        ],
        'instagram': [
            r'instagram\.com'
        ],
        'twitter': [
            r'twitter\.com',
            r'x\.com',
            r't\.co'
        ],
        'reddit': [
            r'reddit\.com',
            r'redd\.it'
        ],
        'soundcloud': [
            r'soundcloud\.com'
        ],
        'dailymotion': [
            r'dailymotion\.com',
            r'dai\.ly'
        ],
        'twitch': [
            r'twitch\.tv'
        ],
        'vimeo': [
            r'vimeo\.com'
        ],
        'facebook': [
            r'facebook\.com',
            r'fb\.watch'
        ],
        'bilibili': [
            r'bilibili\.com',
            r'b23\.tv'
        ],
        'linkedin': [
            r'linkedin\.com'
        ],
        'pinterest': [
            r'pinterest\.com',
            r'pin\.it'
        ]
    }
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """Validate if URL is properly formatted.
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValidationError: If URL is invalid
        """
        if not url or not isinstance(url, str):
            raise ValidationError("url", str(url), "URL must be a non-empty string")
            
        try:
            parsed = urlparse(url.strip())
            
            # Check basic URL structure
            if not parsed.scheme:
                raise ValidationError("url", url, "Missing URL scheme (http:// or https://)")
                
            if not parsed.netloc:
                raise ValidationError("url", url, "Missing domain name")
                
            # Check for valid schemes
            if parsed.scheme not in ['http', 'https']:
                raise ValidationError("url", url, f"Invalid scheme: {parsed.scheme}")
                
            return True
            
        except Exception as e:
            raise ValidationError("url", url, f"Invalid URL format: {str(e)}")
    
    @classmethod
    def detect_platform(cls, url: str) -> str:
        """Detect platform from URL.
        
        Args:
            url: URL to analyze
            
        Returns:
            Platform name or 'unknown' if not recognized
        """
        try:
            cls.validate_url(url)
            url_lower = url.lower()
            
            for platform, patterns in cls.SUPPORTED_PLATFORMS.items():
                for pattern in patterns:
                    if re.search(pattern, url_lower):
                        return platform
                        
            return "unknown"
            
        except ValidationError:
            return "unknown"
    
    @classmethod
    def is_supported_platform(cls, url: str) -> bool:
        """Check if URL belongs to a supported platform.
        
        Args:
            url: URL to check
            
        Returns:
            True if supported, False otherwise
        """
        return cls.detect_platform(url) != "unknown"
    
    @classmethod
    def normalize_url(cls, url: str) -> str:
        """Normalize URL by ensuring it has proper scheme.
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL with https:// scheme if missing
        """
        url = url.strip()
        
        # Add scheme if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        return url
    
    @classmethod
    def get_domain(cls, url: str) -> str:
        """Extract domain from URL.
        
        Args:
            url: URL to parse
            
        Returns:
            Domain name
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return ""
    
    @classmethod
    def get_platform_info(cls, url: str) -> Tuple[str, str, bool]:
        """Get comprehensive platform information.
        
        Args:
            url: URL to analyze
            
        Returns:
            Tuple of (platform_name, domain, is_supported)
        """
        platform = cls.detect_platform(url)
        domain = cls.get_domain(url)
        is_supported = platform != "unknown"
        
        return platform, domain, is_supported