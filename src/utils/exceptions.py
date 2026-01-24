"""Custom exceptions for the LibraryDown project."""

from typing import Optional


class LibraryDownError(Exception):
    """Base exception for all LibraryDown errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class PlatformNotSupportedError(LibraryDownError):
    """Raised when a platform is not supported."""
    
    def __init__(self, platform: str, url: str = ""):
        message = f"Platform '{platform}' is not supported"
        if url:
            message += f" for URL: {url}"
        super().__init__(message, "PLATFORM_NOT_SUPPORTED")


class ContentNotFoundError(LibraryDownError):
    """Raised when content is not found or unavailable."""
    
    def __init__(self, platform: str, url: str):
        message = f"Content not found on {platform}: {url}"
        super().__init__(message, "CONTENT_NOT_FOUND")


class NetworkError(LibraryDownError):
    """Raised for network-related issues."""
    
    def __init__(self, platform: str, url: str, original_error: Optional[Exception] = None):
        message = f"Network error while accessing {platform}: {url}"
        if original_error:
            message += f" ({str(original_error)})"
        super().__init__(message, "NETWORK_ERROR")


class AuthenticationRequiredError(LibraryDownError):
    """Raised when authentication/cookies are required but missing."""
    
    def __init__(self, platform: str, url: str):
        message = f"Authentication required for {platform}: {url}. Please provide valid cookies."
        super().__init__(message, "AUTHENTICATION_REQUIRED")


class DownloadError(LibraryDownError):
    """Raised when download fails."""
    
    def __init__(self, platform: str, url: str, reason: str):
        message = f"Download failed for {platform}: {url} - {reason}"
        super().__init__(message, "DOWNLOAD_FAILED")


class ValidationError(LibraryDownError):
    """Raised for input validation errors."""
    
    def __init__(self, field: str, value: str, reason: str):
        message = f"Validation error for '{field}': {value} - {reason}"
        super().__init__(message, "VALIDATION_ERROR")


class ConfigurationError(LibraryDownError):
    """Raised for configuration-related errors."""
    
    def __init__(self, setting: str, reason: str):
        message = f"Configuration error for '{setting}': {reason}"
        super().__init__(message, "CONFIGURATION_ERROR")


def handle_platform_exception(platform: str, url: str, exception: Exception) -> LibraryDownError:
    """Convert platform-specific exceptions to standardized LibraryDown errors.
    
    Args:
        platform: Platform name
        url: URL being processed
        exception: Original exception
        
    Returns:
        Appropriate LibraryDownError instance
    """
    error_msg = str(exception).lower()
    
    # Handle common error patterns
    if "not found" in error_msg or "404" in error_msg:
        return ContentNotFoundError(platform, url)
    elif "forbidden" in error_msg or "unauthorized" in error_msg or "login" in error_msg:
        return AuthenticationRequiredError(platform, url)
    elif "network" in error_msg or "timeout" in error_msg or "connection" in error_msg:
        return NetworkError(platform, url, exception)
    elif "unsupported" in error_msg or "not supported" in error_msg:
        return PlatformNotSupportedError(platform, url)
    else:
        return DownloadError(platform, url, str(exception))