from typing import List, Dict, Optional, Any
from enum import Enum
from pydantic import BaseModel
import yt_dlp
from loguru import logger
from src.utils.security import security_validator
from src.core.config import settings
import os
import tempfile
import subprocess
from pathlib import Path


class QualityOption(str, Enum):
    """Available quality options for downloads"""
    AUDIO_ONLY = "audio"
    Q144P = "144p"
    Q240P = "240p"
    Q360P = "360p"
    Q480P = "480p"
    Q720P = "720p"
    Q1080P = "1080p"
    Q1440P = "1440p"
    Q2160P = "2160p"  # 4K
    BEST = "best"
    WORST = "worst"


class FormatOption(str, Enum):
    """Available format options for conversion"""
    MP4 = "mp4"
    MP3 = "mp3"
    M4A = "m4a"
    WEBM = "webm"
    FLV = "flv"
    AVI = "avi"
    MOV = "mov"
    WMV = "wmv"
    MKV = "mkv"


class PlaylistInfo(BaseModel):
    """Information about a playlist"""
    id: str
    title: str
    uploader: str
    entry_count: int
    entries: List[Dict[str, Any]]


class QualitySelector:
    """Handles quality selection for different platforms"""
    
    @staticmethod
    def get_quality_format(quality: QualityOption) -> str:
        """Convert quality option to yt-dlp format string"""
        quality_map = {
            QualityOption.AUDIO_ONLY: "bestaudio/best",
            QualityOption.Q144P: "144p/best",
            QualityOption.Q240P: "240p/best",
            QualityOption.Q360P: "360p/best",
            QualityOption.Q480P: "480p/best",
            QualityOption.Q720P: "720p/best",
            QualityOption.Q1080P: "1080p/best",
            QualityOption.Q1440P: "1440p/best",
            QualityOption.Q2160P: "2160p/best",
            QualityOption.BEST: "best",
            QualityOption.WORST: "worst"
        }
        return quality_map.get(quality, "best")
    
    @staticmethod
    def get_quality_options(platform: str) -> List[QualityOption]:
        """Get available quality options for a platform"""
        if platform.lower() in ['youtube', 'tiktok', 'instagram', 'twitch', 'dailymotion']:
            return [
                QualityOption.Q144P,
                QualityOption.Q240P,
                QualityOption.Q360P,
                QualityOption.Q480P,
                QualityOption.Q720P,
                QualityOption.Q1080P,
                QualityOption.AUDIO_ONLY
            ]
        elif platform.lower() == 'soundcloud':
            return [QualityOption.AUDIO_ONLY]
        else:
            return [
                QualityOption.Q144P,
                QualityOption.Q240P,
                QualityOption.Q360P,
                QualityOption.Q480P,
                QualityOption.Q720P,
                QualityOption.AUDIO_ONLY
            ]


class FormatConverter:
    """Handles format conversion for downloaded media"""
    
    @staticmethod
    def convert_file(input_path: str, output_path: str, target_format: FormatOption) -> bool:
        """Convert media file to target format using ffmpeg"""
        try:
            # Determine codec based on target format
            codec_map = {
                FormatOption.MP3: ['-c:a', 'libmp3lame', '-vn'],  # Audio only
                FormatOption.M4A: ['-c:a', 'aac', '-vn'],  # Audio only
                FormatOption.MP4: ['-c:v', 'libx264', '-c:a', 'aac'],
                FormatOption.WEBM: ['-c:v', 'libvpx', '-c:a', 'libvorbis'],
                FormatOption.FLV: ['-c:v', 'flv', '-c:a', 'mp3'],
                FormatOption.AVI: ['-c:v', 'mpeg4', '-c:a', 'mp3'],
                FormatOption.MOV: ['-c:v', 'libx264', '-c:a', 'aac'],
                FormatOption.WMV: ['-c:v', 'wmv2', '-c:a', 'wmav2'],
                FormatOption.MKV: ['-c:v', 'copy', '-c:a', 'copy']  # Copy streams
            }
            
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-y'  # Overwrite output file
            ]
            
            # Add format-specific codecs
            if target_format in codec_map:
                cmd.extend(codec_map[target_format])
            else:
                # Default to copying streams
                cmd.extend(['-c', 'copy'])
            
            cmd.append(output_path)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Successfully converted {input_path} to {output_path}")
                return True
            else:
                logger.error(f"FFmpeg conversion failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Format conversion error: {e}")
            return False


