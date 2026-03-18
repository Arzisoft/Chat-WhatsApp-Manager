"""
Rate limiter and job queue for handling Gemini API rate limits.
Prevents 429 errors and provides graceful degradation.
"""

import asyncio
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from enum import Enum

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    RETRYING = "retrying"

class RateLimiter:
    """Simple token bucket rate limiter"""
    
    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        """
        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: List[float] = []
    
    def is_allowed(self) -> bool:
        """Check if request is allowed"""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Remove old requests outside window
        self.requests = [t for t in self.requests if t > window_start]
        
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        
        return False
    
    def get_retry_after(self) -> int:
        """Get seconds until next request allowed"""
        if not self.requests:
            return 0
        
        oldest = min(self.requests)
        retry_at = oldest + self.window_seconds
        return max(0, int(retry_at - time.time()) + 1)
    
    def get_usage(self) -> Dict[str, Any]:
        """Get rate limit usage info"""
        now = time.time()
        window_start = now - self.window_seconds
        active_requests = len([t for t in self.requests if t > window_start])
        
        return {
            "active_requests": active_requests,
            "limit": self.max_requests,
            "remaining": max(0, self.max_requests - active_requests),
            "window_seconds": self.window_seconds,
            "reset_in_seconds": self.get_retry_after(),
        }

class ExtractionJob:
    """Represents a single extraction job"""
    
    def __init__(self, job_id: str, chat_id: int, text: str, priority: str = "normal"):
        self.job_id = job_id
        self.chat_id = chat_id
        self.text = text
        self.priority = priority
        self.status = JobStatus.QUEUED
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.retries = 0
        self.max_retries = 3
        self.result: Optional[Dict] = None
        self.error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "chat_id": self.chat_id,
            "status": self.status.value,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "error": self.error,
        }

class ExtractionQueue:
    """Job queue for managing extraction tasks"""
    
    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.queue: List[ExtractionJob] = []
        self.active_jobs: Dict[str, ExtractionJob] = {}
        self.completed_jobs: Dict[str, ExtractionJob] = {}
        self.rate_limiter = RateLimiter(max_requests, window_seconds)
        self.counter = 0
    
    def add_job(self, chat_id: int, text: str, priority: str = "normal") -> str:
        """Add job to queue"""
        self.counter += 1
        job_id = f"job_{chat_id}_{self.counter}_{int(time.time() * 1000)}"
        
        job = ExtractionJob(job_id, chat_id, text, priority)
        self.queue.append(job)
        self.active_jobs[job_id] = job
        
        # Sort by priority
        priority_order = {"high": 0, "normal": 1, "low": 2}
        self.queue.sort(
            key=lambda x: (priority_order.get(x.priority, 1), x.created_at)
        )
        
        logger.info(f"Job {job_id} added to queue (priority: {priority})")
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a job"""
        if job_id in self.active_jobs:
            return self.active_jobs[job_id].to_dict()
        if job_id in self.completed_jobs:
            return self.completed_jobs[job_id].to_dict()
        return None
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get overall queue status"""
        return {
            "queue_length": len(self.queue),
            "active_jobs": len(self.active_jobs),
            "completed_jobs": len(self.completed_jobs),
            "rate_limit": self.rate_limiter.get_usage(),
        }
    
    async def process_queue(
        self,
        extraction_func: Callable[[str], Dict[str, Any]]
    ) -> None:
        """Process queue with rate limiting"""
        while self.queue:
            job = self.queue.pop(0)
            
            # Check rate limit
            if not self.rate_limiter.is_allowed():
                retry_after = self.rate_limiter.get_retry_after()
                job.status = JobStatus.RATE_LIMITED
                self.queue.insert(0, job)
                
                logger.warning(
                    f"Rate limited, job {job.job_id} requeued. "
                    f"Retry in {retry_after}s"
                )
                await asyncio.sleep(retry_after)
                continue
            
            # Process job
            await self._process_job(job, extraction_func)
    
    async def _process_job(
        self,
        job: ExtractionJob,
        extraction_func: Callable[[str], Dict[str, Any]]
    ) -> None:
        """Process a single job with retry logic"""
        try:
            job.status = JobStatus.PROCESSING
            job.started_at = datetime.now()
            
            logger.info(f"Processing job {job.job_id}")
            result = extraction_func(job.text)
            
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            job.result = result
            
            self.active_jobs.pop(job.job_id, None)
            self.completed_jobs[job.job_id] = job
            
            logger.info(f"Job {job.job_id} completed successfully")
        
        except Exception as e:
            error_msg = str(e)
            job.retries += 1
            
            if job.retries < job.max_retries:
                # Calculate exponential backoff
                wait_time = min(2 ** job.retries, 30)  # Cap at 30 seconds
                
                job.status = JobStatus.RETRYING
                self.queue.append(job)
                
                logger.warning(
                    f"Job {job.job_id} failed: {error_msg}. "
                    f"Retrying in {wait_time}s (attempt {job.retries}/{job.max_retries})"
                )
                await asyncio.sleep(wait_time)
            else:
                job.status = JobStatus.FAILED
                job.error = error_msg
                job.completed_at = datetime.now()
                
                self.active_jobs.pop(job.job_id, None)
                self.completed_jobs[job.job_id] = job
                
                logger.error(f"Job {job.job_id} failed after {job.max_retries} retries: {error_msg}")
    
    def get_completed_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get result of completed job"""
        if job_id in self.completed_jobs:
            job = self.completed_jobs[job_id]
            if job.status == JobStatus.COMPLETED:
                return job.result
        return None
    
    def clear_completed(self, older_than_seconds: int = 3600) -> int:
        """Clear completed jobs older than specified time"""
        cutoff_time = datetime.now() - timedelta(seconds=older_than_seconds)
        jobs_to_delete = [
            job_id for job_id, job in self.completed_jobs.items()
            if job.completed_at and job.completed_at < cutoff_time
        ]
        
        for job_id in jobs_to_delete:
            del self.completed_jobs[job_id]
        
        logger.info(f"Cleared {len(jobs_to_delete)} completed jobs")
        return len(jobs_to_delete)

# Global queue instance
extraction_queue = ExtractionQueue(max_requests=30, window_seconds=60)

def safe_extract_with_queue(
    chat_id: int,
    text: str,
    extraction_func: Callable[[str], Dict[str, Any]],
    priority: str = "normal"
) -> str:
    """
    Safely extract data using queue system
    
    Args:
        chat_id: Chat ID
        text: Text to extract from
        extraction_func: Function that performs extraction
        priority: Job priority (high, normal, low)
    
    Returns:
        Job ID for tracking
    """
    job_id = extraction_queue.add_job(chat_id, text, priority)
    
    # Note: Actual processing happens in async context
    # This is a convenience wrapper for synchronous code
    
    return job_id
