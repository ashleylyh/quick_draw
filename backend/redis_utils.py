import redis
import os

_redis_client = None

def get_redis():
    """Get or create a Redis client (singleton)."""
    global _redis_client
    if _redis_client is None:
        # You can configure host/port/db via environment variables if needed
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_db = int(os.getenv("REDIS_DB", "0"))
        _redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
    return _redis_client
