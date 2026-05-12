from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import Child, Parent
from app.models.curriculum import Lesson, Exercise, LessonProgress, ExerciseResult
from app.core.dependencies import get_current_parent
from app.services.gamification_service import process_lesson_completion, create_notification
from app.api.v1.websocket import manager
from app.schemas.schemas import LessonComplete, LessonCompleteResult, ExerciseSubmit, ExerciseSubmitResult

router = APIRouter(tags=["Progress"])


@router.post("/lessons/{lesson_id}/complete", response_model=LessonCompleteResult)
async def complete_lesson(
    lesson_id: int,
    data: LessonComplete,
    current_user: Parent = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    lesson = (await db.execute(select(Lesson).where(Lesson.id == lesson_id))).scalar_one_or_none()
    if not lesson:
        raise HTTPException(status_code=404, detail={"message": "Lesson not found"})
    if not lesson.is_published:
        raise HTTPException(status_code=403, detail={"message": "Lesson not published"})

    child = (await db.execute(select(Child).where(Child.id == data.child_id))).scalar_one_or_none()
    if not child:
        raise HTTPException(status_code=404, detail={"message": "Child not found"})
    if child.parent_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail={"message": "Access denied"})

    # Check existing progress
    existing = (await db.execute(
        select(LessonProgress).where(LessonProgress.child_id == child.id, LessonProgress.lesson_id == lesson_id)
    )).scalar_one_or_none()

    # Calculate score from exercise results
    exercises = (await db.execute(select(Exercise).where(Exercise.lesson_id == lesson_id))).scalars().all()
    total = len(exercises)
    if total > 0:
        correct = (await db.execute(
            select(ExerciseResult).where(
                ExerciseResult.child_id == child.id,
                ExerciseResult.exercise_id.in_([e.id for e in exercises]),
                ExerciseResult.is_correct == True,
            )
        )).scalars().all()
        score = len(correct) / total
    else:
        score = 1.0

    result = await process_lesson_completion(child, lesson.xp_reward, score, db)

    if existing:
        existing.is_completed = True
        existing.score = score
        existing.xp_earned = result["xp_earned"]
    else:
        progress = LessonProgress(
            child_id=child.id,
            lesson_id=lesson_id,
            is_completed=True,
            score=score,
            xp_earned=result["xp_earned"],
        )
        db.add(progress)

    # Send notification
    notif_msg = f"{child.display_name} completed '{lesson.title}'"
    if result["leveled_up"]:
        notif_msg += f" and leveled up to Level {result['level']}!"
    await create_notification(current_user.id, child.id, "Lesson Completed! 🎉", notif_msg, db)

    # WebSocket push
    await manager.send_to_parent(current_user.id, {
        "type": "lesson_complete",
        "child": child.display_name,
        "lesson": lesson.title,
        "xp_earned": result["xp_earned"],
        "new_badges": result["new_badges"],
    })

    return LessonCompleteResult(**result)


@router.post("/exercises/{exercise_id}/submit", response_model=ExerciseSubmitResult)
async def submit_exercise(
    exercise_id: int,
    data: ExerciseSubmit,
    current_user: Parent = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    exercise = (await db.execute(select(Exercise).where(Exercise.id == exercise_id))).scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail={"message": "Exercise not found"})

    child = (await db.execute(select(Child).where(Child.id == data.child_id))).scalar_one_or_none()
    if not child:
        raise HTTPException(status_code=404, detail={"message": "Child not found"})
    if child.parent_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail={"message": "Access denied"})

    is_correct = data.answer.strip().lower() == exercise.correct_answer.strip().lower()

    ex_result = ExerciseResult(
        child_id=child.id,
        exercise_id=exercise_id,
        answer=data.answer,
        is_correct=is_correct,
        time_taken_seconds=data.time_taken_seconds,
    )
    db.add(ex_result)

    return ExerciseSubmitResult(
        is_correct=is_correct,
        correct_answer=exercise.correct_answer,
        message="Correct! Great job!" if is_correct else "Not quite. Keep trying!",
    )