class PlaylistHandler:
    """Handles playlist downloads and management"""
    
    @staticmethod
    def get_playlist_info(url: str) -> Optional[PlaylistInfo]:
        """Get information about a playlist"""
        try:
            with yt_dlp.YoutubeDL({'extract_flat': True, 'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if 'entries' in info:
                    entries = []
                    for entry in info['entries']:
                        entries.append({
                            'id': entry.get('id', ''),
                            'title': entry.get('title', ''),
                            'duration': entry.get('duration', 0),
                            'uploader': entry.get('uploader', ''),
                            'url': entry.get('url', ''),
                            'thumbnail': entry.get('thumbnail', '')
                        })
                    
                    playlist_info = PlaylistInfo(
                        id=info.get('id', ''),
                        title=info.get('title', ''),
                        uploader=info.get('uploader', ''),
                        entry_count=len(entries),
                        entries=entries
                    )
                    
                    return playlist_info
                else:
                    logger.warning("URL is not a playlist")
                    return None
        except Exception as e:
            logger.error(f"Error getting playlist info: {e}")
            return None
    
    @staticmethod
    def download_playlist(url: str, quality: QualityOption = QualityOption.Q720P, 
                         max_videos: Optional[int] = None) -> List[str]:
        """Download all videos in a playlist"""
        try:
            quality_format = QualitySelector.get_quality_format(quality)
            
            ydl_opts = {
                'outtmpl': os.path.join(settings.MEDIA_FOLDER, '%(title)s.%(ext)s'),
                'format': quality_format,
                'playliststart': 1,
                'playlistend': max_videos,
                'quiet': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                downloaded_files = []
                if 'entries' in info:
                    for entry in info['entries']:
                        if entry and entry.get('_filename'):
                            downloaded_files.append(entry['_filename'])
                else:
                    # If it's not a playlist, just add the single file
                    if info and info.get('_filename'):
                        downloaded_files.append(info['_filename'])
                
                return downloaded_files
        except Exception as e:
            logger.error(f"Error downloading playlist: {e}")
            return []


class UserPreferences:
    """Handles user preferences and settings"""
    
    def __init__(self):
        self.default_quality = QualityOption.Q720P
        self.default_format = FormatOption.MP4
        self.download_history = []
        self.user_settings = {}
    
    def set_default_quality(self, quality: QualityOption):
        """Set default quality for user"""
        self.default_quality = quality
    
    def set_default_format(self, format_option: FormatOption):
        """Set default format for user"""
        self.default_format = format_option
    
    def get_user_quality_options(self) -> Dict[str, Any]:
        """Get user's quality and format preferences"""
        return {
            "default_quality": self.default_quality.value,
            "default_format": self.default_format.value,
            "available_qualities": [q.value for q in QualityOption],
            "available_formats": [f.value for f in FormatOption]
        }
    
    def add_to_history(self, url: str, quality: QualityOption, result: Dict[str, Any]):
        """Add download to user history"""
        history_item = {
            "url": url,
            "quality": quality.value,
            "result": result,
            "timestamp": "TODO"  # Will be set by caller
        }
        self.download_history.append(history_item)
        
        # Keep only last 100 items
        if len(self.download_history) > 100:
            self.download_history = self.download_history[-100:]


# Global instances
quality_selector = QualitySelector()
format_converter = FormatConverter()
playlist_handler = PlaylistHandler()
user_preferences = UserPreferences()