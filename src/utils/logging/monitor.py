import psutil
import time
import threading
from datetime import datetime
from typing import Dict, Any
from collections import defaultdict
import json
from pathlib import Path


class SystemMonitor:
    """System monitoring for LibraryDown"""
    
    def __init__(self):
        self.stats_history = defaultdict(list)
        self.monitoring = False
        self.monitor_thread = None
        self.stats_file = Path("data/system_stats.json")
        self.stats_file.parent.mkdir(exist_ok=True)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get current system statistics"""
        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "network_io": psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {},
            "process_count": len(psutil.pids()),
            "uptime_seconds": time.time() - psutil.boot_time()
        }
        
        # Add disk usage for specific directories
        for path in ['.', 'media/', 'logs/', 'data/']:
            if Path(path).exists():
                try:
                    path_stat = psutil.disk_usage(str(Path(path).resolve()))
                    stats[f'disk_usage_{path.replace("/", "_").strip("_")}'] = path_stat.percent
                except:
                    pass
        
        return stats
    
    def get_process_stats(self) -> Dict[str, Any]:
        """Get process-specific statistics for LibraryDown"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'cmdline']):
            try:
                if 'librarydown' in ' '.join(proc.info['cmdline']) or \
                   'celery' in proc.info['name'] or \
                   'uvicorn' in proc.info['name'] or \
                   'redis' in proc.info['name']:
                    processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return {"processes": processes}
    
    def get_app_stats(self) -> Dict[str, Any]:
        """Get application-specific statistics"""
        # Count files in media directory
        media_files = 0
        total_size = 0
        if Path('media').exists():
            for f in Path('media').rglob('*'):
                if f.is_file():
                    media_files += 1
                    total_size += f.stat().st_size
        
        # Count log files
        log_files = 0
        if Path('logs').exists():
            log_files = len([f for f in Path('logs').rglob('*') if f.is_file()])
        
        return {
            "media_files_count": media_files,
            "media_total_size_mb": round(total_size / (1024 * 1024), 2),
            "log_files_count": log_files
        }
    
    def collect_stats(self) -> Dict[str, Any]:
        """Collect all statistics"""
        all_stats = {}
        all_stats.update(self.get_system_stats())
        all_stats.update(self.get_process_stats())
        all_stats.update(self.get_app_stats())
        
        # Store in history
        self.stats_history['all'].append(all_stats)
        if len(self.stats_history['all']) > 100:  # Keep last 100 records
            self.stats_history['all'].pop(0)
        
        # Save to file
        self.save_stats_to_file(all_stats)
        
        return all_stats
    
    def save_stats_to_file(self, stats: Dict[str, Any]):
        """Save stats to JSON file"""
        try:
            if self.stats_file.exists():
                with open(self.stats_file, 'r') as f:
                    existing_data = json.load(f)
            else:
                existing_data = []
            
            existing_data.append(stats)
            
            # Keep only last 1000 records
            if len(existing_data) > 1000:
                existing_data = existing_data[-1000:]
            
            with open(self.stats_file, 'w') as f:
                json.dump(existing_data, f, indent=2)
        except Exception as e:
            print(f"Error saving stats to file: {e}")
    
    def start_monitoring(self, interval: int = 60):
        """Start continuous monitoring in background thread"""
        if self.monitoring:
            return
        
        self.monitoring = True
        
        def monitor_loop():
            while self.monitoring:
                try:
                    self.collect_stats()
                    time.sleep(interval)
                except Exception as e:
                    print(f"Error in monitoring loop: {e}")
                    time.sleep(interval)
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
    
    def get_historical_stats(self) -> Dict[str, Any]:
        """Get historical statistics"""
        try:
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        except:
            return []


# Global monitor instance
monitor = SystemMonitor()