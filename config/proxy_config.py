"""
Proxy Configuration for LibraryDown
"""

class ProxyConfig:
    """Configuration class for proxy settings"""
    
    # Proxy settings
    USE_PROXY = True
    PROXY_TYPE = "socks5"  # socks5, http, https
    PROXY_HOST = "127.0.0.1"
    PROXY_PORT = 9050
    PROXY_URL = f"{PROXY_TYPE}://{PROXY_HOST}:{PROXY_PORT}"
    
    # Proxy timeout settings
    PROXY_TIMEOUT = 30
    PROXY_RETRY_COUNT = 3
    
    # Platform-specific proxy settings
    PLATFORM_USE_PROXY = {
        'youtube': True,
        'instagram': False,  # Instagram usually works without proxy
        'tiktok': False,
        'twitter': False
    }
    
    @classmethod
    def get_proxy_for_platform(cls, platform: str) -> dict:
        """Get proxy configuration for specific platform"""
        if cls.PLATFORM_USE_PROXY.get(platform, False):
            return {
                'proxy': cls.PROXY_URL,
                'socket_timeout': cls.PROXY_TIMEOUT
            }
        return {}

    @classmethod
    def get_yt_dlp_proxy_options(cls, platform: str) -> dict:
        """Get proxy options formatted for yt-dlp"""
        if cls.PLATFORM_USE_PROXY.get(platform, False):
            return {
                'proxy': cls.PROXY_URL,
                'socket_timeout': cls.PROXY_TIMEOUT
            }
        return {}