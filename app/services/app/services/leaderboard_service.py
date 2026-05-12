# app/services/leaderboard_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.user import Child
from app.services.cache_service import cache_get, cache_set, cache_delete_pattern


async def get_leaderboard(db: AsyncSession, age_min: int = 5, age_max: int = 12, limit: int = 20):
    """
    Получить лидерборд по возрастной группе с кэшированием
    """
    cache_key = f"leaderboard:{age_min}:{age_max}:{limit}"

    # Пытаемся взять из кэша
    cached = await cache_get(cache_key)
    if cached:
        return cached

    # Если нет в кэше — считаем из БД
    query = (
        select(
            Child.id,
            Child.username,
            Child.xp,
            Child.level,
            Child.streak,
            Child.age
        )
        .where(Child.age.between(age_min, age_max))
        .order_by(Child.xp.desc(), Child.level.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    leaderboard = [dict(row._mapping) for row in result]

    # Сохраняем в кэш на 5 минут
    await cache_set(cache_key, leaderboard, ttl=300)

    return leaderboard