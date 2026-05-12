import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, Text, JSON, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin


class DifficultyLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ExerciseType(str, enum.Enum):
    PHONICS = "phonics"
    HANDWRITING = "handwriting"
    SIGHT_WORDS = "sight_words"
    VOCABULARY = "vocabulary"


class Unit(Base, TimestampMixin):
    __tablename__ = "units"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0, nullable=False, index=True)
    difficulty = Column(SAEnum(DifficultyLevel), default=DifficultyLevel.BEGINNER, nullable=False)
    is_published = Column(Boolean, default=False, nullable=False, index=True)
    title_translations = Column(JSON, nullable=True)  # {"en": "...", "kz": "..."}

    lessons = relationship("Lesson", back_populates="unit", cascade="all, delete-orphan", order_by="Lesson.order_index")


class Lesson(Base, TimestampMixin):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, ForeignKey("units.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0, nullable=False, index=True)
    difficulty = Column(SAEnum(DifficultyLevel), default=DifficultyLevel.BEGINNER, nullable=False)
    is_published = Column(Boolean, default=False, nullable=False, index=True)
    xp_reward = Column(Integer, default=50, nullable=False)
    title_translations = Column(JSON, nullable=True)

    unit = relationship("Unit", back_populates="lessons")
    exercises = relationship("Exercise", back_populates="lesson", cascade="all, delete-orphan", order_by="Exercise.order_index")
    progress_records = relationship("LessonProgress", back_populates="lesson")


class Exercise(Base, TimestampMixin):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    exercise_type = Column(SAEnum(ExerciseType), nullable=False)
    question = Column(Text, nullable=False)
    correct_answer = Column(String(500), nullable=False)
    options = Column(JSON, nullable=True)  # for multiple choice
    order_index = Column(Integer, default=0, nullable=False)
    instructions = Column(Text, nullable=True)

    lesson = relationship("Lesson", back_populates="exercises")
    results = relationship("ExerciseResult", back_populates="exercise", cascade="all, delete-orphan")


class LessonProgress(Base, TimestampMixin):
    __tablename__ = "lesson_progress"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    is_completed = Column(Boolean, default=False, nullable=False)
    score = Column(Float, default=0.0, nullable=False)
    xp_earned = Column(Integer, default=0, nullable=False)

    child = relationship("Child", back_populates="lesson_progress")
    lesson = relationship("Lesson", back_populates="progress_records")


class ExerciseResult(Base, TimestampMixin):
    __tablename__ = "exercise_results"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id", ondelete="CASCADE"), nullable=False, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False, index=True)
    answer = Column(String(500), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    time_taken_seconds = Column(Integer, nullable=True)

    child = relationship("Child", back_populates="exercise_results")
    exercise = relationship("Exercise", back_populates="results")
from fastapi.responses import JSONResponse
from fastapi import Response

@lessons_router.get("/{lesson_id}")
async def get_lesson(..., response: Response):
    # ...
    response.headers["ETag"] = f'"lesson-{lesson.id}-{lesson.updated_at.isoformat()}"'
    response.headers["Cache-Control"] = "public, max-age=3600"
    return lesson