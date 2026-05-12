from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
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

@units_router.get("", response_model=PaginatedResponse)
async def list_units(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_published: Optional[bool] = None,
    difficulty: Optional[DifficultyLevel] = None,
    current_user: Parent = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    query = select(Unit)
    if is_published is not None:
        query = query.where(Unit.is_published == is_published)
    if difficulty:
        query = query.where(Unit.difficulty == difficulty)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    result = await db.execute(query.order_by(Unit.order_index).offset((page - 1) * page_size).limit(page_size))
    return PaginatedResponse(
        total=total, page=page, page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
        items=[UnitOut.model_validate(u) for u in result.scalars().all()],
    )


@units_router.post("", response_model=UnitOut, status_code=status.HTTP_201_CREATED)
async def create_unit(data: UnitCreate, admin: Parent = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    unit = Unit(**data.model_dump())
    db.add(unit)
    await db.flush()
    await db.refresh(unit)
    await log_action(db, admin, "create", "unit", unit.id, {"title": unit.title})
    return unit


@units_router.get("/{unit_id}", response_model=UnitOut)
async def get_unit(unit_id: int, current_user: Parent = Depends(get_current_parent), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Unit).where(Unit.id == unit_id))
    unit = result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail={"message": "Unit not found"})
    return unit


@units_router.put("/{unit_id}", response_model=UnitOut)
async def update_unit(unit_id: int, data: UnitUpdate, admin: Parent = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Unit).where(Unit.id == unit_id))
    unit = result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail={"message": "Unit not found"})
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(unit, field, value)
    await db.flush()
    await db.refresh(unit)
    await log_action(db, admin, "update", "unit", unit.id)
    return unit


@units_router.delete("/{unit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_unit(unit_id: int, admin: Parent = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Unit).where(Unit.id == unit_id))
    unit = result.scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail={"message": "Unit not found"})
    await log_action(db, admin, "delete", "unit", unit.id)
    await db.delete(unit)


# ── Lessons ────────────────────────────────────────────────────────────────────

@lessons_router.get("", response_model=PaginatedResponse)
async def list_lessons(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unit_id: Optional[int] = None,
    is_published: Optional[bool] = None,
    difficulty: Optional[DifficultyLevel] = None,
    sort_by: str = Query("order_index", pattern="^(order_index|created_at|title)$"),
    current_user: Parent = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    query = select(Lesson)
    if unit_id:
        query = query.where(Lesson.unit_id == unit_id)
    if is_published is not None:
        query = query.where(Lesson.is_published == is_published)
    if difficulty:
        query = query.where(Lesson.difficulty == difficulty)
    sort_col = getattr(Lesson, sort_by, Lesson.order_index)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    result = await db.execute(query.order_by(sort_col).offset((page - 1) * page_size).limit(page_size))
    return PaginatedResponse(
        total=total, page=page, page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
        items=[LessonOut.model_validate(l) for l in result.scalars().all()],
    )


@lessons_router.post("", response_model=LessonOut, status_code=status.HTTP_201_CREATED)
async def create_lesson(data: LessonCreate, admin: Parent = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    unit = (await db.execute(select(Unit).where(Unit.id == data.unit_id))).scalar_one_or_none()
    if not unit:
        raise HTTPException(status_code=404, detail={"message": "Unit not found"})
    lesson = Lesson(**data.model_dump())
    db.add(lesson)
    await db.flush()
    await db.refresh(lesson)
    await log_action(db, admin, "create", "lesson", lesson.id, {"title": lesson.title})
    return lesson


@lessons_router.get("/{lesson_id}", response_model=LessonOut)
async def get_lesson(lesson_id: int, current_user: Parent = Depends(get_current_parent), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail={"message": "Lesson not found"})
    return lesson


@lessons_router.put("/{lesson_id}", response_model=LessonOut)
async def update_lesson(lesson_id: int, data: LessonUpdate, admin: Parent = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail={"message": "Lesson not found"})
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(lesson, field, value)
    await db.flush()
    await db.refresh(lesson)
    await log_action(db, admin, "update", "lesson", lesson.id)
    return lesson


@lessons_router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(lesson_id: int, admin: Parent = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
    lesson = result.scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail={"message": "Lesson not found"})
    await log_action(db, admin, "delete", "lesson", lesson.id)
    await db.delete(lesson)


@lessons_router.get("/{lesson_id}/exercises", response_model=List[ExerciseOut])
async def get_lesson_exercises(lesson_id: int, current_user: Parent = Depends(get_current_parent), db: AsyncSession = Depends(get_db)):
    lesson = (await db.execute(select(Lesson).where(Lesson.id == lesson_id))).scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail={"message": "Lesson not found"})
    result = await db.execute(select(Exercise).where(Exercise.lesson_id == lesson_id).order_by(Exercise.order_index))
    return result.scalars().all()


@lessons_router.post("/{lesson_id}/exercises", response_model=ExerciseOut, status_code=201)
async def create_exercise(lesson_id: int, data: ExerciseCreate, admin: Parent = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    lesson = (await db.execute(select(Lesson).where(Lesson.id == lesson_id))).scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail={"message": "Lesson not found"})
    exercise = Exercise(lesson_id=lesson_id, **data.model_dump())
    db.add(exercise)
    await db.flush()
    await db.refresh(exercise)
    await log_action(db, admin, "create", "exercise", exercise.id)
    return exercise


# ── Exercises ──────────────────────────────────────────────────────────────────

@exercises_router.get("/{exercise_id}", response_model=ExerciseOut)
async def get_exercise(exercise_id: int, current_user: Parent = Depends(get_current_parent), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail={"message": "Exercise not found"})
    return exercise


@exercises_router.put("/{exercise_id}", response_model=ExerciseOut)
async def update_exercise(exercise_id: int, data: ExerciseUpdate, admin: Parent = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail={"message": "Exercise not found"})
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(exercise, field, value)
    await db.flush()
    await db.refresh(exercise)
    await log_action(db, admin, "update", "exercise", exercise.id)
    return exercise


@exercises_router.delete("/{exercise_id}", status_code=204)
async def delete_exercise(exercise_id: int, admin: Parent = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail={"message": "Exercise not found"})
    await log_action(db, admin, "delete", "exercise", exercise.id)
    await db.delete(exercise)
