"""
Migrate WorkPulse database schema

This script ensures all required columns exist in the workpulse schema.
Run this to update existing databases with new columns.
"""

from sqlalchemy import create_engine, text, inspect
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:secure_password@localhost:5432/project_management"
)

def migrate_schema():
    """Migrate workpulse schema - add missing columns"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Create schema if not exists
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS workpulse"))
        conn.commit()
        print("✅ Schema 'workpulse' verified")
        
        # Check if users table exists
        inspector = inspect(engine)
        
        # Set search path to workpulse schema
        conn.execute(text("SET search_path TO workpulse,public"))
        conn.commit()
        
        # Get tables in workpulse schema
        tables = inspector.get_table_names(schema='workpulse')
        print(f"📋 Tables in workpulse schema: {tables}")
        
        # Check and add missing columns to users table
        if 'users' in tables:
            columns = {col['name'] for col in inspector.get_columns('users', schema='workpulse')}
            print(f"📋 Columns in users table: {columns}")
            
            # Add orchestrator_user_id if missing
            if 'orchestrator_user_id' not in columns:
                print("➕ Adding orchestrator_user_id column to users table...")
                conn.execute(text("""
                    ALTER TABLE workpulse.users 
                    ADD COLUMN orchestrator_user_id UUID UNIQUE
                """))
                conn.commit()
                print("✅ orchestrator_user_id column added to users table")
            else:
                print("✅ orchestrator_user_id column already exists in users table")
        else:
            print("⚠️ users table does not exist, will be created by app")
        
        # Check and add missing columns to activities table
        if 'activities' in tables:
            columns = {col['name'] for col in inspector.get_columns('activities', schema='workpulse')}
            print(f"📋 Columns in activities table: {columns}")
            
            # Add orchestrator_user_id if missing
            if 'orchestrator_user_id' not in columns:
                print("➕ Adding orchestrator_user_id column to activities table...")
                conn.execute(text("""
                    ALTER TABLE workpulse.activities 
                    ADD COLUMN orchestrator_user_id UUID
                """))
                conn.commit()
                print("✅ orchestrator_user_id column added to activities table")
            else:
                print("✅ orchestrator_user_id column already exists in activities table")
        else:
            print("⚠️ activities table does not exist, will be created by app")
        
        # Check and add missing columns to productivity_stats table
        if 'productivity_stats' in tables:
            columns = {col['name'] for col in inspector.get_columns('productivity_stats', schema='workpulse')}
            print(f"📋 Columns in productivity_stats table: {columns}")
            
            # Add orchestrator_user_id if missing
            if 'orchestrator_user_id' not in columns:
                print("➕ Adding orchestrator_user_id column to productivity_stats table...")
                conn.execute(text("""
                    ALTER TABLE workpulse.productivity_stats 
                    ADD COLUMN orchestrator_user_id UUID
                """))
                conn.commit()
                print("✅ orchestrator_user_id column added to productivity_stats table")
            else:
                print("✅ orchestrator_user_id column already exists in productivity_stats table")
        else:
            print("⚠️ productivity_stats table does not exist, will be created by app")
    
    print("\n✅ Database migration complete!")

if __name__ == "__main__":
    print("🚀 Migrating WorkPulse service database...")
    try:
        migrate_schema()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
