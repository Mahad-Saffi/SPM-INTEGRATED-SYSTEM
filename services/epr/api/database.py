"""
PostgreSQL Database Setup for Performance API
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL connection with performance schema
DATABASE_URL = os.getenv(
    "EPR_DATABASE_URL",
    os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://admin:admin123@localhost:5432/epr"
    )
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    connect_args={"server_settings": {"search_path": "performance,public"}}
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    class_=AsyncSession
)

# Base class for models
Base = declarative_base()

async def get_db():
    """Dependency to get database session"""
    async with SessionLocal() as db:
        yield db

async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


