from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from loguru import logger
import asyncio
import heapq
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import threading
import time


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    """Task status states"""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class QueueTask:
    """Represents a task in the queue"""
    task_id: str
    task_type: str
    priority: TaskPriority
    payload: Dict[str, Any]
    created_at: datetime
    scheduled_at: datetime
    timeout: int = 300  # 5 minutes default
    retries: int = 0
    max_retries: int = 3
    assigned_worker: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING


class PriorityQueue:
    """Priority queue implementation for task management"""
    
    def __init__(self):
        self._heap = []
        self._tasks = {}  # task_id -> QueueTask
        self._lock = threading.Lock()
    
    def put(self, task: QueueTask):
        """Add a task to the queue"""
        with self._lock:
            # Priority queue: higher priority value goes first
            priority_value = -task.priority.value
            heapq.heappush(self._heap, (priority_value, task.created_at.timestamp(), task))
            self._tasks[task.task_id] = task
    
    def get(self) -> Optional[QueueTask]:
        """Get the highest priority task from the queue"""
        with self._lock:
            if not self._heap:
                return None
            
            priority, timestamp, task = heapq.heappop(self._heap)
            # Remove from tasks dict
            self._tasks.pop(task.task_id, None)
            return task
    
    def peek(self) -> Optional[QueueTask]:
        """Peek at the highest priority task without removing it"""
        with self._lock:
            if not self._heap:
                return None
            return self._heap[0][2]  # The task is at index 2
    
    def size(self) -> int:
        """Get the size of the queue"""
        with self._lock:
            return len(self._tasks)
    
    def get_task(self, task_id: str) -> Optional[QueueTask]:
        """Get a specific task by ID"""
        with self._lock:
            return self._tasks.get(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a specific task"""
        with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                task.status = TaskStatus.CANCELLED
                # Remove from heap if it's there
                self._tasks.pop(task_id)
                return True
            return False


class WorkerPool:
    """Worker pool for processing tasks"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_tasks = {}  # task_id -> future
        self.worker_stats = {}
        self._lock = threading.Lock()
    
    def submit_task(self, task: QueueTask, processor_func) -> bool:
        """Submit a task for processing"""
        with self._lock:
            if task.task_id in self.active_tasks:
                logger.warning(f"Task {task.task_id} already in progress")
                return False
            
            future = self.executor.submit(processor_func, task)
            self.active_tasks[task.task_id] = future
            task.status = TaskStatus.PROCESSING
            task.assigned_worker = f"worker_{threading.current_thread().ident}"
            
            # Track worker stats
            worker_id = task.assigned_worker
            if worker_id not in self.worker_stats:
                self.worker_stats[worker_id] = {"processed": 0, "failed": 0}
            
            return True
    
    def is_task_completed(self, task_id: str) -> bool:
        """Check if a task is completed"""
        with self._lock:
            if task_id not in self.active_tasks:
                return True  # Not in active tasks, might be completed
            future = self.active_tasks[task_id]
            return future.done()
    
    def get_result(self, task_id: str) -> Any:
        """Get result of a completed task"""
        with self._lock:
            if task_id not in self.active_tasks:
                return None
            future = self.active_tasks[task_id]
            if future.done():
                result = future.result()
                del self.active_tasks[task_id]
                return result
            return None
    
    def shutdown(self):
        """Shutdown the worker pool"""
        self.executor.shutdown(wait=True)


class QueueManager:
    """Main queue manager that coordinates tasks and workers"""
    
    def __init__(self, max_workers: int = 4):
        self.queue = PriorityQueue()
        self.worker_pool = WorkerPool(max_workers)
        self.running = True
        self.monitor_task = None
    
    def add_task(self, task: QueueTask) -> bool:
        """Add a task to the queue"""
        if not self.running:
            return False
        
        # Set task status to queued
        task.status = TaskStatus.QUEUED
        self.queue.put(task)
        logger.info(f"Task {task.task_id} added to queue with priority {task.priority.name}")
        return True
    
    def process_next_task(self, processor_func):
        """Process the next available task"""
        task = self.queue.get()
        if not task:
            return False
        
        return self.worker_pool.submit_task(task, processor_func)
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        stats = {
            "queue_size": self.queue.size(),
            "active_tasks": len(self.worker_pool.active_tasks),
            "worker_stats": self.worker_pool.worker_stats.copy(),
            "timestamp": datetime.now().isoformat()
        }
        return stats
    
    def start_monitoring(self):
        """Start monitoring queue performance"""
        async def monitor():
            while self.running:
                stats = self.get_queue_stats()
                logger.info(f"Queue Stats - Size: {stats['queue_size']}, Active: {stats['active_tasks']}")
                
                # Log if queue is getting too large
                if stats['queue_size'] > 50:
                    logger.warning(f"Queue is large: {stats['queue_size']} items")
                
                await asyncio.sleep(30)  # Check every 30 seconds
        
        self.monitor_task = asyncio.create_task(monitor())
    
    def stop(self):
        """Stop the queue manager"""
        self.running = False
        if self.monitor_task:
            self.monitor_task.cancel()
        self.worker_pool.shutdown()


class CDNManager:
    """CDN simulation for optimizing media delivery"""
    
    def __init__(self, regions: List[str] = None):
        self.regions = regions or ["us-east", "us-west", "eu-west", "asia-east"]
        self.cache_servers = {region: {} for region in self.regions}
        self.region_latencies = {region: {} for region in self.regions}
        self.global_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self._lock = threading.Lock()
    
    def get_closest_region(self, client_location: str) -> str:
        """Get the closest CDN region to the client"""
        # Simple heuristic - in real world this would use IP geolocation
        region_mapping = {
            "north_america": ["us-east", "us-west"],
            "europe": ["eu-west"],
            "asia": ["asia-east"],
            "default": ["us-east"]
        }
        
        for continent, regions in region_mapping.items():
            if continent in client_location.lower():
                return regions[0]
        
        return "us-east"  # Default
    
    def store_content(self, content_id: str, content: Any, region: str = None) -> bool:
        """Store content in CDN"""
        if region:
            self.cache_servers[region][content_id] = {
                "content": content,
                "timestamp": datetime.now(),
                "size": len(str(content)) if hasattr(content, '__len__') else len(str(content))
            }
            self.global_cache[content_id] = content
            logger.info(f"Content {content_id} stored in {region} CDN")
            return True
        else:
            # Store in all regions
            success = True
            for region in self.regions:
                try:
                    self.cache_servers[region][content_id] = {
                        "content": content,
                        "timestamp": datetime.now(),
                        "size": len(str(content)) if hasattr(content, '__len__') else len(str(content))
                    }
                except:
                    success = False
            self.global_cache[content_id] = content
            logger.info(f"Content {content_id} replicated across all CDN regions")
            return success
    
    def get_content(self, content_id: str, client_location: str = "default") -> Optional[Any]:
        """Get content from CDN"""
        with self._lock:
            closest_region = self.get_closest_region(client_location)
            
            # Try regional cache first
            if content_id in self.cache_servers[closest_region]:
                self.cache_hits += 1
                logger.info(f"Content {content_id} served from {closest_region} CDN (cache hit)")
                return self.cache_servers[closest_region][content_id]["content"]
            
            # Fallback to global cache
            if content_id in self.global_cache:
                self.cache_hits += 1
                logger.info(f"Content {content_id} served from global cache")
                return self.global_cache[content_id]
            
            # Cache miss
            self.cache_misses += 1
            logger.info(f"Content {content_id} not found in CDN (cache miss)")
            return None
    
    def invalidate_content(self, content_id: str):
        """Invalidate content in CDN"""
        with self._lock:
            for region in self.regions:
                if content_id in self.cache_servers[region]:
                    del self.cache_servers[region][content_id]
            
            if content_id in self.global_cache:
                del self.global_cache[content_id]
    
    def get_cdn_stats(self) -> Dict[str, Any]:
        """Get CDN statistics"""
        with self._lock:
            total_cached = sum(len(region_cache) for region_cache in self.cache_servers.values())
            cache_hit_ratio = self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
            
            return {
                "regions": self.regions,
                "total_cached_items": total_cached,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "cache_hit_ratio": round(cache_hit_ratio, 2),
                "global_cache_size": len(self.global_cache),
                "timestamp": datetime.now().isoformat()
            }
    
    def cleanup_old_content(self, max_age_hours: int = 24):
        """Clean up old content from CDN"""
        with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            cleaned_count = 0
            
            for region, cache in self.cache_servers.items():
                old_keys = [
                    key for key, value in cache.items() 
                    if value["timestamp"] < cutoff_time
                ]
                for key in old_keys:
                    del cache[key]
                    cleaned_count += 1
            
            logger.info(f"CDN cleanup completed: {cleaned_count} old items removed")


# Global instances
queue_manager = QueueManager(max_workers=4)
cdn_manager = CDNManager()