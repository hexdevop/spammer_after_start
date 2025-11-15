from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from contextlib import asynccontextmanager
from config import config


def engine():
    return create_async_engine(url=config.database.database_url, echo=False)


@asynccontextmanager
async def get_session() -> AsyncSession:
    eng = engine()
    try:
        session_maker = async_sessionmaker(eng, expire_on_commit=False)
        async with session_maker() as session:
            yield session
    finally:
        await eng.dispose()
