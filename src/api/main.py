from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from src.core.config import settings
from src.api.endpoints import router as api_router
from src.database.base import engine, Base
from loguru import logger
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
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    logger.info(f"{settings.APP_NAME} v{settings.VERSION} is starting...")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Rate limit: {settings.RATE_LIMIT_PER_MINUTE} requests/minute")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"{settings.APP_NAME} is shutting down...")

@app.get("/", tags=["Root"])
async def read_root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.VERSION,
        "docs": "/docs",
        "supported_platforms": ["TikTok", "YouTube", "Instagram", "Twitter"]
    }
