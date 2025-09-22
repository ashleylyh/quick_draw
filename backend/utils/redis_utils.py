import redis
import os
from config import REDIS_HOST, REDIS_PORT, REDIS_DB

_redis_client = None

def get_redis():
    """Get or create a Redis client (singleton)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )
    return _redis_client
