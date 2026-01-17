from src.workers.celery_app import celery_app
from src.core.config import settings
from loguru import logger
import os
from datetime import datetime, timedelta
from pathlib import Path

@celery_app.task
def cleanup_old_files():
    """
    Periodic task to clean up old downloaded files based on TTL.
    Runs every hour via Celery Beat.
    """
    logger.info(f"[Cleanup] Starting cleanup task. TTL: {settings.FILE_TTL_HOURS} hours")
    
    media_folder = Path(settings.MEDIA_FOLDER)
    
    if not media_folder.exists():
        logger.warning(f"[Cleanup] Media folder does not exist: {media_folder}")
        return {
            'status': 'skipped',
            'reason': 'media folder not found'
        }
    
    cutoff_time = datetime.now() - timedelta(hours=settings.FILE_TTL_HOURS)
    deleted_count = 0
    total_size_freed = 0
    
    try:
        for file_path in media_folder.iterdir():
            if not file_path.is_file():
                continue
            
            # Check file modification time
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            if file_mtime < cutoff_time:
                file_size = file_path.stat().st_size
                try:
                    file_path.unlink()
                    deleted_count += 1
                    total_size_freed += file_size
                    logger.debug(f"[Cleanup] Deleted: {file_path.name} (age: {datetime.now() - file_mtime})")
                except Exception as e:
                    logger.error(f"[Cleanup] Failed to delete {file_path.name}: {e}")
        
        # Convert bytes to MB
        size_freed_mb = total_size_freed / (1024 * 1024)
        
        logger.info(
            f"[Cleanup] Completed. Deleted {deleted_count} files, "
            f"freed {size_freed_mb:.2f} MB"
        )
        
        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'size_freed_mb': round(size_freed_mb, 2),
            'cutoff_time': cutoff_time.isoformat()
        }
        
    except Exception as e:
        logger.exception(f"[Cleanup] Cleanup task failed: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }
