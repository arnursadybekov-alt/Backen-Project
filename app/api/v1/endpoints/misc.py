from app.core.redis import get_cached_leaderboard, set_cached_leaderboard, invalidate_leaderboard

@leaderboard_router.get("", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    age_min: int = Query(3, ge=3, le=12),
    age_max: int = Query(12, ge=3, le=12),
    limit: int = Query(20, ge=1, le=100),
    current_user: Parent = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    cached = await get_cached_leaderboard(age_min, age_max, limit)
    if cached:
        return cached

    result = await db.execute(
        select(Child)
        .where(Child.age >= age_min, Child.age <= age_max)
        .order_by(Child.xp.desc())
        .limit(limit)
    )
    children = result.scalars().all()

    entries = []
    for rank, child in enumerate(children, 1):
        age_group = "3-6" if child.age <= 6 else "7-9" if child.age <= 9 else "10-12"
        entries.append(LeaderboardEntry(
            rank=rank,
            display_name=child.display_name,
            xp=child.xp,
            level=child.level,
            streak=child.streak,
            age_group=age_group
        ))

    await set_cached_leaderboard(age_min, age_max, limit, [e.model_dump() for e in entries])
    return entries