"""Database connection and session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from grc_core.models import Base


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, database_url: str, echo: bool = False) -> None:
        """Initialize database manager.

        Args:
            database_url: PostgreSQL connection URL (postgresql+asyncpg://...)
            echo: Whether to log SQL statements
        """
        self.engine: AsyncEngine = create_async_engine(
            database_url,
            echo=echo,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    async def create_tables(self) -> None:
        """Create all tables in the database."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self) -> None:
        """Drop all tables in the database."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def close(self) -> None:
        """Close the database engine."""
        await self.engine.dispose()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Provide a transactional scope around a series of operations."""
        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session (for FastAPI dependency injection)."""
        async with self.session() as session:
            yield session


# Global database manager instance (initialized in application startup)
_db_manager: DatabaseManager | None = None


def init_database(database_url: str, echo: bool = False) -> DatabaseManager:
    """Initialize the global database manager."""
    global _db_manager
    _db_manager = DatabaseManager(database_url, echo=echo)
    return _db_manager


def get_database() -> DatabaseManager:
    """Get the global database manager."""
    if _db_manager is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _db_manager
