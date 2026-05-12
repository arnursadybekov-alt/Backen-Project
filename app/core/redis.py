import json
import asyncio
from redis.asyncio import Redis
from app.config import settings

redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)

async def get_cached_leaderboard(age_min: int, age_max: int, limit: int = 20):
    key = f"leaderboard:{age_min}-{age_max}:{limit}"
    cached = await redis.get(key)
    if cached:
        return json.loads(cached)
    return None

async def set_cached_leaderboard(age_min: int, age_max: int, limit: int, data: list, ttl: int = None):
    key = f"leaderboard:{age_min}-{age_max}:{limit}"
    await redis.setex(
        key,
        ttl or settings.LEADERBOARD_CACHE_TTL,
        json.dumps(data, default=str)
    )

async def invalidate_leaderboard(age_group: str = None):
    """Инвалидация при обновлении прогресса"""
    # Простая стратегия — инвалидируем все лидерборды
    await redis.flushdb()  # или pattern delete, если много