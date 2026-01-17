from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Enum
from datetime import datetime
from src.database.base import Base
import enum

class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROGRESS = "PROGRESS"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"

class PlatformType(str, enum.Enum):
    TIKTOK = "TIKTOK"
    YOUTUBE = "YOUTUBE"
    INSTAGRAM = "INSTAGRAM"
    TWITTER = "TWITTER"
    REDDIT = "REDDIT"
    SOUNDCLOUD = "SOUNDCLOUD"
    DAILYMOTION = "DAILYMOTION"
    TWITCH = "TWITCH"
    VIMEO = "VIMEO"
    FACEBOOK = "FACEBOOK"
    BILIBILI = "BILIBILI"
    LINKEDIN = "LINKEDIN"
    PINTEREST = "PINTEREST"

class DownloadHistory(Base):
    __tablename__ = "download_history"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True, nullable=False)
    url = Column(Text, nullable=False)
    platform = Column(Enum(PlatformType), nullable=False)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Download metadata
    title = Column(String, nullable=True)
    author = Column(String, nullable=True)
    duration = Column(Float, nullable=True)  # Video duration in seconds
    file_size = Column(Integer, nullable=True)  # File size in bytes
    file_path = Column(Text, nullable=True)  # Path to downloaded file
    thumbnail_path = Column(Text, nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Request metadata
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)

    def __repr__(self):
        return f"<DownloadHistory(task_id={self.task_id}, platform={self.platform}, status={self.status})>"
