# app/services/leaderboard_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import Child
from app.services.cache_service import cache_get, cache_set


async def get_leaderboard(db: AsyncSession, age_min: int = 6, age_max: int = 12, limit: int = 20):
    """Полноценный лидерборд с кэшированием по возрастным группам"""
    cache_key = f"leaderboard:{age_min}:{age_max}:{limit}"

    # Проверка кэша
    cached = await cache_get(cache_key)
    if cached:
        return cached

    # Запрос к базе
    result = await db.execute(
        select(Child)
        .where(Child.age >= age_min, Child.age <= age_max)
        .order_by(Child.xp.desc(), Child.level.desc())
        .limit(limit)
    )
    children = result.scalars().all()

    leaderboard = []
    for rank, child in enumerate(children, 1):
        leaderboard.append({
            "rank": rank,
            "display_name": getattr(child, "display_name", None) or child.username,
            "xp": child.xp,
            "level": child.level,
            "streak": child.streak,
            "age": child.age
        })

    # Сохранение в кэш (5 минут)
    await cache_set(cache_key, leaderboard, ttl=300)
    return leaderboard