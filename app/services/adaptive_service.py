"""
Adaptive Difficulty Service.
 
Analyses a child's last N exercise results and recommends the next
difficulty level (beginner / intermediate / advanced).
 
Rules:
  - Look at the last WINDOW results for the child.
  - accuracy >= HIGH_THRESHOLD  → go up one level
  - accuracy <= LOW_THRESHOLD   → go down one level
  - otherwise                   → stay at current level
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.curriculum import ExerciseResult, Exercise, DifficultyLevel
 
WINDOW = 10          # how many recent results to consider
HIGH_THRESHOLD = 0.8  # 80 % correct → increase difficulty
LOW_THRESHOLD = 0.5   # below 50 % correct → decrease difficulty
 
_LEVELS = [DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED]
 
 
async def get_recommended_difficulty(
    child_id: int,
    db: AsyncSession,
) -> dict:
    """
    Return the recommended difficulty for the child's next exercise session.
 
    Returns a dict:
    {
        "recommended_difficulty": "beginner" | "intermediate" | "advanced",
        "accuracy": float,          # 0.0 – 1.0
        "results_analysed": int,
        "reason": str,
    }
    """
    # Fetch last WINDOW exercise results for this child
    stmt = (
        select(ExerciseResult)
        .where(ExerciseResult.child_id == child_id)
        .order_by(desc(ExerciseResult.created_at))
        .limit(WINDOW)
    )
    rows = (await db.execute(stmt)).scalars().all()
 
    if not rows:
        return {
            "recommended_difficulty": DifficultyLevel.BEGINNER.value,
            "accuracy": 0.0,
            "results_analysed": 0,
            "reason": "No exercise history found — starting at beginner level.",
        }
 
    total = len(rows)
    correct = sum(1 for r in rows if r.is_correct)
    accuracy = correct / total
 
    # Determine current difficulty from the most recent exercise
    latest_exercise = (
        await db.execute(
            select(Exercise).where(Exercise.id == rows[0].exercise_id)
        )
    ).scalar_one_or_none()
 
    current_level = (
        DifficultyLevel(latest_exercise.lesson.difficulty.value)
        if latest_exercise and hasattr(latest_exercise, "lesson") and latest_exercise.lesson
        else DifficultyLevel.BEGINNER
    )
 
    current_idx = _LEVELS.index(current_level) if current_level in _LEVELS else 0
 
    if accuracy >= HIGH_THRESHOLD:
        new_idx = min(current_idx + 1, len(_LEVELS) - 1)
        reason = f"Accuracy {accuracy:.0%} ≥ {HIGH_THRESHOLD:.0%} — moving up."
    elif accuracy <= LOW_THRESHOLD:
        new_idx = max(current_idx - 1, 0)
        reason = f"Accuracy {accuracy:.0%} ≤ {LOW_THRESHOLD:.0%} — moving down."
    else:
        new_idx = current_idx
        reason = f"Accuracy {accuracy:.0%} — staying at current level."
 
    return {
        "recommended_difficulty": _LEVELS[new_idx].value,
        "accuracy": round(accuracy, 4),
        "results_analysed": total,
        "reason": reason,
    }