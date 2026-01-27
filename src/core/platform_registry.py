from typing import Optional, Dict, Type, Any
from src.engine.base_downloader import BaseDownloader
from src.engine.platforms.tiktok import TikTokDownloader
from src.engine.platforms.youtube import YouTubeDownloader
from src.engine.platforms.instagram import InstagramDownloader
from src.engine.platforms.twitter import TwitterDownloader
from src.engine.platforms.reddit import RedditDownloader
from src.engine.platforms.soundcloud import SoundCloudDownloader
from src.engine.platforms.dailymotion import DailymotionDownloader
from src.engine.platforms.twitch import TwitchDownloader
from src.engine.platforms.vimeo import VimeoDownloader
from src.engine.platforms.facebook import FacebookDownloader
from src.engine.platforms.bilibili import BilibiliDownloader
from src.engine.platforms.linkedin import LinkedInDownloader
from src.engine.platforms.pinterest import PinterestDownloader

class PlatformRegistry:
    """
    Central registry for platform detection and downloader management.
    """

    @staticmethod
    def get_downloader(url: str) -> BaseDownloader:
        """Return appropriate downloader based on URL"""
        url_lower = url.lower()

        if "tiktok.com" in url_lower or "vt.tiktok.com" in url_lower:
            return TikTokDownloader()
        elif "youtube.com" in url_lower or "youtu.be" in url_lower:
            return YouTubeDownloader()
        elif "instagram.com" in url_lower:
            return InstagramDownloader()
        elif "twitter.com" in url_lower or "x.com" in url_lower or "t.co" in url_lower:
            return TwitterDownloader()
        elif "reddit.com" in url_lower or "redd.it" in url_lower:
            return RedditDownloader()
        elif "soundcloud.com" in url_lower:
            return SoundCloudDownloader()
        elif "dailymotion.com" in url_lower or "dai.ly" in url_lower:
            return DailymotionDownloader()
        elif "twitch.tv" in url_lower:
            return TwitchDownloader()
        elif "vimeo.com" in url_lower:
            return VimeoDownloader()
        elif "facebook.com" in url_lower or "fb.watch" in url_lower:
            return FacebookDownloader()
        elif "bilibili.com" in url_lower or "b23.tv" in url_lower:
            return BilibiliDownloader()
        elif "linkedin.com" in url_lower:
            return LinkedInDownloader()
        elif "pinterest.com" in url_lower or "pin.it" in url_lower:
            return PinterestDownloader()
        else:
            raise ValueError(f"No downloader found for URL: {url}. Supported platforms: TikTok, YouTube, Instagram, Twitter/X, Reddit, SoundCloud, Dailymotion, Twitch, Vimeo, Facebook, Bilibili, LinkedIn, Pinterest")

    @staticmethod
    def detect_platform(url: str) -> str:
        """Detect platform from URL"""
        url_lower = url.lower()

        if "tiktok.com" in url_lower or "vt.tiktok.com" in url_lower:
            return "tiktok"
        elif "youtube.com" in url_lower or "youtu.be" in url_lower:
            return "youtube"
        elif "instagram.com" in url_lower:
            return "instagram"
        elif "twitter.com" in url_lower or "x.com" in url_lower:
            return "twitter"
        elif "reddit.com" in url_lower or "redd.it" in url_lower:
            return "reddit"
        elif "soundcloud.com" in url_lower:
            return "soundcloud"
        elif "dailymotion.com" in url_lower or "dai.ly" in url_lower:
            return "dailymotion"
        elif "twitch.tv" in url_lower:
            return "twitch"
        elif "vimeo.com" in url_lower:
            return "vimeo"
        elif "facebook.com" in url_lower or "fb.watch" in url_lower:
            return "facebook"
        elif "bilibili.com" in url_lower or "b23.tv" in url_lower:
            return "bilibili"
        elif "linkedin.com" in url_lower:
            return "linkedin"
        elif "pinterest.com" in url_lower or "pin.it" in url_lower:
            return "pinterest"
        else:
            return "unknown"

    @staticmethod
    def get_downloader_by_platform(platform: str) -> BaseDownloader:
        """Get downloader instance by platform name"""
        platform_map = {
            'tiktok': TikTokDownloader,
            'youtube': YouTubeDownloader,
            'instagram': InstagramDownloader,
            'twitter': TwitterDownloader,
            'reddit': RedditDownloader,
            'soundcloud': SoundCloudDownloader,
            'dailymotion': DailymotionDownloader,
            'twitch': TwitchDownloader,
            'vimeo': VimeoDownloader,
            'facebook': FacebookDownloader,
            'bilibili': BilibiliDownloader,
            'linkedin': LinkedInDownloader,
            'pinterest': PinterestDownloader
        }

        downloader_class = platform_map.get(platform.lower())
        if downloader_class:
            return downloader_class()
        raise ValueError(f"Unknown platform: {platform}")
