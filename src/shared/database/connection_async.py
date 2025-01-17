from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.config import settings


def get_async_engine():
    db_engine = create_async_engine(settings.async_db_url, pool_pre_ping=True)
    return db_engine


async_engine = get_async_engine()
AsyncSessionFactory = async_sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=async_engine
)


# 비동기 generator 반환
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    db = AsyncSessionFactory()
    try:
        yield db
    finally:
        await db.close()
