import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin
 
 
class UserRole(str, enum.Enum):
    PARENT = "parent"
    ADMIN = "admin"
 
 
class BadgeType(str, enum.Enum):
    FIRST_LESSON = "first_lesson"
    STREAK_7 = "streak_7"
    STREAK_30 = "streak_30"
    XP_100 = "xp_100"
    XP_500 = "xp_500"
    UNIT_COMPLETE = "unit_complete"
    PERFECT_LESSON = "perfect_lesson"
 
 
class Parent(Base, TimestampMixin):
    __tablename__ = "parents"
 
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.PARENT, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
 
    children = relationship("Child", back_populates="parent", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="parent", cascade="all, delete-orphan")
 
 
class Child(Base, TimestampMixin):
    __tablename__ = "children"
 
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("parents.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=False)
    avatar = Column(String(500), nullable=True)
    display_name = Column(String(100), nullable=False)
 
    xp = Column(Integer, default=0, nullable=False)
    level = Column(Integer, default=1, nullable=False)
    streak = Column(Integer, default=0, nullable=False)
    last_activity_date = Column(DateTime(timezone=True), nullable=True)
    progress_percentage = Column(Integer, default=0, nullable=False)
 
    parent = relationship("Parent", back_populates="children")
    badges = relationship("Badge", back_populates="child", cascade="all, delete-orphan")
    lesson_progress = relationship("LessonProgress", back_populates="child", cascade="all, delete-orphan")
    exercise_results = relationship("ExerciseResult", back_populates="child", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="child")
 
 
class Badge(Base, TimestampMixin):
    __tablename__ = "badges"
 
    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id", ondelete="CASCADE"), nullable=False, index=True)
    badge_type = Column(SAEnum(BadgeType), nullable=False)
    description = Column(String(500), nullable=True)
 
    child = relationship("Child", back_populates="badges")
 
 
class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"
 
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("parents.id", ondelete="CASCADE"), nullable=False, index=True)
    child_id = Column(Integer, ForeignKey("children.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
 
    parent = relationship("Parent", back_populates="notifications")
    child = relationship("Child", back_populates="notifications")
 
 
class AuditLog(Base, TimestampMixin):
    """
    Immutable audit log for all admin content operations.
    before_snapshot: JSON string of the resource state BEFORE the operation.
    after_snapshot:  JSON string of the resource state AFTER the operation.
    Records are never updated or deleted — only inserted.
    """
    __tablename__ = "audit_logs"
 
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    user_email = Column(String(255), nullable=False)
    action = Column(String(100), nullable=False)          # create | update | delete
    resource_type = Column(String(100), nullable=False)   # unit | lesson | exercise
    resource_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)                 # extra context
    before_snapshot = Column(Text, nullable=True)         # state before operation
    after_snapshot = Column(Text, nullable=True)          # state after operation
    ip_address = Column(String(50), nullable=True)