import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.gamification_service import (
    calculate_level,
    calculate_streak,
    is_streak_at_risk,
    process_lesson_completion,
    award_badges,
)
from app.models.user import Child, Badge, BadgeType


def make_child(**kwargs):
    child = Child()
    child.id = kwargs.get("id", 1)
    child.xp = kwargs.get("xp", 0)
    child.level = kwargs.get("level", 1)
    child.streak = kwargs.get("streak", 0)
    child.last_activity_date = kwargs.get("last_activity_date", None)
    child.lesson_progress = kwargs.get("lesson_progress", [])
    return child


# ── calculate_level ───────────────────────────────────────────────────────────

def test_calculate_level_zero_xp():
    assert calculate_level(0) == 1

def test_calculate_level_threshold():
    assert calculate_level(200) == 2

def test_calculate_level_mid():
    assert calculate_level(150) == 1

def test_calculate_level_high():
    assert calculate_level(600) == 4

def test_calculate_level_negative():
    assert calculate_level(-10) == 1


# ── calculate_streak ──────────────────────────────────────────────────────────

def test_streak_no_activity():
    result = calculate_streak(None, 0)
    assert result == 1

def test_streak_consecutive_day():
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    result = calculate_streak(yesterday, 5)
    assert result == 6

def test_streak_same_day():
    today = datetime.now(timezone.utc)
    result = calculate_streak(today, 3)
    assert result == 3  # no change

def test_streak_broken():
    three_days_ago = datetime.now(timezone.utc) - timedelta(days=3)
    result = calculate_streak(three_days_ago, 10)
    assert result == 1  # reset


# ── is_streak_at_risk ─────────────────────────────────────────────────────────

def test_streak_at_risk_no_activity():
    assert is_streak_at_risk(None) is True

def test_streak_at_risk_yesterday():
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    assert is_streak_at_risk(yesterday) is True

def test_streak_not_at_risk_today():
    today = datetime.now(timezone.utc)
    assert is_streak_at_risk(today) is False


# ── process_lesson_completion ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_process_lesson_xp_awarded():
    child = make_child(xp=0, level=1, streak=0)
    db = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock(fetchall=MagicMock(return_value=[])))
    result = await process_lesson_completion(child, 50, 1.0, db)
    assert result["xp_earned"] == 50
    assert child.xp == 50

@pytest.mark.asyncio
async def test_process_lesson_streak_bonus():
    # streak >= 3 gives bonus XP
    child = make_child(xp=100, streak=5, last_activity_date=datetime.now(timezone.utc) - timedelta(days=1))
    db = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock(fetchall=MagicMock(return_value=[])))
    result = await process_lesson_completion(child, 50, 1.0, db)
    assert result["bonus_xp"] == 10
    assert result["xp_earned"] == 60

@pytest.mark.asyncio
async def test_process_lesson_level_up():
    child = make_child(xp=190, level=1, streak=0)
    db = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock(fetchall=MagicMock(return_value=[])))
    result = await process_lesson_completion(child, 50, 0.5, db)
    assert result["leveled_up"] is True
    assert result["level"] == 2

@pytest.mark.asyncio
async def test_process_lesson_no_level_up():
    child = make_child(xp=50, level=1, streak=0)
    db = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock(fetchall=MagicMock(return_value=[])))
    result = await process_lesson_completion(child, 50, 0.5, db)
    assert result["leveled_up"] is False

@pytest.mark.asyncio
async def test_process_lesson_streak_update():
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    child = make_child(xp=0, streak=3, last_activity_date=yesterday)
    db = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock(fetchall=MagicMock(return_value=[])))
    result = await process_lesson_completion(child, 50, 1.0, db)
    assert result["streak"] == 4
    assert result["streak_increased"] is True
