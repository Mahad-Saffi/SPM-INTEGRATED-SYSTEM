"""
Database migration script for Atlas service
Converts all Integer IDs to UUIDs
"""
import logging
import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://paperless:paperless@localhost:5432/project_management")


def migrate_to_uuid():
    """Convert all IDs to UUID"""
    # Convert async URL to sync URL
    db_url = os.getenv("DATABASE_URL", "postgresql://paperless:paperless@localhost:5432/project_management")
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    try:
        logger.info("🔄 Converting Atlas IDs to UUID...")
        
        # Update users table
        cursor.execute("""
            ALTER TABLE users ADD COLUMN id_new UUID DEFAULT gen_random_uuid();
            ALTER TABLE users ADD COLUMN invited_by_new UUID;
        """)
        
        # Update projects table
        cursor.execute("""
            ALTER TABLE projects ADD COLUMN owner_id_new UUID;
            ALTER TABLE projects ADD COLUMN lab_id_new UUID;
        """)
        
        # Update tasks table
        cursor.execute("""
            ALTER TABLE tasks ADD COLUMN assignee_id_new UUID;
        """)
        
        # Copy data
        cursor.execute("""
            UPDATE users SET id_new = gen_random_uuid();
            UPDATE projects SET owner_id_new = (SELECT id_new FROM users WHERE users.id = projects.owner_id);
            UPDATE tasks SET assignee_id_new = (SELECT id_new FROM users WHERE users.id = tasks.assignee_id);
        """)
        
        # Drop constraints
        cursor.execute("""
            ALTER TABLE projects DROP CONSTRAINT IF EXISTS projects_owner_id_fkey;
            ALTER TABLE tasks DROP CONSTRAINT IF EXISTS tasks_assignee_id_fkey;
        """)
        
        # Drop old columns and rename
        cursor.execute("""
            ALTER TABLE users DROP COLUMN id;
            ALTER TABLE users RENAME COLUMN id_new TO id;
            ALTER TABLE users DROP COLUMN invited_by;
            ALTER TABLE users RENAME COLUMN invited_by_new TO invited_by;
            ALTER TABLE users ADD PRIMARY KEY (id);
            
            ALTER TABLE projects DROP COLUMN owner_id;
            ALTER TABLE projects RENAME COLUMN owner_id_new TO owner_id;
            ALTER TABLE projects DROP COLUMN lab_id;
            ALTER TABLE projects RENAME COLUMN lab_id_new TO lab_id;
            
            ALTER TABLE tasks DROP COLUMN assignee_id;
            ALTER TABLE tasks RENAME COLUMN assignee_id_new TO assignee_id;
        """)
        
        # Recreate foreign keys
        cursor.execute("""
            ALTER TABLE projects ADD CONSTRAINT projects_owner_id_fkey 
                FOREIGN KEY (owner_id) REFERENCES users(id);
            ALTER TABLE tasks ADD CONSTRAINT tasks_assignee_id_fkey 
                FOREIGN KEY (assignee_id) REFERENCES users(id);
        """)
        
        conn.commit()
        logger.info("✅ Successfully converted all IDs to UUID")
        
    except Exception as e:
        logger.error(f"❌ Error during migration: {str(e)}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def main():
    """Run migration"""
    logger.info("🔄 Starting Atlas UUID migration...")
    migrate_to_uuid()


if __name__ == "__main__":
    main()
