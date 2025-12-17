"""
Initialize WorkPulse Schema in PostgreSQL

This script creates the 'workpulse' schema and all required tables.
Run this once before starting the service.
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:secure_password@localhost:5432/project_management"
)

def init_schema():
    """Create workpulse schema and tables"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Create schema if not exists
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS workpulse"))
        conn.commit()
        print("✅ Schema 'workpulse' created/verified")
    
    # Now create tables with schema prefix
    from app.database import Base, engine as app_engine
    Base.metadata.create_all(bind=app_engine)
    print("✅ Tables created in 'workpulse' schema")
    print("\nDatabase initialization complete!")

if __name__ == "__main__":
    print("🚀 Initializing WorkPulse service database...")
    init_schema()
