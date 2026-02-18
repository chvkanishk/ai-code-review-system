import json
import redis
from .config import REDIS_URL

QUEUE_NAME = "code_review_jobs"

class RedisClient:
    def __init__(self):
        self.client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    def push_job(self, job: dict):
        """Push a job into the Redis queue."""
        self.client.lpush(QUEUE_NAME, json.dumps(job))

    def pop_job(self, block=True, timeout=5):
        """Pop a job from the queue (blocking)."""
        if block:
            result = self.client.brpop(QUEUE_NAME, timeout=timeout)
            if result is None:
                return None
            _, data = result
        else:
            data = self.client.rpop(QUEUE_NAME)
            if data is None:
                return None

        return json.loads(data)

redis_client = RedisClient()
