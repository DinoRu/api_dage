"""Database session management."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy import text, event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

logger = logging.getLogger(__name__)


# ===== BASE DECLARATIVE =====
class Base(DeclarativeBase):
    """Base class for all models."""
    pass


# ===== ENGINE CONFIGURATION =====
def get_engine_config() -> dict:
    """Get engine configuration based on environment."""
    config = {
        "echo": settings.DB_ECHO,
        "future": True,
        "pool_pre_ping": True,
    }
    
    if settings.is_production:
        # Production: pool optimisé
        config.update({
            "poolclass": QueuePool,
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_timeout": settings.DB_POOL_TIMEOUT,
            "pool_recycle": settings.DB_POOL_RECYCLE,
        })
    else:
        # Development: pool plus simple
        config.update({
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
        })
    
    return config


# ===== ENGINE CREATION =====
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    **get_engine_config()
)


# ===== TEST ENGINE (optionnel) =====
test_engine: AsyncEngine | None = None
if settings.TEST_DATABASE_URL:
    test_engine = create_async_engine(
        settings.TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,  # Pas de pool pour les tests
        future=True,
    )


# ===== SESSION FACTORY =====
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Permet d'accéder aux objets après commit
    autoflush=False,  # Contrôle manuel du flush
    autocommit=False,
)

TestAsyncSessionLocal = None
if test_engine:
    TestAsyncSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


# ===== DEPENDENCY INJECTION =====
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.
    
    Usage in FastAPI:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def get_test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting test database sessions.
    
    Usage in tests:
        @pytest.fixture
        async def db_session():
            async for session in get_test_db():
                yield session
    
    Yields:
        AsyncSession: Test database session
    """
    if not TestAsyncSessionLocal:
        raise RuntimeError("Test database is not configured")
    
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ===== CONTEXT MANAGER =====
@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """
    Context manager for getting database sessions outside of FastAPI.
    
    Usage:
        async with get_session() as session:
            result = await session.execute(query)
            await session.commit()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Session error: {e}")
            raise
        finally:
            await session.close()


# ===== DATABASE OPERATIONS =====
async def create_tables() -> None:
    """
    Create all tables in the database.
    
    Note: In production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables created successfully")


async def drop_tables() -> None:
    """
    Drop all tables from the database.
    
    Warning: This will delete all data!
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.warning("⚠️  Database tables dropped")


async def truncate_tables() -> None:
    """
    Truncate all tables (delete all data but keep structure).
    
    Warning: This will delete all data!
    """
    async with engine.begin() as conn:
        # Get all table names
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))
    logger.warning("⚠️  All tables truncated")


# ===== HEALTH CHECK =====
async def check_db_connection() -> bool:
    """
    Check if database connection is healthy.
    
    Returns:
        bool: True if connection is healthy, False otherwise
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection is healthy")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


async def get_db_info() -> dict:
    """
    Get database information.
    
    Returns:
        dict: Database information
    """
    try:
        async with engine.connect() as conn:
            # PostgreSQL version
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            
            # Current database
            result = await conn.execute(text("SELECT current_database()"))
            database = result.scalar()
            
            # Connection count
            result = await conn.execute(
                text("SELECT count(*) FROM pg_stat_activity")
            )
            connections = result.scalar()
            
            return {
                "status": "healthy",
                "version": version,
                "database": database,
                "connections": connections,
                "pool_size": engine.pool.size(),
                "pool_checked_out": engine.pool.checkedout(),
            }
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# ===== LIFECYCLE MANAGEMENT =====
async def init_db() -> None:
    """
    Initialize database connection.
    Call this on application startup.
    """
    logger.info("🔄 Initializing database connection...")
    
    # Check connection
    is_healthy = await check_db_connection()
    if not is_healthy:
        raise RuntimeError("Failed to connect to database")
    
    # Log database info
    db_info = await get_db_info()
    logger.info(f"📊 Database info: {db_info}")
    
    logger.info("✅ Database initialized successfully")


async def close_db() -> None:
    """
    Close database connection.
    Call this on application shutdown.
    """
    logger.info("🔄 Closing database connection...")
    
    await engine.dispose()
    
    if test_engine:
        await test_engine.dispose()
    
    logger.info("✅ Database connection closed")


# ===== EVENT LISTENERS =====
@event.listens_for(engine.sync_engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Event listener for new database connections."""
    logger.debug("New database connection established")


@event.listens_for(engine.sync_engine, "close")
def receive_close(dbapi_conn, connection_record):
    """Event listener for closed database connections."""
    logger.debug("Database connection closed")


# ===== TRANSACTION HELPER =====
class TransactionManager:
    """
    Context manager for handling database transactions.
    
    Usage:
        async with TransactionManager(session) as tm:
            # Your database operations
            await session.execute(query)
            # Auto-commit on success, auto-rollback on error
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def __aenter__(self) -> AsyncSession:
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.session.rollback()
            logger.error(f"Transaction rolled back: {exc_val}")
        else:
            await self.session.commit()
        
        await self.session.close()