"""Test configuration and fixtures."""

import sys
import os
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.api.main import app
from src.database.base import Base
from src.core.config import settings


# Test database configuration
TEST_DATABASE_URL = "sqlite:///./test_librarydown.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=test_engine
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db():
    """Create test database tables."""
    Base.metadata.create_all(bind=test_engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client() -> Generator:
    """Create test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def mock_redis():
    """Mock Redis client for testing."""
    with patch('src.utils.cache.redis.Redis') as mock_redis:
        mock_instance = Mock()
        mock_instance.ping.return_value = True
        mock_instance.get.return_value = None
        mock_instance.setex.return_value = True
        mock_redis.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="function")
def mock_httpx():
    """Mock HTTPX client for testing."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_instance = Mock()
        mock_instance.__aenter__ = Mock(return_value=mock_instance)
        mock_instance.__aexit__ = Mock(return_value=None)
        mock_client.return_value = mock_instance
        yield mock_instance


# Test data fixtures
@pytest.fixture
def sample_youtube_url():
    """Sample YouTube URL for testing."""
    return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


@pytest.fixture
def sample_tiktok_url():
    """Sample TikTok URL for testing."""
    return "https://vt.tiktok.com/ZS593uwQc/"


@pytest.fixture
def valid_cookie_content():
    """Valid Netscape cookie format for testing."""
    return """# Netscape HTTP Cookie File
.youtube.com	TRUE	/	FALSE	2147483647	YSC	abc123def456
.youtube.com	TRUE	/	FALSE	2147483647	SID	google123456
"""


@pytest.fixture
def invalid_cookie_content():
    """Invalid cookie content for testing."""
    return """# Invalid format
This is not a proper cookie file
Random text without proper structure
"""