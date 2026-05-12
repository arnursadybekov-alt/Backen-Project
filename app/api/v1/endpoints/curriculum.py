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
    create_unit,
    update_unit,
    create_lesson,
    update_lesson,
    create_exercise,
    update_exercise,
)
from app.services.cache_headers import generate_etag, add_cache_headers
from app.services.audit_service import create_audit_log
from app.core.dependencies import get_current_admin, get_current_parent

router = APIRouter(prefix="/curriculum", tags=["Curriculum"])


# ====================== PUBLIC ENDPOINTS (Offline-ready) ======================

@router.get("/units")
async def list_units(db: AsyncSession = Depends(get_db)):
    return await get_all_units(db)


@router.get("/units/{unit_id}")
async def get_unit(unit_id: int, db: AsyncSession = Depends(get_db)):
    unit = await get_unit_by_id(db, unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    return unit


@router.get("/units/{unit_id}/lessons")
async def list_lessons_by_unit(unit_id: int, db: AsyncSession = Depends(get_db)):
    return await get_lessons_by_unit(db, unit_id)


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

    etag_data = {
        "id": lesson.id,
        "title": lesson.title,
        "content": lesson.content,
        "updated_at": str(lesson.updated_at) if hasattr(lesson, "updated_at") else None,
    }
    etag = generate_etag(etag_data)

    if if_none_match and if_none_match.strip('"') == etag:
        response.status_code = 304
        return None

    add_cache_headers(response, etag, max_age=7200)
    return lesson


@router.get("/lessons/{lesson_id}/exercises")
async def list_exercises(lesson_id: int, db: AsyncSession = Depends(get_db)):
    return await get_exercises_by_lesson(db, lesson_id)


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
        "options": getattr(exercise, "options", None),
        "updated_at": str(exercise.updated_at) if hasattr(exercise, "updated_at") else None,
    }
    etag = generate_etag(etag_data)

    if if_none_match and if_none_match.strip('"') == etag:
        response.status_code = 304
        return None

    add_cache_headers(response, etag, max_age=3600)
    return exercise


# ====================== ADMIN ENDPOINTS (с Audit Logging) ======================

@router.post("/units")
async def admin_create_unit(
    unit_data: dict,  # Замени на свою Pydantic схему, если есть
    current_admin=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    new_unit = await create_unit(db, unit_data)

    await create_audit_log(
        db=db,
        admin_id=current_admin.id,
        action="CREATE",
        entity_type="Unit",
        entity_id=new_unit.id,
        before=None,
        after=new_unit.__dict__ if hasattr(new_unit, "__dict__") else None,
    )
    return new_unit


@router.put("/units/{unit_id}")
async def admin_update_unit(
    unit_id: int,
    unit_data: dict,
    current_admin=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    old_unit = await get_unit_by_id(db, unit_id)
    before = old_unit.__dict__.copy() if old_unit else None

    updated_unit = await update_unit(db, unit_id, unit_data)

    await create_audit_log(
        db=db,
        admin_id=current_admin.id,
        action="UPDATE",
        entity_type="Unit",
        entity_id=unit_id,
        before=before,
        after=updated_unit.__dict__ if hasattr(updated_unit, "__dict__") else None,
    )
    return updated_unit


@router.post("/lessons")
async def admin_create_lesson(
    lesson_data: dict,
    current_admin=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    new_lesson = await create_lesson(db, lesson_data)

    await create_audit_log(
        db=db,
        admin_id=current_admin.id,
        action="CREATE",
        entity_type="Lesson",
        entity_id=new_lesson.id,
        before=None,
        after=new_lesson.__dict__ if hasattr(new_lesson, "__dict__") else None,
    )
    return new_lesson


@router.put("/lessons/{lesson_id}")
async def admin_update_lesson(
    lesson_id: int,
    lesson_data: dict,
    current_admin=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    old_lesson = await get_lesson_by_id(db, lesson_id)
    before = old_lesson.__dict__.copy() if old_lesson else None

    updated_lesson = await update_lesson(db, lesson_id, lesson_data)

    await create_audit_log(
        db=db,
        admin_id=current_admin.id,
        action="UPDATE",
        entity_type="Lesson",
        entity_id=lesson_id,
        before=before,
        after=updated_lesson.__dict__ if hasattr(updated_lesson, "__dict__") else None,
    )
    return updated_lesson