from fastapi import APIRouter, HTTPException, Depends, Request
from src.database.base import get_db
from src.database.models import DownloadHistory, TaskStatus
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from loguru import logger
from src.utils.logging.logger import log_api_call, log_error
from src.utils.logging.monitor import monitor
from src.config.monitoring_config import monitoring_settings
from src.utils.version_checker import version_checker

router = APIRouter()

@router.get("/health", summary="Health check endpoint")
async def health_check():
    """
    Simple health check endpoint for monitoring.
    Returns 200 OK if service is running properly.
    """
    try:
        from src.core.config import settings

        response = {
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.VERSION,
            "timestamp": datetime.utcnow().isoformat()
        }

        if monitoring_settings.MONITORING_ENABLED:
            try:
                system_stats = monitor.get_system_stats()
                response["system_stats"] = {
                    "cpu_percent": system_stats.get("cpu_percent"),
                    "memory_percent": system_stats.get("memory_percent"),
                    "disk_usage": system_stats.get("disk_usage"),
                    "uptime_seconds": system_stats.get("uptime_seconds")
                }
            except Exception as e:
                logger.warning(f"Failed to get system stats for health check: {e}")
                response["system_stats"] = "unavailable"

        return response
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

@router.get("/metrics", summary="System metrics")
async def get_metrics(db: Session = Depends(get_db)):
    """
    Get system metrics and statistics.
    """
    start_time = datetime.utcnow()
    try:
        # Get download statistics
        total_downloads = db.query(DownloadHistory).count()
        successful_downloads = db.query(DownloadHistory).filter(
            DownloadHistory.status == TaskStatus.SUCCESS
        ).count()

        # Get recent activity
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recent_downloads = db.query(DownloadHistory).filter(
            DownloadHistory.created_at >= last_24h
        ).count()

        # Get cache stats if available
        cache_stats = {}
        try:
            from src.utils.cache import cache_manager
            cache_stats = cache_manager.get_stats()
        except ImportError:
            cache_stats = {"enabled": False}

        # Get system stats if monitoring is enabled
        system_stats = {}
        if monitoring_settings.MONITORING_ENABLED:
            system_stats = monitor.get_system_stats()

        duration = (datetime.utcnow() - start_time).total_seconds() * 1000  # Convert to milliseconds
        log_api_call("/api/v1/metrics", "GET", "system", 200, duration)

        return {
            "downloads": {
                "total": total_downloads,
                "successful": successful_downloads,
                "recent_24h": recent_downloads,
                "success_rate": round(successful_downloads/total_downloads*100, 2) if total_downloads > 0 else 0
            },
            "cache": cache_stats,
            "system": system_stats,
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": duration
        }
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000  # Convert to milliseconds
        logger.error(f"Metrics endpoint error: {e}")
        log_error(f"Metrics endpoint error: {e}", exception=e, context={"duration_ms": duration})
        raise HTTPException(status_code=500, detail="Unable to fetch metrics")

@router.get("/version", summary="Get version information")
async def get_version_info():
    """
    Get current version and check for updates.
    """
    start_time = datetime.utcnow()

    try:
        system_info = version_checker.get_system_info()
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000  # Convert to milliseconds
        log_api_call("/api/v1/version", "GET", "system", 200, duration)

        return {
            "version_info": system_info,
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": duration
        }
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000  # Convert to milliseconds
        logger.error(f"Version endpoint error: {e}")
        log_error(f"Version endpoint error: {e}", exception=e, context={"duration_ms": duration})
        raise HTTPException(status_code=500, detail="Unable to fetch version info")

@router.post("/update", summary="Update the system")
async def update_system(request: Request):
    """
    Update the system to the latest version.
    """
    client_ip = request.client.host if request.client else None
    start_time = datetime.utcnow()

    log_api_call("/api/v1/update", "POST", client_ip, 200)

    try:
        # Check if update is available first
        update_available, latest_version, update_msg = version_checker.is_update_available()

        if not update_available:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.info(f"No update needed: {update_msg}")
            return {
                "status": "no_update_needed",
                "message": update_msg,
                "latest_version": latest_version,
                "timestamp": datetime.utcnow().isoformat(),
                "response_time_ms": duration
            }

        # Perform update
        success, message = version_checker.update_system()

        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        if success:
            logger.info(f"Update completed: {message}")
            log_api_call("/api/v1/update", "POST", client_ip, 200, duration)
            return {
                "status": "updated",
                "message": message,
                "previous_version": version_checker.current_version,
                "timestamp": datetime.utcnow().isoformat(),
                "response_time_ms": duration
            }
        else:
            logger.error(f"Update failed: {message}")
            log_error(f"Update failed: {message}", context={"client_ip": client_ip, "duration_ms": duration})
            return {
                "status": "failed",
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "response_time_ms": duration
            }
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000  # Convert to milliseconds
        logger.error(f"Update endpoint error: {e}")
        log_error(f"Update endpoint error: {e}", exception=e, context={"client_ip": client_ip, "duration_ms": duration})
        raise HTTPException(status_code=500, detail="Unable to perform update")
