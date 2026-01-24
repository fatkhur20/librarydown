import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class LoggerSetup:
    """Comprehensive logging system for LibraryDown"""
    
    def __init__(self, name: str = "librarydown", log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """Setup logger with multiple handlers and formatters"""
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers to avoid duplication
        logger.handlers.clear()
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        # File handler for all logs
        all_log_file = self.log_dir / "all.log"
        all_handler = logging.FileHandler(all_log_file)
        all_handler.setLevel(logging.DEBUG)
        all_handler.setFormatter(formatter)
        logger.addHandler(all_handler)
        
        # File handler for errors only
        error_log_file = self.log_dir / "errors.log"
        error_handler = logging.FileHandler(error_log_file)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def get_logger(self):
        """Return configured logger instance"""
        return self.logger


def get_logger(name: str = "librarydown") -> logging.Logger:
    """Get configured logger instance"""
    setup = LoggerSetup(name)
    return setup.get_logger()


# Global logger instance
logger = get_logger()


def log_api_call(endpoint: str, method: str, user_id: Optional[str] = None, 
                 status_code: Optional[int] = None, duration: Optional[float] = None):
    """Log API call details"""
    log_data = {
        "endpoint": endpoint,
        "method": method,
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "status_code": status_code,
        "duration_ms": duration
    }
    logger.info(f"API_CALL: {log_data}")


def log_download_event(url: str, user_id: str, status: str, 
                      file_size: Optional[int] = None, duration: Optional[float] = None):
    """Log download event details"""
    log_data = {
        "url": url,
        "user_id": user_id,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "file_size_bytes": file_size,
        "duration_ms": duration
    }
    logger.info(f"DOWNLOAD_EVENT: {log_data}")


def log_bot_interaction(user_id: str, chat_id: str, command: str, 
                       message_text: Optional[str] = None):
    """Log bot interaction details"""
    log_data = {
        "user_id": user_id,
        "chat_id": chat_id,
        "command": command,
        "timestamp": datetime.utcnow().isoformat(),
        "message_text": message_text
    }
    logger.info(f"BOT_INTERACTION: {log_data}")


def log_error(error_msg: str, exception: Optional[Exception] = None, 
              context: Optional[dict] = None):
    """Log error with optional exception and context"""
    log_data = {
        "error_msg": error_msg,
        "timestamp": datetime.utcnow().isoformat(),
        "exception": str(exception) if exception else None,
        "context": context
    }
    logger.error(f"ERROR: {log_data}")