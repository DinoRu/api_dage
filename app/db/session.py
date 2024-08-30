from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://postgres:admin123@db:5432/test_db"

engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()


async def get_db():
    async with async_session_maker() as session:
        yield session
   

async def create_all_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)