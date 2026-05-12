# app/services/gamification_service.py
from datetime import datetime, date, timezone
from typing import Optional, List
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import Child, Badge, BadgeType, Notification
from app.models.curriculum import ExerciseResult, DifficultyLevel
from app.config import settings
from app.services.cache_service import cache_delete_pattern

logger = logging.getLogger(__name__)


def calculate_level(xp: int) -> int:
    """Calculate child's level based on total XP"""
    return max(1, (xp // settings.XP_LEVEL_THRESHOLD) + 1)


def calculate_streak(last_activity: Optional[datetime], current_streak: int) -> int:
    """Calculate current learning streak"""
    if last_activity is None:
        return 1

    today = date.today()
    last_date = last_activity.date() if hasattr(last_activity, "date") else last_activity

    if last_date == today:
        return current_streak
    elif (today - last_date).days == 1:
        return current_streak + 1
    else:
        return 1


def is_streak_at_risk(last_activity: Optional[datetime]) -> bool:
    """Check if streak is at risk of breaking today"""
    if last_activity is None:
        return True
    last_date = last_activity.date() if hasattr(last_activity, "date") else last_activity
    return last_date < date.today()


BADGE_DESCRIPTIONS = {
    BadgeType.FIRST_LESSON: "Completed your first lesson!",
    BadgeType.XP_100: "Earned 100 XP points!",
    BadgeType.XP_500: "Earned 500 XP points!",
    BadgeType.STREAK_7: "7-day learning streak!",
    BadgeType.STREAK_30: "30-day learning streak!",
    BadgeType.UNIT_COMPLETE: "Completed a full unit!",
    BadgeType.PERFECT_LESSON: "Perfect score on a lesson!",
}


async def award_badges(
    child: Child,
    db: AsyncSession,
    lesson_completed: bool = False,
    perfect: bool = False,
) -> List[BadgeType]:
    """Award new badges if conditions are met"""
    result = await db.execute(
        select(Badge.badge_type).where(Badge.child_id == child.id)
    )
    existing = {row[0] for row in result.fetchall()}

    conditions = [
        (BadgeType.FIRST_LESSON, lesson_completed),
        (BadgeType.XP_100, child.xp >= 100),
        (BadgeType.XP_500, child.xp >= 500),
        (BadgeType.STREAK_7, child.streak >= 7),
        (BadgeType.STREAK_30, child.streak >= 30),
        (BadgeType.PERFECT_LESSON, perfect),
    ]

    new_badges: List[BadgeType] = []

    for badge_type, condition in conditions:
        if condition and badge_type not in existing:
            db.add(
                Badge(
                    child_id=child.id,
                    badge_type=badge_type,
                    description=BADGE_DESCRIPTIONS[badge_type],
                )
            )
            new_badges.append(badge_type)

    return new_badges


async def process_lesson_completion(
    child: Child, lesson_xp: int, score: float, db: AsyncSession
) -> dict:
    """Process lesson completion: XP, streak, level, badges + cache invalidation"""
    old_level = child.level

    bonus_xp = settings.STREAK_BONUS_XP if child.streak >= 3 else 0
    earned_xp = lesson_xp + bonus_xp
    child.xp += earned_xp

    new_streak = calculate_streak(child.last_activity_date, child.streak)
    streak_increased = new_streak > child.streak

    child.streak = new_streak
    child.last_activity_date = datetime.now(timezone.utc)
    child.level = calculate_level(child.xp)

    new_badges = await award_badges(
        child, db, lesson_completed=True, perfect=(score >= 1.0)
    )

    # Invalidate leaderboard cache
    try:
        await cache_delete_pattern("leaderboard:*")
    except Exception as e:
        logger.warning(f"Failed to invalidate leaderboard cache: {e}")

    return {
        "xp_earned": earned_xp,
        "bonus_xp": bonus_xp,
        "total_xp": child.xp,
        "level": child.level,
        "leveled_up": child.level > old_level,
        "streak": new_streak,
        "streak_increased": streak_increased,
        "new_badges": [b.value for b in new_badges],
    }


async def create_notification(
    parent_id: int,
    child_id: Optional[int],
    title: str,
    message: str,
    db: AsyncSession,
) -> Notification:
    """Create notification for parent"""
    notification = Notification(
        parent_id=parent_id,
        child_id=child_id,
        title=title,
        message=message,
    )
    db.add(notification)
    await db.flush()
    return notification