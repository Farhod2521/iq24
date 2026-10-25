from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import get_settings

engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    from . import models  # noqa: F401 — registers the tables on Base.metadata

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # create_all never alters existing tables; columns added after a table first shipped go here
        await conn.execute(text("ALTER TABLE questions ADD COLUMN IF NOT EXISTS image_url VARCHAR(500)"))
        await conn.execute(text("ALTER TABLE questions ADD COLUMN IF NOT EXISTS solution JSON"))
        await conn.execute(text("ALTER TABLE questions ADD COLUMN IF NOT EXISTS explainer JSON"))
        await conn.execute(text("ALTER TABLE questions ADD COLUMN IF NOT EXISTS figure JSON"))
