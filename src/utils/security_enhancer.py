import hashlib
import hmac
import time
from typing import Optional, Dict, Any
from loguru import logger
from src.config.monitoring_config import monitoring_settings
from src.utils.logging.logger import log_error
import re
from datetime import datetime, timedelta


class SecurityEnhancer:
    """Additional security features for LibraryDown"""
    
    def __init__(self):
        self.rate_limit_storage = {}  # In-memory rate limiting storage
        self.blocked_ips = set()  # Blocked IP addresses
        self.failed_attempts = {}  # Track failed attempts
        self.encryption_key = None  # Will be set from environment
    
    def setup_encryption_key(self, key: str):
        """Setup encryption key from environment"""
        self.encryption_key = key.encode() if isinstance(key, str) else key
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data using HMAC"""
        if not self.encryption_key:
            raise ValueError("Encryption key not set")
        
        timestamp = str(int(time.time()))
        data_with_time = f"{data}|{timestamp}"
        signature = hmac.new(self.encryption_key, data_with_time.encode(), hashlib.sha256).hexdigest()
        return f"{data_with_time}|{signature}"
    
    def decrypt_data(self, encrypted_data: str) -> Optional[str]:
        """Decrypt sensitive data and verify integrity"""
        if not self.encryption_key:
            raise ValueError("Encryption key not set")
        
        parts = encrypted_data.split("|")
        if len(parts) != 3:
            return None
        
        original_data, timestamp_str, signature = parts
        
        # Verify signature
        expected_signature = hmac.new(
            self.encryption_key, 
            f"{original_data}|{timestamp_str}".encode(), 
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            log_error("Data integrity check failed", context={"encrypted_data": encrypted_data})
            return None
        
        # Verify timestamp (within 1 hour)
        try:
            timestamp = int(timestamp_str)
            if abs(time.time() - timestamp) > 3600:  # 1 hour
                log_error("Encrypted data expired", context={"timestamp": timestamp})
                return None
        except ValueError:
            return None
        
        return original_data
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        return ip in self.blocked_ips
    
    def block_ip(self, ip: str, duration: int = 3600):
        """Block an IP address for a duration (seconds)"""
        self.blocked_ips.add(ip)
        logger.warning(f"IP {ip} blocked for {duration} seconds")
        
        # Schedule unblock
        import threading
        def unblock():
            time.sleep(duration)
            self.unblock_ip(ip)
        
        thread = threading.Thread(target=unblock, daemon=True)
        thread.start()
    
    def unblock_ip(self, ip: str):
        """Unblock an IP address"""
        self.blocked_ips.discard(ip)
        logger.info(f"IP {ip} unblocked")
    
    def check_rate_limit(self, identifier: str, limit: int, window: int = 60) -> tuple[bool, int]:
        """
        Check if request exceeds rate limit
        Returns (is_allowed, remaining_requests)
        """
        current_time = time.time()
        
        if identifier not in self.rate_limit_storage:
            self.rate_limit_storage[identifier] = []
        
        # Clean old requests outside the window
        self.rate_limit_storage[identifier] = [
            req_time for req_time in self.rate_limit_storage[identifier] 
            if current_time - req_time < window
        ]
        
        # Check if limit exceeded
        current_requests = len(self.rate_limit_storage[identifier])
        remaining = limit - current_requests
        
        if current_requests >= limit:
            return False, 0
        
        # Record this request
        self.rate_limit_storage[identifier].append(current_time)
        return True, remaining
    
    def track_failed_attempt(self, ip: str, reason: str = "authentication"):
        """Track failed attempts for an IP"""
        if ip not in self.failed_attempts:
            self.failed_attempts[ip] = {
                "attempts": [],
                "last_reset": time.time()
            }
        
        # Reset counter if too much time passed
        if time.time() - self.failed_attempts[ip]["last_reset"] > 3600:  # 1 hour
            self.failed_attempts[ip] = {
                "attempts": [],
                "last_reset": time.time()
            }
        
        self.failed_attempts[ip]["attempts"].append({
            "timestamp": time.time(),
            "reason": reason
        })
        
        # Block IP if too many failed attempts
        recent_attempts = [
            attempt for attempt in self.failed_attempts[ip]["attempts"]
            if time.time() - attempt["timestamp"] < 300  # Last 5 minutes
        ]
        
        if len(recent_attempts) >= 5:  # 5 failed attempts in 5 minutes
            self.block_ip(ip, 3600)  # Block for 1 hour
            logger.warning(f"IP {ip} blocked due to multiple failed attempts")
    
    def validate_input(self, input_str: str, pattern: str = None) -> bool:
        """Validate input against common attack patterns"""
        # Check for common attack patterns
        dangerous_patterns = [
            r'<script',  # XSS
            r'javascript:',  # XSS
            r'on\w+\s*=',  # Event handlers
            r'\.\./',  # Directory traversal
            r'%2e%2e%2f',  # Encoded directory traversal
            r'\.\.\%2f',  # Mixed encoding
            r'union\s+select',  # SQL injection
            r'\';\s*\w+',  # SQL injection
            r'exec\s*\(',  # Command injection
            r'eval\s*\(',  # Code injection
        ]
        
        test_str = input_str.lower()
        
        for pattern in dangerous_patterns:
            if re.search(pattern, test_str):
                return False
        
        # If custom pattern provided, validate against it
        if pattern:
            if not re.fullmatch(pattern, input_str):
                return False
        
        return True
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent directory traversal and other attacks"""
        # Remove dangerous characters
        sanitized = re.sub(r'[^\w\-_.]', '_', filename)
        
        # Prevent directory traversal
        sanitized = sanitized.replace('../', '').replace('..\\', '')
        sanitized = sanitized.replace('./', '').replace('.\\', '')
        
        # Limit length
        if len(sanitized) > 255:
            name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
            sanitized = name[:250] + ('.' + ext if ext else '')
        
        return sanitized
    
    def get_security_report(self) -> Dict[str, Any]:
        """Get security-related statistics"""
        current_time = time.time()
        
        # Calculate active blocks
        active_blocks = len(self.blocked_ips)
        
        # Calculate rate limit stats
        rate_limited_endpoints = len(self.rate_limit_storage)
        
        # Calculate failed attempts stats
        recent_failed_attempts = 0
        for ip, data in self.failed_attempts.items():
            recent_attempts = [
                attempt for attempt in data["attempts"]
                if current_time - attempt["timestamp"] < 300  # Last 5 minutes
            ]
            recent_failed_attempts += len(recent_attempts)
        
        return {
            "active_blocks": active_blocks,
            "rate_limited_endpoints": rate_limited_endpoints,
            "recent_failed_attempts": recent_failed_attempts,
            "timestamp": datetime.utcnow().isoformat()
        }


# Global security enhancer instance
security_enhancer = SecurityEnhancer()