import redis
import os
from env_config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD

_redis_client = None

def get_redis():
    """Get or create a Redis client (singleton)."""
    global _redis_client
    if _redis_client is None:
        # Use environment variables if available (for Docker), otherwise use config
        redis_host = os.getenv('REDIS_HOST', REDIS_HOST)
        redis_port = int(os.getenv('REDIS_PORT', REDIS_PORT))
        redis_db = int(os.getenv('REDIS_DB', REDIS_DB))
        redis_password = os.getenv('REDIS_PASSWORD', REDIS_PASSWORD)
        
        _redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password if redis_password else None,
            decode_responses=True
        )
    return _redis_client
