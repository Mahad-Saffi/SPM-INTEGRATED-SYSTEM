"""
Initialize Atlas Schema in PostgreSQL

This script creates the 'atlas' schema and all required tables.
Run this once before starting the service.
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://admin:secure_password@localhost:5432/project_management"
).replace("+asyncpg", "")  # Use sync driver for init

async def init_schema():
    """Create atlas schema and tables"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Create schema if not exists
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS atlas"))
        conn.commit()
        print("✅ Schema 'atlas' created/verified")
    
    # Now create tables with async engine
    from app.config.database import engine as app_engine
    from app.models.user import Base
    # Import all models to ensure they're registered
    from app.models import user, project, organization
    
    async with app_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Tables created in 'atlas' schema")
    print("\nDatabase initialization complete!")

if __name__ == "__main__":
    print("🚀 Initializing Atlas service database...")
    asyncio.run(init_schema())
