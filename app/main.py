from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import IntegrityError
import logging
import os

from app.config import settings
from app.db.session import engine
from app.db.base import Base

# Import models so SQLAlchemy registers them
from app.models import user, curriculum  # noqa

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.children import router as children_router
from app.api.v1.endpoints.curriculum import units_router, lessons_router, exercises_router
from app.api.v1.endpoints.progress import router as progress_router
from app.api.v1.endpoints.misc import parents_router, notifications_router, leaderboard_router, admin_router
from app.api.v1.websocket import router as ws_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready")
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Children's Literacy Learning Platform API

Backend for a gamified children's literacy platform inspired by Duolingo ABC.

### Features
- **JWT Authentication** with refresh tokens
- **Role-based access control** (Parent / Admin)
- **Gamification**: XP, levels, streaks, badges
- **Real-time notifications** via WebSocket
- **Full curriculum management**: Units → Lessons → Exercises
- **Progress tracking** with detailed analytics
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    return JSONResponse(status_code=409, content={"message": "Resource already exists or constraint violation"})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"message": "Internal server error"})


PREFIX = "/api/v1"
app.include_router(auth_router, prefix=PREFIX)
app.include_router(parents_router, prefix=PREFIX)
app.include_router(children_router, prefix=PREFIX)
app.include_router(units_router, prefix=PREFIX)
app.include_router(lessons_router, prefix=PREFIX)
app.include_router(exercises_router, prefix=PREFIX)
app.include_router(progress_router, prefix=PREFIX)
app.include_router(notifications_router, prefix=PREFIX)
app.include_router(leaderboard_router, prefix=PREFIX)
app.include_router(admin_router, prefix=PREFIX)
app.include_router(ws_router)

# Serve frontend
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
