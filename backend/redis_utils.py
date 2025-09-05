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

def set_hash(key, mapping, expire_sec=None):
    """Set a hash in Redis and optionally set expiration."""
    r = get_redis()
    r.hset(key, mapping=mapping)
    if expire_sec:
        r.expire(key, expire_sec)

def get_hash(key):
    """Get a hash from Redis."""
    r = get_redis()
    return r.hgetall(key)

def push_list(key, value, expire_sec=None):
    """Push a value to a Redis list and optionally set expiration."""
    r = get_redis()
    r.lpush(key, value)
    if expire_sec:
        r.expire(key, expire_sec)

def get_list(key):
    """Get all values from a Redis list."""
    r = get_redis()
    return r.lrange(key, 0, -1)

def set_expire(key, expire_sec):
    """Set expiration for a key."""
    r = get_redis()
    r.expire(key, expire_sec)