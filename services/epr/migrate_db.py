"""
Migrate EPR database schema

This script ensures all required columns exist in the EPR schema.
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
    """Migrate EPR schema - add missing orchestrator_user_id columns"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Create schema if not exists
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS epr"))
        conn.commit()
        print("✅ Schema 'epr' verified")
        
        # Set search path to epr schema
        conn.execute(text("SET search_path TO epr,public"))
        conn.commit()
        
        # Get tables in epr schema
        inspector = inspect(engine)
        tables = inspector.get_table_names(schema='epr')
        print(f"📋 Tables in epr schema: {tables}")
        
        # Tables that need orchestrator_user_id column
        tables_to_update = {
            'performance_reviews': 'orchestrator_user_id',
            'performance_goals': 'orchestrator_user_id',
            'peer_feedback': 'orchestrator_user_id',
            'skill_assessments': 'orchestrator_user_id',
            'performance_metrics': 'orchestrator_user_id',
            'performances': 'orchestrator_user_id',
            'notifications': 'orchestrator_user_id'
        }
        
        for table_name, column_name in tables_to_update.items():
            if table_name in tables:
                columns = {col['name'] for col in inspector.get_columns(table_name, schema='epr')}
                print(f"📋 Columns in {table_name} table: {columns}")
                
                if column_name not in columns:
                    print(f"➕ Adding {column_name} column to {table_name} table...")
                    conn.execute(text(f"""
                        ALTER TABLE epr.{table_name} 
                        ADD COLUMN {column_name} UUID
                    """))
                    conn.commit()
                    print(f"✅ {column_name} column added to {table_name} table")
                else:
                    print(f"✅ {column_name} column already exists in {table_name} table")
            else:
                print(f"⚠️ {table_name} table does not exist, will be created by app")
        
        # Special case: peer_feedback needs reviewer_orchestrator_user_id
        if 'peer_feedback' in tables:
            columns = {col['name'] for col in inspector.get_columns('peer_feedback', schema='epr')}
            if 'reviewer_orchestrator_user_id' not in columns:
                print("➕ Adding reviewer_orchestrator_user_id column to peer_feedback table...")
                conn.execute(text("""
                    ALTER TABLE epr.peer_feedback 
                    ADD COLUMN reviewer_orchestrator_user_id UUID
                """))
                conn.commit()
                print("✅ reviewer_orchestrator_user_id column added to peer_feedback table")
    
    print("\n✅ Database migration complete!")

if __name__ == "__main__":
    print("🚀 Migrating EPR service database...")
    try:
        migrate_schema()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
