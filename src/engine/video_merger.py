"""
Video/Audio Merger using FFmpeg
Handles merging separate video and audio streams
"""

import asyncio
import os
from typing import Optional
from loguru import logger
from src.core.config import settings

class VideoMerger:
    
    @staticmethod
    async def merge_video_audio(video_path: str, audio_path: str, output_path: str) -> bool:
        """
        Merge video and audio files using FFmpeg
        
        Args:
            video_path: Path to video file
            audio_path: Path to audio file
            output_path: Path for output file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"[Merger] Merging video and audio...")
            logger.info(f"[Merger] Video: {video_path}")
            logger.info(f"[Merger] Audio: {audio_path}")
            logger.info(f"[Merger] Output: {output_path}")
            
            # FFmpeg command to merge video and audio
            cmd = [
                'ffmpeg',
                '-i', video_path,          # Input video
                '-i', audio_path,          # Input audio
                '-c:v', 'copy',            # Copy video codec (no re-encoding)
                '-c:a', 'aac',             # Convert audio to AAC
                '-strict', 'experimental',
                '-y',                      # Overwrite output file
                output_path
            ]
            
            # Run FFmpeg
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"[Merger] Successfully merged video and audio")
                
                # Clean up temporary files
                try:
                    os.remove(video_path)
                    os.remove(audio_path)
                    logger.info(f"[Merger] Cleaned up temporary files")
                except Exception as e:
                    logger.warning(f"[Merger] Failed to clean up temp files: {e}")
                
                return True
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"[Merger] FFmpeg failed: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"[Merger] Merge failed: {e}")
            return False
    
    @staticmethod
    async def check_ffmpeg() -> bool:
        """Check if FFmpeg is installed"""
        try:
            process = await asyncio.create_subprocess_exec(
                'ffmpeg', '-version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            return process.returncode == 0
        except FileNotFoundError:
            logger.error("[Merger] FFmpeg not found. Please install FFmpeg.")
            return False
