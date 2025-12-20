from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL connection with labs schema
SQLALCHEMY_DATABASE_URL = os.getenv(
    "LABS_DATABASE_URL",
    os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://admin:admin123@localhost:5432/labs"
    )
)

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"server_settings": {"search_path": "labs,public"}}
)
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    class_=AsyncSession
)
Base = declarative_base()

# DB dependency
async def get_db():
    async with SessionLocal() as db:
        yield db
