from pydantic_settings import BaseSettings
from typing import Optional


class MonitoringSettings(BaseSettings):
    """Configuration for monitoring system"""
    
    # Monitoring settings
    MONITORING_ENABLED: bool = True
    MONITORING_INTERVAL: int = 60  # seconds
    LOG_LEVEL: str = "INFO"
    LOG_RETENTION_DAYS: int = 30
    
    # Health check settings
    HEALTH_CHECK_TIMEOUT: int = 30
    METRICS_ENABLED: bool = True
    
    # Performance thresholds
    CPU_THRESHOLD: float = 80.0  # percentage
    MEMORY_THRESHOLD: float = 80.0  # percentage
    DISK_THRESHOLD: float = 90.0  # percentage
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields from .env


# Global monitoring settings instance
monitoring_settings = MonitoringSettings()