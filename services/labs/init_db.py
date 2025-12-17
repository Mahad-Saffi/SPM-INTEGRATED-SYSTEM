"""
Initialize Labs Schema in PostgreSQL

This script creates the 'labs' schema and all required tables.
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
    """Create labs schema and tables"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Create schema if not exists
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS labs"))
        conn.commit()
        print("✅ Schema 'labs' created/verified")
    
    # Now create tables with schema prefix
    from app.database import Base, engine as app_engine
    Base.metadata.create_all(bind=app_engine)
    print("✅ Tables created in 'labs' schema")
    print("\nDatabase initialization complete!")

if __name__ == "__main__":
    print("🚀 Initializing Labs service database...")
    init_schema()
