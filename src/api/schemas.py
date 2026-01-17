from pydantic import BaseModel, HttpUrl
from typing import Any, Dict, Optional, Literal
from datetime import datetime

class DownloadRequest(BaseModel):
    url: HttpUrl
    quality: Optional[str] = "720p"  # Default quality (e.g., "720p", "1080p", "audio")

class DownloadResponse(BaseModel):
    task_id: str
    status: str
    platform: Optional[str] = None

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Dict[str, Any] | None = None

class DownloadHistoryResponse(BaseModel):
    id: int
    task_id: str
    url: str
    platform: str
    status: str
    title: Optional[str] = None
    author: Optional[str] = None
    duration: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

class VideoFormat(BaseModel):
    format_id: str
    quality: str
    ext: str
    filesize_mb: Optional[float] = None  # File size in MB
    height: Optional[int] = None
    width: Optional[int] = None
    fps: Optional[int] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    format_note: Optional[str] = None  # e.g., "audio only", "video only"

class FormatsResponse(BaseModel):
    platform: str
    url: str
    title: Optional[str] = None
    thumbnail: Optional[str] = None
    duration: Optional[float] = None
    formats: list[VideoFormat]
