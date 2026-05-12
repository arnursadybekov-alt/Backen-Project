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

parents_router = APIRouter(prefix="/parents", tags=["Parents"])
notifications_router = APIRouter(prefix="/notifications", tags=["Notifications"])
leaderboard_router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])
admin_router = APIRouter(prefix="/admin", tags=["Admin"])


# ── Parents ────────────────────────────────────────────────────────────────────

@parents_router.get("/{parent_id}", response_model=ParentOut)
async def get_parent(parent_id: int, current_user: Parent = Depends(get_current_parent), db: AsyncSession = Depends(get_db)):
    if current_user.id != parent_id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail={"message": "Forbidden"})
    result = await db.execute(select(Parent).where(Parent.id == parent_id))
    parent = result.scalar_one_or_none()
    if not parent:
        raise HTTPException(status_code=404, detail={"message": "Parent not found"})
    return parent


@parents_router.put("/{parent_id}", response_model=ParentOut)
async def update_parent(parent_id: int, data: ParentUpdate, current_user: Parent = Depends(get_current_parent), db: AsyncSession = Depends(get_db)):
    if current_user.id != parent_id:
        raise HTTPException(status_code=403, detail={"message": "Forbidden"})
    result = await db.execute(select(Parent).where(Parent.id == parent_id))
    parent = result.scalar_one_or_none()
    if not parent:
        raise HTTPException(status_code=404, detail={"message": "Parent not found"})
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(parent, field, value)
    await db.flush()
    await db.refresh(parent)
    return parent


@parents_router.get("/{parent_id}/children", response_model=List[ChildOut])
async def get_parent_children(parent_id: int, current_user: Parent = Depends(get_current_parent), db: AsyncSession = Depends(get_db)):
    if current_user.id != parent_id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail={"message": "Forbidden"})
    result = await db.execute(select(Child).where(Child.parent_id == parent_id))
    return result.scalars().all()


# ── Notifications ─────────────────────────────────────────────────────────────

@notifications_router.get("", response_model=PaginatedResponse)
async def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = False,
    current_user: Parent = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    query = select(Notification).where(Notification.parent_id == current_user.id)
    if unread_only:
        query = query.where(Notification.is_read == False)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    result = await db.execute(query.order_by(Notification.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
    return PaginatedResponse(
        total=total, page=page, page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
        items=[NotificationOut.model_validate(n) for n in result.scalars().all()],
    )


@notifications_router.patch("", response_model=dict)
async def mark_notifications_read(data: NotificationMarkRead, current_user: Parent = Depends(get_current_parent), db: AsyncSession = Depends(get_db)):
    await db.execute(
        update(Notification)
        .where(Notification.id.in_(data.notification_ids), Notification.parent_id == current_user.id)
        .values(is_read=True)
    )
    return {"message": f"Marked {len(data.notification_ids)} notifications as read"}


# ── Leaderboard ───────────────────────────────────────────────────────────────

@leaderboard_router.get("", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    age_min: int = Query(3, ge=3, le=12),
    age_max: int = Query(12, ge=3, le=12),
    limit: int = Query(20, ge=1, le=100),
    current_user: Parent = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Child).where(Child.age >= age_min, Child.age <= age_max).order_by(Child.xp.desc()).limit(limit)
    )
    children = result.scalars().all()
    entries = []
    for rank, child in enumerate(children, 1):
        age_group = "ages 3-6" if child.age <= 6 else "ages 7-9" if child.age <= 9 else "ages 10-12"
        entries.append(LeaderboardEntry(rank=rank, display_name=child.display_name, xp=child.xp, level=child.level, streak=child.streak, age_group=age_group))
    return entries


# ── Admin ──────────────────────────────────────────────────────────────────────

@admin_router.get("/stats", response_model=AdminStats)
async def get_stats(admin: Parent = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    from datetime import date
    today = date.today()
    total_parents = (await db.execute(select(func.count()).select_from(Parent))).scalar()
    total_children = (await db.execute(select(func.count()).select_from(Child))).scalar()
    total_lessons = (await db.execute(select(func.count()).select_from(Lesson))).scalar()
    total_units = (await db.execute(select(func.count()).select_from(Unit))).scalar()
    total_xp = (await db.execute(select(func.sum(Child.xp)))).scalar() or 0
    total_completions = (await db.execute(select(func.count()).select_from(LessonProgress).where(LessonProgress.is_completed == True))).scalar()
    active_today = (await db.execute(select(func.count()).select_from(Child).where(func.date(Child.last_activity_date) == today))).scalar()
    return AdminStats(
        total_parents=total_parents, total_children=total_children,
        total_lessons=total_lessons, total_units=total_units,
        active_children_today=active_today, total_xp_awarded=total_xp,
        total_lesson_completions=total_completions,
    )


@admin_router.get("/logs", response_model=PaginatedResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    resource_type: Optional[str] = None,
    admin: Parent = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(AuditLog)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    result = await db.execute(query.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
    return PaginatedResponse(
        total=total, page=page, page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
        items=[AuditLogOut.model_validate(l) for l in result.scalars().all()],
    )
