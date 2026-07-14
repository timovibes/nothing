"""
single shared Redis client (talks to Memurai on Windows) used for caching,
rate limiting, and as the Celery broker."""
import redis

from app.core.config import settings

redis_client = redis.Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)


def get_redis() -> redis.Redis:
    return redis_client