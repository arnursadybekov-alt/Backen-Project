from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import Response
from typing import Optional, List
from app.db.session import get_db
from app.models.curriculum import Unit, Lesson, Exercise, DifficultyLevel
from app.models.user import Parent
from app.core.dependencies import get_current_parent, get_current_admin
from app.services.audit_service import log_action
from app.schemas.schemas import (
    UnitCreate, UnitUpdate, UnitOut,
    LessonCreate, LessonUpdate, LessonOut,
    ExerciseCreate, ExerciseUpdate, ExerciseOut,
    PaginatedResponse,
)

units_router = APIRouter(prefix="/units", tags=["Units"])
lessons_router = APIRouter(prefix="/lessons", tags=["Lessons"])
exercises_router = APIRouter(prefix="/exercises", tags=["Exercises"])


# ── Units ──────────────────────────────────────────────────────────────────────
# ... (оставляем без изменений) ...


# ── Lessons ────────────────────────────────────────────────────────────────────

@lessons_router.get("/{lesson_id}", response_model=LessonOut)
async def get_lesson(
    lesson_id: int,
    response: Response,                    # ← Добавь
    current_user: Parent = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail={"message": "Lesson not found"})

    # Offline caching headers
    response.headers["ETag"] = f'"lesson-{lesson.id}-{lesson.updated_at.isoformat()}"'
    response.headers["Cache-Control"] = "public, max-age=3600"

    return lesson

# ── Exercises ──────────────────────────────────────────────────────────────────

@exercises_router.get("/{exercise_id}", response_model=ExerciseOut)
async def get_exercise(
    exercise_id: int,
    response: Response,                    # ← Для Cache headers
    current_user: Parent = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail={"message": "Exercise not found"})

    # Offline-ready Content API (бонус)
    response.headers["ETag"] = f'"exercise-{exercise.id}-{exercise.updated_at.isoformat()}"'
    response.headers["Cache-Control"] = "public, max-age=3600"

    return exercise


# Остальной код файла оставляем как есть
@units_router.get("")
# ... (весь остальной код без изменений) ...