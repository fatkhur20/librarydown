from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Universal Social Media Downloader"
    VERSION: str = "2.0.0"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    API_BASE_URL: str = "http://localhost:8000"

    # Security
    ALLOWED_ORIGINS: list = ["*"]  # CORS origins
    RATE_LIMIT_PER_MINUTE: int = 10  # API rate limit per IP

    # Redis Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Celery Settings
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # Database Settings
    DATABASE_NAME: str = "librarydown.db"

    # File Management
    MEDIA_FOLDER: str = "media"
    FILE_TTL_HOURS: int = 24  # Files will be deleted after 24 hours
    MAX_FILE_SIZE_MB: int = 500  # Maximum file size to download

    # Task Settings
    MAX_RETRIES: int = 3
    RETRY_BACKOFF: int = 5  # Base seconds for exponential backoff

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra='ignore'
    )

settings = Settings()
