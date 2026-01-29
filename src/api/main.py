from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from src.core.config import settings
from src.api.routers import downloads, system, media
from src.database.base import engine, Base
from loguru import logger
from src.utils.logging.monitor import monitor
from src.config.monitoring_config import monitoring_settings
from src.utils.version_checker import VersionChecker
import os

# Create media directory if it doesn't exist
os.makedirs(settings.MEDIA_FOLDER, exist_ok=True)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"])

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version=settings.VERSION,
    description="Universal Social Media Downloader API - Download videos from TikTok, YouTube, Instagram, and Twitter",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the media directory to be served at the '/media' URL path
app.mount("/media", StaticFiles(directory=settings.MEDIA_FOLDER), name="media")

# Include API routes
app.include_router(downloads.router, prefix=settings.API_V1_STR, tags=["Downloads"])
app.include_router(system.router, prefix=settings.API_V1_STR, tags=["System"])
app.include_router(media.router, prefix=settings.API_V1_STR, tags=["Media"])

@app.on_event("startup")
async def startup_event():
    global version_checker
    logger.info(f"{settings.APP_NAME} v{settings.VERSION} is starting...")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Rate limit: {settings.RATE_LIMIT_PER_MINUTE} requests/minute")
    
    # Initialize version checker
    from src.utils.version_checker import VersionChecker
    version_checker = VersionChecker(current_version=settings.VERSION)
    
    # Start monitoring if enabled
    if monitoring_settings.MONITORING_ENABLED:
        monitor.start_monitoring(monitoring_settings.MONITORING_INTERVAL)
        logger.info(f"System monitoring started with interval {monitoring_settings.MONITORING_INTERVAL}s")
        # Log initial system stats
        initial_stats = monitor.get_system_stats()
        logger.info(f"Initial system stats - CPU: {initial_stats.get('cpu_percent')}%, Memory: {initial_stats.get('memory_percent')}%, Disk: {initial_stats.get('disk_usage')}%")

    # Check for YouTube tokens on startup
    token_path = os.path.join(os.getcwd(), "data", "youtube_tokens.json")
    if not os.path.exists(token_path):
        logger.warning("YouTube tokens not found. Triggering initial token refresh task...")
        try:
            from src.workers.tasks import refresh_youtube_tokens_task
            refresh_youtube_tokens_task.delay()
            logger.info("Initial token refresh task queued.")
        except Exception as e:
            logger.error(f"Failed to queue initial token refresh: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"{settings.APP_NAME} is shutting down...")
    
    # Stop monitoring if enabled
    if monitoring_settings.MONITORING_ENABLED:
        monitor.stop_monitoring()
        logger.info("System monitoring stopped")

@app.get("/", tags=["Root"])
async def read_root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.VERSION,
        "docs": "/docs",
        "supported_platforms": ["TikTok", "YouTube", "Instagram", "Twitter"]
    }
