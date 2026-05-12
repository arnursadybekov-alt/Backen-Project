# app/api/v1/endpoints/curriculum.py
from fastapi import APIRouter, Depends, HTTPException, Response, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_db
from app.services.curriculum_service import (
    get_all_units,
    get_unit_by_id,
    get_lessons_by_unit,
    get_lesson_by_id,
    get_exercises_by_lesson,
    get_exercise_by_id,
)
from app.services.cache_headers import generate_etag, add_cache_headers
from app.core.dependencies import get_current_user, get_current_admin

router = APIRouter(prefix="/curriculum", tags=["Curriculum"])


@router.get("/units")
async def list_units(db: AsyncSession = Depends(get_db)):
    units = await get_all_units(db)
    return units


@router.get("/units/{unit_id}")
async def get_unit(unit_id: int, db: AsyncSession = Depends(get_db)):
    unit = await get_unit_by_id(db, unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    return unit


@router.get("/units/{unit_id}/lessons")
async def list_lessons(unit_id: int, db: AsyncSession = Depends(get_db)):
    lessons = await get_lessons_by_unit(db, unit_id)
    return lessons


# ==================== OFFLINE-READY ENDPOINTS ====================

@router.get("/lessons/{lesson_id}")
async def get_lesson(
    lesson_id: int,
    response: Response,
    if_none_match: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    lesson = await get_lesson_by_id(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Генерация ETag
    etag_data = {
        "id": lesson.id,
        "title": lesson.title,
        "content": lesson.content,
        "updated_at": str(lesson.updated_at) if lesson.updated_at else None,
    }
    etag = generate_etag(etag_data)

    # Проверка If-None-Match (304 Not Modified)
    if if_none_match and if_none_match.strip('"') == etag:
        response.status_code = 304
        return None

    add_cache_headers(response, etag, max_age=7200)  # 2 часа
    return lesson


@router.get("/exercises/{exercise_id}")
async def get_exercise(
    exercise_id: int,
    response: Response,
    if_none_match: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    exercise = await get_exercise_by_id(db, exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    etag_data = {
        "id": exercise.id,
        "question": exercise.question,
        "options": exercise.options,
        "correct_answer": exercise.correct_answer,
        "updated_at": str(exercise.updated_at) if exercise.updated_at else None,
    }
    etag = generate_etag(etag_data)

    if if_none_match and if_none_match.strip('"') == etag:
        response.status_code = 304
        return None

    add_cache_headers(response, etag, max_age=3600)  # 1 час
    return exercise


@router.get("/lessons/{lesson_id}/exercises")
async def list_exercises(lesson_id: int, db: AsyncSession = Depends(get_db)):
    exercises = await get_exercises_by_lesson(db, lesson_id)
    return exercises


# Admin endpoints (без агрессивного кэширования)
@router.post("/units")
async def create_unit(...):  # оставь как было
    ...