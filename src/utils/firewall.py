from typing import List, Dict, Optional, Set
from loguru import logger
import ipaddress
import re
from datetime import datetime
from src.utils.logging.logger import log_error


class SimpleFirewall:
    """Simple firewall implementation for LibraryDown"""
    
    def __init__(self):
        self.allowed_ips: Set[str] = set()
        self.blocked_ips: Set[str] = set()
        self.blocked_countries: Set[str] = set()
        self.rate_limits: Dict[str, Dict] = {}
        self.access_logs: List[Dict] = []
        self.max_log_entries = 1000
    
    def add_allowed_ip(self, ip: str):
        """Add IP to allowed list"""
        try:
            ipaddress.ip_address(ip)  # Validate IP
            self.allowed_ips.add(ip)
            logger.info(f"Added {ip} to allowed IPs")
        except ValueError:
            log_error(f"Invalid IP address: {ip}")
    
    def remove_allowed_ip(self, ip: str):
        """Remove IP from allowed list"""
        self.allowed_ips.discard(ip)
        logger.info(f"Removed {ip} from allowed IPs")
    
    def block_ip(self, ip: str, reason: str = "Manual block"):
        """Block an IP address"""
        try:
            ipaddress.ip_address(ip)  # Validate IP
            self.blocked_ips.add(ip)
            self._log_access(ip, "BLOCKED", reason)
            logger.warning(f"Blocked IP {ip}: {reason}")
        except ValueError:
            log_error(f"Invalid IP address: {ip}")
    
    def unblock_ip(self, ip: str):
        """Unblock an IP address"""
        self.blocked_ips.discard(ip)
        logger.info(f"Unblocked IP {ip}")
    
    def is_ip_allowed(self, ip: str) -> bool:
        """Check if IP is allowed to access the service"""
        # If allowed IPs list is not empty, only allow those IPs
        if self.allowed_ips and ip not in self.allowed_ips:
            return False
        
        # Always block explicitly blocked IPs
        if ip in self.blocked_ips:
            return False
        
        return True
    
    def check_request(self, ip: str, endpoint: str = "/", method: str = "GET") -> tuple[bool, str]:
        """Check if request should be allowed"""
        # First check IP-based access
        if not self.is_ip_allowed(ip):
            reason = f"IP {ip} not in allowed list or explicitly blocked"
            self._log_access(ip, "DENIED", reason, endpoint, method)
            return False, reason
        
        # Check rate limits
        if self._check_rate_limit(ip, endpoint):
            reason = f"Rate limit exceeded for IP {ip} on endpoint {endpoint}"
            self._log_access(ip, "RATE_LIMITED", reason, endpoint, method)
            return False, reason
        
        # All checks passed
        self._log_access(ip, "ALLOWED", "Passed all checks", endpoint, method)
        return True, "Access granted"
    
    def _check_rate_limit(self, ip: str, endpoint: str) -> bool:
        """Check if request exceeds rate limit for IP and endpoint"""
        key = f"{ip}:{endpoint}"
        
        current_time = datetime.now().timestamp()
        
        if key not in self.rate_limits:
            self.rate_limits[key] = {
                "requests": [],
                "window_start": current_time
            }
        
        # Remove requests older than 1 minute
        self.rate_limits[key]["requests"] = [
            req_time for req_time in self.rate_limits[key]["requests"]
            if current_time - req_time < 60  # 1 minute window
        ]
        
        # Add current request
        self.rate_limits[key]["requests"].append(current_time)
        
        # Check if limit exceeded (max 10 requests per minute per IP-endpoint combination)
        if len(self.rate_limits[key]["requests"]) > 10:
            return True  # Rate limit exceeded
        
        return False  # Within limits
    
    def _log_access(self, ip: str, action: str, reason: str, endpoint: str = "/", method: str = "GET"):
        """Log access attempt"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "ip": ip,
            "action": action,
            "reason": reason,
            "endpoint": endpoint,
            "method": method
        }
        
        self.access_logs.append(log_entry)
        
        # Keep only recent logs
        if len(self.access_logs) > self.max_log_entries:
            self.access_logs = self.access_logs[-self.max_log_entries:]
    
    def get_access_logs(self, limit: int = 100) -> List[Dict]:
        """Get recent access logs"""
        return self.access_logs[-limit:]
    
    def get_firewall_stats(self) -> Dict:
        """Get firewall statistics"""
        allowed_requests = sum(1 for log in self.access_logs if log["action"] == "ALLOWED")
        denied_requests = sum(1 for log in self.access_logs if log["action"] == "DENIED")
        rate_limited_requests = sum(1 for log in self.access_logs if log["action"] == "RATE_LIMITED")
        blocked_requests = sum(1 for log in self.access_logs if log["action"] == "BLOCKED")
        
        return {
            "allowed_ips_count": len(self.allowed_ips),
            "blocked_ips_count": len(self.blocked_ips),
            "total_access_logs": len(self.access_logs),
            "allowed_requests": allowed_requests,
            "denied_requests": denied_requests,
            "rate_limited_requests": rate_limited_requests,
            "blocked_requests": blocked_requests,
            "timestamp": datetime.now().isoformat()
        }
    
    def block_country(self, country_code: str):
        """Block all IPs from a specific country (would require GeoIP lookup in practice)"""
        self.blocked_countries.add(country_code.upper())
        logger.info(f"Blocking country: {country_code}")
    
    def unblock_country(self, country_code: str):
        """Unblock a country"""
        self.blocked_countries.discard(country_code.upper())
        logger.info(f"Unblocking country: {country_code}")


# Global firewall instance
firewall = SimpleFirewall()