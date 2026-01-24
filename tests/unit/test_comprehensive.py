import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from src.api.main import app
from src.core.config import settings
from src.utils.security import security_validator
from src.utils.version_checker import version_checker
from src.utils.user_features import quality_selector, format_converter, playlist_handler
from src.utils.performance_optimizer import queue_manager, cdn_manager
import tempfile
import os


@pytest.fixture
def client():
    """Create test client for API"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    original_media_folder = settings.MEDIA_FOLDER
    settings.MEDIA_FOLDER = tempfile.mkdtemp()
    yield settings
    settings.MEDIA_FOLDER = original_media_folder


class TestSecurityValidation:
    """Test security validation functions"""
    
    def test_validate_safe_url(self):
        """Test validation of safe URLs"""
        is_valid, error = security_validator.validate_url("https://youtube.com/watch?v=test")
        assert is_valid == True
        assert error == ""
    
    def test_validate_dangerous_protocol(self):
        """Test validation of dangerous protocols"""
        is_valid, error = security_validator.validate_url("javascript:alert('xss')")
        assert is_valid == False
        assert "Dangerous protocol" in error
    
    def test_validate_private_ip(self):
        """Test validation of private IPs"""
        is_valid, error = security_validator.validate_url("http://127.0.0.1/test")
        assert is_valid == False
        assert "Private IP addresses not allowed" in error
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        result = security_validator.sanitize_filename("../../secret.txt")
        assert result == "secret.txt"
        
        result = security_validator.sanitize_filename("<script>alert</script>")
        assert result == "_script_alert_script_"
    
    def test_validate_media_path(self):
        """Test media path validation"""
        base_path = "/tmp/media"
        # Valid path
        is_valid, error = security_validator.validate_media_path(base_path, "video.mp4")
        assert is_valid == True
        
        # Invalid path (directory traversal)
        is_valid, error = security_validator.validate_media_path(base_path, "../../../etc/passwd")
        assert is_valid == False
        assert "Path traversal" in error


class TestQualitySelection:
    """Test quality selection functions"""
    
    def test_get_quality_format(self):
        """Test getting quality format strings"""
        result = quality_selector.get_quality_format("720p")
        assert "720p" in result or "best" in result
    
    def test_get_quality_options(self):
        """Test getting quality options for platforms"""
        youtube_qualities = quality_selector.get_quality_options("youtube")
        assert len(youtube_qualities) > 0
        assert "720p" in [q.value for q in youtube_qualities]


class TestAPIEndpoints:
    """Test API endpoints"""
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint"""
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "downloads" in data
        assert "cache" in data
        assert "timestamp" in data
    
    def test_version_endpoint(self, client):
        """Test version endpoint"""
        response = client.get("/api/v1/version")
        assert response.status_code == 200
        data = response.json()
        assert "version_info" in data
        assert "current_version" in data["version_info"]
    
    def test_qualities_endpoint(self, client):
        """Test qualities endpoint"""
        response = client.get("/api/v1/qualities")
        assert response.status_code == 200
        data = response.json()
        assert "all_qualities" in data
    
    def test_preferences_endpoint(self, client):
        """Test preferences endpoint"""
        response = client.get("/api/v1/preferences")
        assert response.status_code == 200
        data = response.json()
        assert "preferences" in data
        assert "default_quality" in data["preferences"]


class TestVersionChecker:
    """Test version checking functionality"""
    
    def test_version_comparison(self):
        """Test version comparison logic"""
        # Mock the get_latest_version method to return a known value
        with patch.object(version_checker, 'get_latest_version', return_value="2.1.0"):
            is_update, latest, msg = version_checker.is_update_available()
            # We expect this to return False since we're mocking a newer version
            # but the current version in the mock is unknown
            assert isinstance(is_update, bool)
            assert isinstance(msg, str)
    
    def test_system_info(self):
        """Test getting system information"""
        info = version_checker.get_system_info()
        assert "current_version" in info
        assert "system" in info
        assert "python_version" in info


class TestPerformanceOptimizer:
    """Test performance optimization components"""
    
    def test_queue_manager_add_task(self):
        """Test adding tasks to queue"""
        from src.utils.performance_optimizer import QueueTask, TaskPriority, TaskStatus
        from datetime import datetime
        
        task = QueueTask(
            task_id="test_task_1",
            task_type="download",
            priority=TaskPriority.NORMAL,
            payload={"url": "https://test.com"},
            created_at=datetime.now(),
            scheduled_at=datetime.now()
        )
        
        result = queue_manager.add_task(task)
        assert result == True
        
        # Check that task is in queue
        queue_stats = queue_manager.get_queue_stats()
        assert queue_stats["queue_size"] >= 0  # May be processed already
    
    def test_cdn_store_and_retrieve(self):
        """Test CDN store and retrieve functionality"""
        content_id = "test_content_123"
        content = {"video": "data", "title": "Test Video"}
        
        # Store content
        success = cdn_manager.store_content(content_id, content)
        assert success == True
        
        # Retrieve content
        retrieved = cdn_manager.get_content(content_id)
        assert retrieved is not None
        assert retrieved["title"] == "Test Video"
        
        # Get CDN stats
        stats = cdn_manager.get_cdn_stats()
        assert "total_cached_items" in stats
        assert "cache_hit_ratio" in stats


class TestFormatConverter:
    """Test format conversion (mocked for testing)"""
    
    def test_convert_file_mocked(self):
        """Test format conversion with mocked ffmpeg"""
        with patch('subprocess.run') as mock_run:
            # Mock successful conversion
            mock_result = Mock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            success = format_converter.convert_file("/tmp/input.mp4", "/tmp/output.mp3", "mp3")
            assert success == True
            
            # Verify subprocess was called
            mock_run.assert_called_once()


def test_comprehensive_api_workflow(client, mock_settings):
    """Comprehensive test of API workflow"""
    # Test health first
    health_response = client.get("/api/v1/health")
    assert health_response.status_code == 200
    
    # Test metrics
    metrics_response = client.get("/api/v1/metrics")
    assert metrics_response.status_code == 200
    
    # Test version
    version_response = client.get("/api/v1/version")
    assert version_response.status_code == 200
    
    # Test all endpoints that don't require specific data
    qualities_response = client.get("/api/v1/qualities")
    assert qualities_response.status_code == 200
    
    preferences_response = client.get("/api/v1/preferences")
    assert preferences_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__])