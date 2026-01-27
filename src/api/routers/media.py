from fastapi import APIRouter, HTTPException, Request
from src.api.schemas import FormatsResponse
from pydantic import HttpUrl
from datetime import datetime
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional
import os
from src.utils.logging.logger import log_api_call, log_error
from src.core.config import settings
from src.utils.security import security_validator
from src.utils.user_features import QualityOption, FormatOption, quality_selector, format_converter, playlist_handler, user_preferences
from src.core.platform_registry import PlatformRegistry

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.get("/qualities", summary="Get available quality options")
async def get_quality_options(platform: Optional[str] = None):
    """
    Get available quality options for a platform.
    If no platform is specified, returns all available options.
    """
    start_time = datetime.utcnow()

    try:
        if platform:
            qualities = quality_selector.get_quality_options(platform)
            result = {
                "platform": platform,
                "qualities": [q.value for q in qualities],
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            result = {
                "all_qualities": [q.value for q in QualityOption],
                "timestamp": datetime.utcnow().isoformat()
            }

        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        log_api_call("/api/v1/qualities", "GET", "system", 200, duration)
        return result
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.error(f"Qualities endpoint error: {e}")
        log_error(f"Qualities endpoint error: {e}", exception=e, context={"duration_ms": duration})
        raise HTTPException(status_code=500, detail="Unable to fetch quality options")

@router.post("/convert", summary="Convert media format")
async def convert_media(
    input_file: str,
    target_format: FormatOption
):
    """
    Convert media file to target format.
    Input file should be a path to an existing file in the media folder.
    """
    start_time = datetime.utcnow()

    try:
        # Validate input file path to prevent directory traversal
        is_valid, error = security_validator.validate_media_path(settings.MEDIA_FOLDER, input_file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error)

        input_path = os.path.join(settings.MEDIA_FOLDER, input_file)
        if not os.path.exists(input_path):
            raise HTTPException(status_code=404, detail="Input file not found")

        # Generate output filename
        file_base, file_ext = os.path.splitext(input_path)
        output_path = f"{file_base}.{target_format.value}"

        # Perform conversion
        success = format_converter.convert_file(input_path, output_path, target_format)

        if success:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            log_api_call("/api/v1/convert", "POST", "system", 200, duration)
            return {
                "status": "converted",
                "input_file": input_file,
                "output_file": os.path.basename(output_path),
                "target_format": target_format.value,
                "timestamp": datetime.utcnow().isoformat(),
                "response_time_ms": duration
            }
        else:
            raise HTTPException(status_code=500, detail="Conversion failed")
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.error(f"Media conversion error: {e}")
        log_error(f"Media conversion error: {e}", exception=e, context={"duration_ms": duration})
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

@router.get("/playlist-info", summary="Get playlist information")
async def get_playlist_info(url: HttpUrl):
    """
    Get information about a playlist.
    """
    start_time = datetime.utcnow()

    try:
        url_str = str(url)
        playlist_info = playlist_handler.get_playlist_info(url_str)

        if playlist_info:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            log_api_call("/api/v1/playlist-info", "GET", "system", 200, duration)
            return {
                "playlist": playlist_info.dict(),
                "timestamp": datetime.utcnow().isoformat(),
                "response_time_ms": duration
            }
        else:
            raise HTTPException(status_code=400, detail="URL is not a playlist or could not be processed")
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.error(f"Playlist info error: {e}")
        log_error(f"Playlist info error: {e}", exception=e, context={"duration_ms": duration})
        raise HTTPException(status_code=500, detail=f"Could not get playlist info: {str(e)}")

@router.get("/preferences", summary="Get user preferences")
async def get_user_preferences():
    """
    Get current user preferences.
    """
    start_time = datetime.utcnow()

    try:
        prefs = user_preferences.get_user_quality_options()
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        log_api_call("/api/v1/preferences", "GET", "system", 200, duration)
        return {
            "preferences": prefs,
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": duration
        }
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.error(f"User preferences error: {e}")
        log_error(f"User preferences error: {e}", exception=e, context={"duration_ms": duration})
        raise HTTPException(status_code=500, detail="Unable to fetch user preferences")

@router.get("/formats", response_model=FormatsResponse, summary="Get available video formats")
@limiter.limit("20/minute")
async def get_video_formats(
    request: Request,
    url: HttpUrl
):
    """
    Get all available formats/resolutions for a video without downloading.
    """
    try:
        url_str = str(url)
        platform = PlatformRegistry.detect_platform(url_str)

        if platform == "unknown":
            raise HTTPException(
                status_code=400,
                detail="Unsupported platform. Supported: TikTok, YouTube, Instagram, Reddit"
            )

        logger.info(f"[API] Fetching formats for {platform}: {url_str}")

        try:
            downloader = PlatformRegistry.get_downloader(url_str)
        except ValueError:
             raise HTTPException(
                status_code=400,
                detail=f"Format fetching not yet implemented for {platform}"
            )

        # Get formats without downloading
        formats_data = await downloader.get_formats(url_str)

        logger.info(f"[API] Found {len(formats_data.get('formats', []))} formats")

        return formats_data

    except ValueError as e:
        logger.error(f"[API] ValueError while fetching formats: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[API] Error fetching formats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch formats: {str(e)}")
