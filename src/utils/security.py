"""Security utilities for input validation and protection."""

import re
from urllib.parse import urlparse
from typing import Optional, List, Dict, Any
import ipaddress
from loguru import logger


class SecurityValidator:
    """Comprehensive security validation utilities."""
    
    # Dangerous protocols that should be blocked
    DANGEROUS_PROTOCOLS = ['file', 'javascript', 'vbscript', 'data', 'blob']
    
    # Private/reserved IP ranges that should be blocked
    PRIVATE_IP_RANGES = [
        '127.0.0.0/8',      # Loopback
        '10.0.0.0/8',       # Private network
        '172.16.0.0/12',    # Private network
        '192.168.0.0/16',   # Private network
        '169.254.0.0/16',   # Link-local
        '::1/128',          # IPv6 loopback
        'fc00::/7',         # IPv6 private
        'fe80::/10',        # IPv6 link-local
    ]
    
    # Allowed domains for social media platforms
    ALLOWED_DOMAINS = {
        'youtube.com', 'youtu.be', 'youtube-nocookie.com',
        'tiktok.com', 'vt.tiktok.com',
        'instagram.com', 'instagr.am',
        'twitter.com', 'x.com', 't.co',
        'reddit.com', 'redd.it',
        'soundcloud.com',
        'dailymotion.com', 'dai.ly',
        'twitch.tv',
        'vimeo.com',
        'facebook.com', 'fb.watch',
        'bilibili.com', 'b23.tv',
        'linkedin.com',
        'pinterest.com', 'pin.it'
    }
    
    @classmethod
    def validate_url(cls, url: str) -> tuple[bool, str]:
        """Validate URL for security and supported platforms.
        
        Args:
            url: URL to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not url or not isinstance(url, str):
            return False, "URL must be a non-empty string"
            
        url = url.strip()
        
        # Basic format validation
        try:
            parsed = urlparse(url)
        except Exception:
            return False, "Invalid URL format"
            
        # Check protocol
        if not parsed.scheme:
            # Add https if missing
            url = 'https://' + url
            parsed = urlparse(url)
        elif parsed.scheme in cls.DANGEROUS_PROTOCOLS:
            return False, f"Dangerous protocol '{parsed.scheme}' not allowed"
            
        # Validate domain
        if not parsed.netloc:
            return False, "URL must contain a domain"
            
        domain = parsed.netloc.lower()
        
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]
            
        # Check for private IP addresses
        try:
            ip_obj = ipaddress.ip_address(domain)
            for ip_range in cls.PRIVATE_IP_RANGES:
                if ipaddress.ip_address(ip_obj) in ipaddress.ip_network(ip_range):
                    return False, "Private IP addresses not allowed"
        except ValueError:
            # Not an IP address, check domain
            pass
            
        # Check domain against allowed list
        domain_parts = domain.split('.')
        # Check main domain and subdomains
        valid_domain = False
        for i in range(len(domain_parts)):
            check_domain = '.'.join(domain_parts[i:])
            if check_domain in cls.ALLOWED_DOMAINS:
                valid_domain = True
                break
                
        if not valid_domain:
            return False, f"Domain '{domain}' not in allowed list"
            
        # Additional security checks
        if cls._contains_suspicious_patterns(url):
            return False, "URL contains suspicious patterns"
            
        return True, ""
    
    @classmethod
    def _contains_suspicious_patterns(cls, url: str) -> bool:
        """Check for suspicious URL patterns."""
        suspicious_patterns = [
            r'\.\./',           # Path traversal
            r'\.\\',            # Windows path traversal
            r'%2e%2e/',         # URL encoded path traversal
            r'localhost',       # Local references
            r'127\.0\.0\.1',    # Loopback IP
            r'\${.*}',          # Template injection
            r'<script',         # XSS attempts
            r'javascript:',     # JavaScript injection
        ]
        
        url_lower = url.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, url_lower):
                return True
        return False
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename to prevent path traversal and injection.
        
        Args:
            filename: Filename to sanitize
            
        Returns:
            Sanitized filename
        """
        if not filename:
            return "unnamed_file"
            
        # Remove dangerous characters
        dangerous_chars = '<>:"/\\|?*\x00-\x1f'
        for char in dangerous_chars:
            filename = filename.replace(char, '_')
            
        # Remove path traversal attempts
        filename = filename.replace('../', '').replace('..\\', '')
        
        # Limit length
        if len(filename) > 255:
            filename = filename[:255]
            
        # Ensure it's not empty
        if not filename.strip():
            return "unnamed_file"
            
        return filename.strip()
    
    @classmethod
    def validate_media_path(cls, base_path: str, requested_path: str) -> tuple[bool, str]:
        """Validate media file path to prevent directory traversal.
        
        Args:
            base_path: Base media directory
            requested_path: Requested file path
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        import os
        
        try:
            # Resolve the requested path
            requested_full = os.path.abspath(os.path.join(base_path, requested_path))
            base_full = os.path.abspath(base_path)
            
            # Check if requested path is within base path
            if not requested_full.startswith(base_full):
                return False, "Path traversal attempt detected"
                
            return True, ""
            
        except Exception as e:
            return False, f"Path validation error: {str(e)}"
    
    @classmethod
    def get_security_headers(cls) -> Dict[str, str]:
        """Get recommended security headers."""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: https:; font-src 'self'",
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }


# Global validator instance
security_validator = SecurityValidator()