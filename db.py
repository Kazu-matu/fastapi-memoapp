"""
DB セッション管理

DATABASE_URL の先頭を見て SQLite / PostgreSQL を自動判別し、
それぞれ適切なエンジン設定を適用する。

  sqlite    : NullPool（接続プール不要）+ check_same_thread=False
  postgresql: QueuePool（デフォルト）+ pool_pre_ping + pool_size/max_overflow
"""
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from config import DATABASE_URL, DEBUG

Base = declarative_base()


def _build_engine():
    if DATABASE_URL.startswith("sqlite"):
        return create_async_engine(
            DATABASE_URL,
            echo=DEBUG,
            connect_args={"check_same_thread": False},
            poolclass=NullPool,
        )
    # PostgreSQL（asyncpg）
    return create_async_engine(
        DATABASE_URL,
        echo=DEBUG,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
    )


engine = _build_engine()

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_dbsession():
    async with async_session() as session:
        yield session
