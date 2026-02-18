"""
Redis client for message queue operations
"""
import json
import redis
import logging
from shared.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Simple Redis queue client"""
    
    def __init__(self):
        """Connect to Redis"""
        self.client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_timeout=5
        )
        self.queue_name = settings.REDIS_QUEUE_NAME
        logger.info(f"Redis connected: {settings.REDIS_HOST}")
    
    def push_job(self, job_data):
        """
        Push a job to the queue
        
        Args:
            job_data: Dictionary with job info
        
        Returns:
            True if successful
        """
        try:
            job_json = json.dumps(job_data)
            self.client.rpush(self.queue_name, job_json)
            logger.info(f"✅ Job queued: PR #{job_data.get('pr_number')}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to queue job: {e}")
            return False
    
    def pop_job(self, timeout=5):
        """
        Get a job from the queue (waits up to timeout seconds)
        
        Args:
            timeout: How long to wait for a job
        
        Returns:
            Job data dictionary or None
        """
        try:
            result = self.client.blpop(self.queue_name, timeout=timeout)
            if result:
                _, job_json = result
                job_data = json.loads(job_json)
                logger.info(f"📥 Job received: PR #{job_data.get('pr_number')}")
                return job_data
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get job: {e}")
            return None
    
    def get_queue_length(self):
        """Get how many jobs are waiting"""
        try:
            return self.client.llen(self.queue_name)
        except:
            return 0
    
    def health_check(self):
        """Check if Redis is working"""
        try:
            return self.client.ping()
        except:
            return False


# Global Redis client
redis_client = RedisClient()