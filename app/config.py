from pydantic_settings import BaseSettings
from typing import Optional
 
 
class Settings(BaseSettings):
    APP_NAME: str = "Children's Literacy Learning Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
 
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/literacy_db"
    TEST_DATABASE_URL: Optional[str] = None
 
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRES: int = 30    # minutes
    JWT_REFRESH_TOKEN_EXPIRES: int = 7   # days
 
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    LEADERBOARD_CACHE_TTL: int = 60      # seconds
 
    # Gamification
    XP_PER_LESSON: int = 50
    XP_LEVEL_THRESHOLD: int = 200
    STREAK_BONUS_XP: int = 10
 
    class Config:
        env_file = ".env"
        case_sensitive = True
 
 
settings = Settings()