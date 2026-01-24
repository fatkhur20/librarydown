"""
Proxy Configuration for LibraryDown
"""

class ProxyConfig:
    """Configuration class for proxy settings"""
    
    # Proxy settings - Default to Tor
    USE_PROXY = True
    PROXY_TYPE = "socks5"  # socks5, http, https
    PROXY_HOST = "127.0.0.1"
    PROXY_PORT = 9050  # Default Tor port, change to 2080 for 3proxy
    PROXY_URL = f"{PROXY_TYPE}://{PROXY_HOST}:{PROXY_PORT}"
    
    # Alternative proxy settings for 3proxy
    PROXY_PORTS = {
        'tor': 9050,      # Tor SOCKS5 port
        '3proxy': 2080,   # 3proxy SOCKS5 port
        'custom': None    # Set to specific port if using custom proxy
    }
    
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
    def set_proxy_type(cls, proxy_type: str = 'tor'):
        """Set proxy type and update configuration accordingly"""
        if proxy_type in cls.PROXY_PORTS:
            port = cls.PROXY_PORTS[proxy_type]
            if port is not None:
                cls.PROXY_PORT = port
                cls.PROXY_URL = f"{cls.PROXY_TYPE}://{cls.PROXY_HOST}:{cls.PROXY_PORT}"
                return True
        return False
    
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
                'socket_timeout': cls.PROXY_TIMEOUT,
                'geo_bypass': True,  # Additional geo-bypass for yt-dlp
            }
        return {}