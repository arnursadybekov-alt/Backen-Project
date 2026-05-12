from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.config import settings

_url = settings.DATABASE_URL
_is_sqlite = "sqlite" in _url

_kwargs = {"echo": settings.DEBUG, "pool_pre_ping": not _is_sqlite}
if not _is_sqlite:
    _kwargs["pool_size"] = 10
    _kwargs["max_overflow"] = 20

engine = create_async_engine(_url, **_kwargs)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
