from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from app.models.user import UserRole, BadgeType
from app.models.curriculum import DifficultyLevel, ExerciseType


# ── Pagination ────────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[Any]


# ── Auth ──────────────────────────────────────────────────────────────────────

class ParentRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ── Parent ────────────────────────────────────────────────────────────────────

class ParentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class ParentUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)


# ── Child ─────────────────────────────────────────────────────────────────────

class ChildCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    age: int = Field(ge=1, le=18)
    avatar: Optional[str] = None
    display_name: str = Field(min_length=1, max_length=100)


class ChildUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    age: Optional[int] = Field(None, ge=1, le=18)
    avatar: Optional[str] = None
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)


class ChildOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_id: int
    name: str
    age: int
    avatar: Optional[str]
    display_name: str
    xp: int
    level: int
    streak: int
    progress_percentage: int
    last_activity_date: Optional[datetime]
    created_at: datetime


# ── Badge ─────────────────────────────────────────────────────────────────────

class BadgeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    badge_type: BadgeType
    description: Optional[str]
    created_at: datetime


# ── Unit ──────────────────────────────────────────────────────────────────────

class UnitCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    order_index: int = 0
    difficulty: DifficultyLevel = DifficultyLevel.BEGINNER
    is_published: bool = False
    title_translations: Optional[dict] = None


class UnitUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    order_index: Optional[int] = None
    difficulty: Optional[DifficultyLevel] = None
    is_published: Optional[bool] = None
    title_translations: Optional[dict] = None


class UnitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str]
    order_index: int
    difficulty: DifficultyLevel
    is_published: bool
    title_translations: Optional[dict]
    created_at: datetime


# ── Lesson ────────────────────────────────────────────────────────────────────

class LessonCreate(BaseModel):
    unit_id: int
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    order_index: int = 0
    difficulty: DifficultyLevel = DifficultyLevel.BEGINNER
    is_published: bool = False
    xp_reward: int = Field(default=50, ge=1)
    title_translations: Optional[dict] = None


class LessonUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    order_index: Optional[int] = None
    difficulty: Optional[DifficultyLevel] = None
    is_published: Optional[bool] = None
    xp_reward: Optional[int] = Field(None, ge=1)
    title_translations: Optional[dict] = None


class LessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    unit_id: int
    title: str
    description: Optional[str]
    order_index: int
    difficulty: DifficultyLevel
    is_published: bool
    xp_reward: int
    title_translations: Optional[dict]
    created_at: datetime


# ── Exercise ──────────────────────────────────────────────────────────────────

class ExerciseCreate(BaseModel):
    exercise_type: ExerciseType
    question: str = Field(min_length=1)
    correct_answer: str = Field(min_length=1, max_length=500)
    options: Optional[list] = None
    order_index: int = 0
    instructions: Optional[str] = None


class ExerciseUpdate(BaseModel):
    exercise_type: Optional[ExerciseType] = None
    question: Optional[str] = None
    correct_answer: Optional[str] = Field(None, max_length=500)
    options: Optional[list] = None
    order_index: Optional[int] = None
    instructions: Optional[str] = None


class ExerciseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lesson_id: int
    exercise_type: ExerciseType
    question: str
    correct_answer: str
    options: Optional[list]
    order_index: int
    instructions: Optional[str]
    created_at: datetime


class ExerciseSubmit(BaseModel):
    child_id: int
    answer: str
    time_taken_seconds: Optional[int] = None


class ExerciseSubmitResult(BaseModel):
    is_correct: bool
    correct_answer: str
    message: str


# ── Progress ──────────────────────────────────────────────────────────────────

class LessonComplete(BaseModel):
    child_id: int


class LessonProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    child_id: int
    lesson_id: int
    is_completed: bool
    score: float
    xp_earned: int
    created_at: datetime


class LessonCompleteResult(BaseModel):
    xp_earned: int
    bonus_xp: int
    total_xp: int
    level: int
    leveled_up: bool
    streak: int
    streak_increased: bool
    new_badges: List[str]


# ── Notification ──────────────────────────────────────────────────────────────

class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    message: str
    is_read: bool
    child_id: Optional[int]
    created_at: datetime


class NotificationMarkRead(BaseModel):
    notification_ids: List[int]


# ── Leaderboard ───────────────────────────────────────────────────────────────

class LeaderboardEntry(BaseModel):
    rank: int
    display_name: str
    xp: int
    level: int
    streak: int
    age_group: str


# ── Admin ─────────────────────────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user_email: str
    action: str
    resource_type: str
    resource_id: Optional[int]
    details: Optional[str]
    created_at: datetime


class AdminStats(BaseModel):
    total_parents: int
    total_children: int
    total_lessons: int
    total_units: int
    active_children_today: int
    total_xp_awarded: int
    total_lesson_completions: int
