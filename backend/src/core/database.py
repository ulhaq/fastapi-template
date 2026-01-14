from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.core.config import settings

engine = create_async_engine(settings.db_connection, echo=settings.sqlalchemy_echo)
ASYNC_SESSION_LOCAL = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase): ...  # pylint: disable=too-few-public-methods


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with ASYNC_SESSION_LOCAL(expire_on_commit=True) as db:
        yield db
