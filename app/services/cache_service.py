# app/services/cache_service.py
import json
import logging
from typing import Any, Optional
import aioredis
from app.config import settings

logger = logging.getLogger(__name__)

redis = None


async def get_redis():
    global redis
    if redis is None:
        redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return redis


async def cache_set(key: str, value: Any, ttl: int = 300):
    """Сохранить в кэш с TTL (по умолчанию 5 минут)"""
    try:
        r = await get_redis()
        await r.set(key, json.dumps(value), ex=ttl)
    except Exception as e:
        logger.error(f"Cache set error: {e}")


async def cache_get(key: str) -> Optional[Any]:
    """Получить из кэша"""
    try:
        r = await get_redis()
        data = await r.get(key)
        return json.loads(data) if data else None
    except Exception as e:
        logger.error(f"Cache get error: {e}")
        return None


async def cache_delete_pattern(pattern: str):
    """Инвалидация по паттерну (например leaderboard:*)"""
    try:
        r = await get_redis()
        keys = await r.keys(pattern)
        if keys:
            await r.delete(*keys)
    except Exception as e:
        logger.error(f"Cache delete pattern error: {e}")