# app/api/v1/endpoints/misc.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.core.dependencies import get_current_parent
from app.schemas.schemas import LeaderboardEntry, NotificationOut
from app.services.leaderboard_service import get_leaderboard

# ====================== ROUTERS ======================
router = APIRouter(prefix="/misc", tags=["Misc"])
leaderboard_router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])


# ====================== LEADERBOARD ======================
@leaderboard_router.get("", response_model=List[LeaderboardEntry])
@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_global_leaderboard(
    age_min: int = Query(6, ge=3, le=15),
    age_max: int = Query(12, ge=3, le=15),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_parent),
):
    """
    Redis-cached leaderboard by age group
    Доступен по двум путям:
    - /leaderboard
    - /misc/leaderboard
    """
    return await get_leaderboard(
        db=db,
        age_min=age_min,
        age_max=age_max,
        limit=limit
    )


# ====================== NOTIFICATIONS ======================
@router.get("/notifications", response_model=List[NotificationOut])
async def get_notifications(
    current_user=Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
):
    # Твой существующий код получения уведомлений
    # ... (оставь свою реализацию)
    pass


# ====================== OTHER ENDPOINTS ======================
# Добавляй сюда остальные эндпоинты (admin stats и т.д.)
