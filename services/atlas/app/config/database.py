from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from starlette.config import Config
import os
from dotenv import load_dotenv

load_dotenv()

# Try to load .env from backend directory
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
config = Config(env_path if os.path.exists(env_path) else ".env")

# PostgreSQL with atlas schema
DATABASE_URL = os.getenv(
    "ATLAS_DATABASE_URL",
    os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://admin:admin123@localhost:5432/atlas"
    )
)

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"server_settings": {"search_path": "atlas,public"}}
)
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

from app.models.user import Base