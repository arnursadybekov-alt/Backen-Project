"""
Redis cache service.
Provides a simple async get/set/delete interface used by endpoints.
"""
import json
import logging
from typing import Any, Optional
 
import redis.asyncio as aioredis
 
from app.config import settings
 
logger = logging.getLogger(__name__)
 
# Module-level pool — initialised once on first use
_redis: Optional[aioredis.Redis] = None
 
 
async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis
 
 
async def cache_get(key: str) -> Optional[Any]:
    try:
        r = await get_redis()
        value = await r.get(key)
        if value is None:
            return None
        return json.loads(value)
    except Exception as exc:
        logger.warning("Redis GET failed for key=%s: %s", key, exc)
        return None
 
 
async def cache_set(key: str, value: Any, ttl: int = 60) -> None:
    try:
        r = await get_redis()
        await r.setex(key, ttl, json.dumps(value, ensure_ascii=False))
    except Exception as exc:
        logger.warning("Redis SET failed for key=%s: %s", key, exc)
 
 
async def cache_delete(key: str) -> None:
    try:
        r = await get_redis()
        await r.delete(key)
    except Exception as exc:
        logger.warning("Redis DELETE failed for key=%s: %s", key, exc)
 
 
async def cache_delete_pattern(pattern: str) -> None:
    """Delete all keys matching a glob pattern (e.g. 'leaderboard:*')."""
    try:
        r = await get_redis()
        keys = await r.keys(pattern)
        if keys:
            await r.delete(*keys)
    except Exception as exc:
        logger.warning("Redis DELETE pattern=%s failed: %s", pattern, exc)