"""
Migrate Labs database schema

This script ensures all required columns exist in the labs schema.
Run this to update existing databases with new columns.
"""

from sqlalchemy import create_engine, text, inspect
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://paperless:paperless@localhost:5432/project_management"
)

def migrate_schema():
    """Migrate labs schema - add missing columns and update constraints"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Create schema if not exists
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS labs"))
        conn.commit()
        print("✅ Schema 'labs' verified")
        
        # Set search path to labs schema
        conn.execute(text("SET search_path TO labs,public"))
        conn.commit()
        
        # Get tables in labs schema
        inspector = inspect(engine)
        tables = inspector.get_table_names(schema='labs')
        print(f"📋 Tables in labs schema: {tables}")
        
        # Check and add missing columns to labs table
        if 'labs' in tables:
            columns = {col['name'] for col in inspector.get_columns('labs', schema='labs')}
            print(f"📋 Columns in labs table: {columns}")
            
            # Add orchestrator_user_id if missing
            if 'orchestrator_user_id' not in columns:
                print("➕ Adding orchestrator_user_id column to labs table...")
                conn.execute(text("""
                    ALTER TABLE labs.labs 
                    ADD COLUMN orchestrator_user_id UUID
                """))
                conn.commit()
                print("✅ orchestrator_user_id column added to labs table")
            else:
                print("✅ orchestrator_user_id column already exists in labs table")
            
            # Update orchestrator_org_id to NOT NULL
            print("➕ Updating orchestrator_org_id constraint...")
            try:
                # Check if there are any NULL values
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM labs.labs WHERE orchestrator_org_id IS NULL
                """))
                null_count = result.scalar()
                
                if null_count > 0:
                    print(f"⚠️  Found {null_count} labs with NULL orchestrator_org_id")
                    print("   Setting default organization UUID for existing labs...")
                    # Use a default UUID for existing labs
                    conn.execute(text("""
                        UPDATE labs.labs 
                        SET orchestrator_org_id = '00000000-0000-0000-0000-000000000000'::uuid
                        WHERE orchestrator_org_id IS NULL
                    """))
                    conn.commit()
                    print("✅ Updated NULL values with default UUID")
                
                # Now add NOT NULL constraint
                conn.execute(text("""
                    ALTER TABLE labs.labs 
                    ALTER COLUMN orchestrator_org_id SET NOT NULL
                """))
                conn.commit()
                print("✅ orchestrator_org_id is now NOT NULL")
            except Exception as e:
                if "already" in str(e).lower() or "constraint" in str(e).lower():
                    print("✅ orchestrator_org_id constraint already set")
                else:
                    print(f"⚠️  Could not update constraint: {e}")
        else:
            print("⚠️ labs table does not exist, will be created by app")
    
    print("\n✅ Database migration complete!")

if __name__ == "__main__":
    print("🚀 Migrating Labs service database...")
    try:
        migrate_schema()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
