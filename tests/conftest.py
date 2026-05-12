import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.security import hash_password
from app.models.user import Parent, Child, UserRole

TEST_DB_URL = "sqlite+aiosqlite:///./test.db"

engine_test = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine_test, class_=AsyncSession, expire_on_commit=False, autoflush=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture(scope="function")
async def db():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSessionLocal() as session:
        yield session
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db):
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def parent_user(db):
    parent = Parent(
        email="test@example.com",
        hashed_password=hash_password("testpass123"),
        full_name="Test Parent",
        role=UserRole.PARENT,
    )
    db.add(parent)
    await db.commit()
    await db.refresh(parent)
    return parent


@pytest_asyncio.fixture
async def admin_user(db):
    admin = Parent(
        email="admin@example.com",
        hashed_password=hash_password("adminpass123"),
        full_name="Admin User",
        role=UserRole.ADMIN,
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def auth_headers(client):
    res = await client.post("/api/v1/auth/register", json={
        "email": "parent@test.com",
        "password": "password123",
        "full_name": "Test Parent",
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_headers(client, db):
    # Create admin directly
    admin = Parent(
        email="admin2@test.com",
        hashed_password=hash_password("adminpass123"),
        full_name="Admin",
        role=UserRole.ADMIN,
    )
    db.add(admin)
    await db.commit()
    res = await client.post("/api/v1/auth/login", json={"email": "admin2@test.com", "password": "adminpass123"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
