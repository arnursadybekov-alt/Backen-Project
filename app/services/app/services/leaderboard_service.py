# app/services/leaderboard_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import Child
from app.services.cache_service import cache_get, cache_set


async def get_leaderboard(db: AsyncSession, age_min: int = 6, age_max: int = 12, limit: int = 20):
    cache_key = f"leaderboard:{age_min}:{age_max}:{limit}"

    cached = await cache_get(cache_key)
    if cached:
        return cached

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
            "display_name": child.display_name or child.username,
            "xp": child.xp,
            "level": child.level,
            "streak": child.streak,
            "age": child.age
        })

    await cache_set(cache_key, leaderboard, ttl=300)
    return leaderboard