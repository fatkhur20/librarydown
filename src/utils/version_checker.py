import requests
import subprocess
import os
import sys
from typing import Dict, Optional, Tuple
from packaging import version
from loguru import logger
import tempfile
import shutil


class VersionChecker:
    """Version checking and auto-update system for LibraryDown"""
    
    def __init__(self, current_version: str, repo_owner: str = "fatkhur20", repo_name: str = "librarydown"):
        self.current_version = current_version
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    
    def get_latest_version(self) -> Optional[str]:
        """Get the latest version from GitHub releases"""
        try:
            response = requests.get(f"{self.github_api_url}/releases/latest", timeout=10)
            response.raise_for_status()
            release_info = response.json()
            tag_name = release_info.get("tag_name", "")
            
            # Remove 'v' prefix if present
            if tag_name.startswith("v"):
                tag_name = tag_name[1:]
            
            return tag_name
        except Exception as e:
            logger.error(f"Failed to fetch latest version: {e}")
            return None
    
    def is_update_available(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """Check if an update is available"""
        latest_version = self.get_latest_version()
        
        if not latest_version:
            return False, None, "Could not fetch latest version"
        
        try:
            current_ver = version.parse(self.current_version)
            latest_ver = version.parse(latest_version)
            
            if latest_ver > current_ver:
                return True, latest_version, f"Update available: {self.current_version} -> {latest_version}"
            elif latest_ver < current_ver:
                return False, latest_version, f"You are running a newer version: {self.current_version} > {latest_version}"
            else:
                return False, latest_version, f"You are running the latest version: {self.current_version}"
        except Exception as e:
            logger.error(f"Version comparison failed: {e}")
            return False, None, f"Version comparison failed: {e}"
    
    def update_system(self) -> Tuple[bool, str]:
        """Perform system update"""
        try:
            # Check if we're in a git repository
            if not os.path.exists(".git"):
                return False, "Not a git repository, cannot update automatically"
            
            # Fetch latest changes
            logger.info("Fetching latest changes from repository...")
            result = subprocess.run(["git", "fetch"], capture_output=True, text=True)
            if result.returncode != 0:
                return False, f"Git fetch failed: {result.stderr}"
            
            # Check if we're behind the remote
            result = subprocess.run(["git", "status", "--porcelain", "--branch"], capture_output=True, text=True)
            if result.returncode != 0:
                return False, f"Git status check failed: {result.stderr}"
            
            if "behind" not in result.stdout:
                return False, "Already up to date"
            
            # Pull latest changes
            logger.info("Pulling latest changes...")
            result = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True)
            if result.returncode != 0:
                return False, f"Git pull failed: {result.stderr}"
            
            # Upgrade dependencies
            logger.info("Upgrading dependencies...")
            result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"], 
                                    capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning(f"Dependency upgrade failed: {result.stderr}")
            
            return True, "Update completed successfully"
        except Exception as e:
            logger.error(f"Update failed: {e}")
            return False, f"Update failed: {e}"
    
    def get_system_info(self) -> Dict:
        """Get comprehensive system information"""
        try:
            # Get current version
            current_version = self.current_version
            
            # Check if update is available
            update_available, latest_version, update_msg = self.is_update_available()
            
            # Get git info
            git_branch = "unknown"
            git_commit = "unknown"
            try:
                result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], 
                                        capture_output=True, text=True)
                if result.returncode == 0:
                    git_branch = result.stdout.strip()
                
                result = subprocess.run(["git", "rev-parse", "--short", "HEAD"], 
                                        capture_output=True, text=True)
                if result.returncode == 0:
                    git_commit = result.stdout.strip()
            except:
                pass
            
            # Get system info
            import platform
            import psutil
            
            system_info = {
                "current_version": current_version,
                "latest_version": latest_version,
                "update_available": update_available,
                "update_message": update_msg,
                "git_branch": git_branch,
                "git_commit": git_commit,
                "system": platform.system(),
                "release": platform.release(),
                "architecture": platform.machine(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "disk_total_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
                "uptime_seconds": int(psutil.boot_time())
            }
            
            return system_info
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {"error": str(e)}


# Global version checker instance - initialized later
version_checker = None