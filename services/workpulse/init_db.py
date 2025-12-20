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
        
        # Create users table explicitly (SQLAlchemy ORM sometimes doesn't create it)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS workpulse.users (
                id VARCHAR(50) PRIMARY KEY,
                orchestrator_user_id UUID UNIQUE NOT NULL,
                email VARCHAR UNIQUE,
                name VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
        print("✅ Users table created/verified")
    
    # Now create other tables with schema prefix
    from app.database import Base, engine as app_engine
    
    # Set search path for the engine
    with app_engine.connect() as conn:
        conn.execute(text("SET search_path TO workpulse,public"))
        conn.commit()
    
    Base.metadata.create_all(bind=app_engine)
    print("✅ All tables created in 'workpulse' schema")
    
    # Verify tables were created
    from sqlalchemy import inspect
    inspector = inspect(app_engine)
    with app_engine.connect() as conn:
        conn.execute(text("SET search_path TO workpulse,public"))
        conn.commit()
    
    tables = inspector.get_table_names(schema='workpulse')
    print(f"📋 Tables created: {tables}")
    print("\nDatabase initialization complete!")

if __name__ == "__main__":
    print("🚀 Initializing WorkPulse service database...")
    init_schema()
