from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from typing import List, Optional
from app.db.session import get_db
from app.models.user import Parent, Child, Notification, AuditLog
from app.models.curriculum import LessonProgress, Lesson, Unit
from app.core.dependencies import get_current_parent, get_current_admin
from app.schemas.schemas import (
    NotificationOut, NotificationMarkRead,
    LeaderboardEntry, AuditLogOut, AdminStats,
    ParentOut, ParentUpdate, ChildOut, PaginatedResponse,
)

# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
from app.services.cache_service import cache_get, cache_set
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←

parents_router = APIRouter(prefix="/parents", tags=["Parents"])
notifications_router = APIRouter(prefix="/notifications", tags=["Notifications"])
leaderboard_router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])
admin_router = APIRouter(prefix="/admin", tags=["Admin"])


# ── Parents, Notifications, Admin (оставляем как есть) ───────────────────────
# ... (весь код до Leaderboard без изменений) ...


# ── Leaderboard ───────────────────────────────────────────────────────────────

@leaderboard_router.get("", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    age_min: int = Query(3, ge=3, le=12),
    age_max: int = Query(12, ge=3, le=12),
    limit: int = Query(20, ge=1, le=100),
    current_user: Parent = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Redis-cached leaderboard by age group"""
    cache_key = f"leaderboard:{age_min}:{age_max}:{limit}"

    # Проверка кэша
    cached = await cache_get(cache_key)
    if cached:
        return cached

    # Если нет в кэше — из базы
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

    # Сохраняем в Redis
    await cache_set(cache_key, [e.model_dump() for e in entries], ttl=60)

    return entries


# ── Admin (оставляем как есть) ───────────────────────────────────────────────
# ... остальной код файла ...