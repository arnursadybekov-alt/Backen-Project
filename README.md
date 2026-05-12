# Children's Literacy Learning Platform

![CI](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml/badge.svg)

A production-grade backend for a gamified children's literacy learning platform inspired by Duolingo ABC.

## Stack
- **FastAPI** + **SQLAlchemy 2.0** (async) + **PostgreSQL**
- **JWT** authentication with refresh tokens
- **WebSocket** real-time notifications
- **Alembic** database migrations
- **pytest** with 60%+ coverage

## Quick Start

### 1. Clone & configure
```bash
cp .env.example .env
# Edit .env with your DB credentials and JWT secret
```

### 2. Run with Docker Compose
```bash
docker-compose up --build
```

### 3. Run manually
```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### 4. Run tests
```bash
pytest
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL async URL | required |
| `JWT_SECRET_KEY` | Secret for signing JWTs | required |
| `JWT_ACCESS_TOKEN_EXPIRES` | Access token TTL (minutes) | 30 |
| `JWT_REFRESH_TOKEN_EXPIRES` | Refresh token TTL (days) | 7 |
| `XP_PER_LESSON` | XP awarded per lesson | 50 |
| `XP_LEVEL_THRESHOLD` | XP needed per level | 200 |
| `STREAK_BONUS_XP` | Bonus XP for streak ≥ 3 | 10 |
| `DEBUG` | Enable SQL logging | false |

## API Documentation

After starting the server:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Frontend**: http://localhost:8000/

## Architecture

```
app/
├── api/v1/endpoints/   # Route handlers (no business logic)
│   ├── auth.py         # Registration, login, refresh
│   ├── children.py     # Child profile CRUD
│   ├── curriculum.py   # Units, lessons, exercises
│   ├── progress.py     # Lesson completion, exercise submit
│   └── misc.py         # Parents, notifications, leaderboard, admin
├── core/
│   ├── security.py     # JWT, bcrypt
│   └── dependencies.py # FastAPI Depends (auth guards)
├── db/
│   ├── base.py         # DeclarativeBase + TimestampMixin
│   └── session.py      # Async engine & session
├── models/
│   ├── user.py         # Parent, Child, Badge, Notification, AuditLog
│   └── curriculum.py   # Unit, Lesson, Exercise, LessonProgress, ExerciseResult
├── schemas/
│   └── schemas.py      # All Pydantic request/response models
├── services/
│   ├── gamification_service.py  # XP, streaks, badges logic
│   └── audit_service.py         # Admin action logging
└── main.py             # FastAPI app, middleware, router registration
```

## Deployment (Render / Railway)

1. Set environment variables in your platform dashboard
2. Set build command: `pip install -r requirements.txt && alembic upgrade head`
3. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## API Endpoints

| Endpoint | Methods | Auth |
|----------|---------|------|
| `/api/v1/auth/register` | POST | Public |
| `/api/v1/auth/login` | POST | Public |
| `/api/v1/auth/refresh` | POST | Public |
| `/api/v1/auth/logout` | POST | Bearer |
| `/api/v1/parents/{id}` | GET, PUT | Bearer |
| `/api/v1/parents/{id}/children` | GET | Bearer |
| `/api/v1/children` | GET, POST | Bearer |
| `/api/v1/children/{id}` | GET, PUT, DELETE | Bearer |
| `/api/v1/children/{id}/badges` | GET | Bearer |
| `/api/v1/children/{id}/progress` | GET | Bearer |
| `/api/v1/units` | GET, POST | Bearer (POST: Admin) |
| `/api/v1/units/{id}` | GET, PUT, DELETE | Bearer (write: Admin) |
| `/api/v1/lessons` | GET, POST | Bearer (POST: Admin) |
| `/api/v1/lessons/{id}` | GET, PUT, DELETE | Bearer (write: Admin) |
| `/api/v1/lessons/{id}/exercises` | GET, POST | Bearer (POST: Admin) |
| `/api/v1/lessons/{id}/complete` | POST | Bearer |
| `/api/v1/exercises/{id}` | GET, PUT, DELETE | Bearer (write: Admin) |
| `/api/v1/exercises/{id}/submit` | POST | Bearer |
| `/api/v1/notifications` | GET, PATCH | Bearer |
| `/api/v1/leaderboard` | GET | Bearer |
| `/api/v1/admin/stats` | GET | Admin |
| `/api/v1/admin/logs` | GET | Admin |
| `/ws/notifications` | WS | Token query param |

## Gamification Logic

- **XP**: Each lesson awards `xp_reward` XP (default 50). Streak ≥ 3 adds 10 bonus XP.
- **Levels**: `level = (xp // 200) + 1`. Every 200 XP = level up.
- **Streaks**: Consecutive days with at least one lesson completed. Missed day resets to 1.
- **Badges**: Automatically awarded — First Lesson, 7-day Streak, 30-day Streak, 100 XP, 500 XP, Perfect Lesson.

## Real-Time Feature

WebSocket endpoint `/ws/notifications?token=<JWT>` pushes live events to parents when their child completes a lesson or earns a badge.
