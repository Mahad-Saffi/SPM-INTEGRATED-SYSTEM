"""
Database migration script for Labs service
Converts all Integer IDs to UUIDs
"""
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://paperless:paperless@localhost:5432/project_management")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def migrate_to_uuid():
    """Convert all IDs to UUID"""
    session = SessionLocal()
    try:
        # Check if labs table has UUID id
        result = session.execute(
            text("""
                SELECT data_type FROM information_schema.columns 
                WHERE table_schema='labs' AND table_name='labs' AND column_name='id'
            """)
        )
        
        data_type = result.scalar()
        if data_type and 'uuid' in data_type.lower():
            logger.info("✅ Labs already using UUID IDs")
            return
        
        logger.info("🔄 Converting Labs IDs to UUID...")
        
        # Recreate labs table with UUID
        session.execute(text("""
            ALTER TABLE labs.collaborations DROP CONSTRAINT IF EXISTS collaborations_lab_id_fkey;
            ALTER TABLE labs.collaborations DROP CONSTRAINT IF EXISTS collaborations_researcher_id_fkey;
            ALTER TABLE labs.researchers DROP CONSTRAINT IF EXISTS researchers_lab_id_fkey;
        """))
        
        # Add new UUID columns
        session.execute(text("""
            ALTER TABLE labs.labs ADD COLUMN id_new UUID DEFAULT gen_random_uuid();
            ALTER TABLE labs.researchers ADD COLUMN id_new UUID DEFAULT gen_random_uuid();
            ALTER TABLE labs.researchers ADD COLUMN lab_id_new UUID;
            ALTER TABLE labs.collaborations ADD COLUMN id_new UUID DEFAULT gen_random_uuid();
            ALTER TABLE labs.collaborations ADD COLUMN lab_id_new UUID;
            ALTER TABLE labs.collaborations ADD COLUMN researcher_id_new UUID;
        """))
        
        # Copy data
        session.execute(text("""
            UPDATE labs.researchers SET lab_id_new = (
                SELECT id_new FROM labs.labs WHERE labs.id = researchers.lab_id
            );
            UPDATE labs.collaborations SET lab_id_new = (
                SELECT id_new FROM labs.labs WHERE labs.id = collaborations.lab_id
            );
            UPDATE labs.collaborations SET researcher_id_new = (
                SELECT id_new FROM labs.researchers WHERE researchers.id = collaborations.researcher_id
            );
        """))
        
        # Drop old columns and rename
        session.execute(text("""
            ALTER TABLE labs.labs DROP COLUMN id;
            ALTER TABLE labs.labs RENAME COLUMN id_new TO id;
            ALTER TABLE labs.labs ADD PRIMARY KEY (id);
            
            ALTER TABLE labs.researchers DROP COLUMN id;
            ALTER TABLE labs.researchers RENAME COLUMN id_new TO id;
            ALTER TABLE labs.researchers DROP COLUMN lab_id;
            ALTER TABLE labs.researchers RENAME COLUMN lab_id_new TO lab_id;
            ALTER TABLE labs.researchers ADD PRIMARY KEY (id);
            
            ALTER TABLE labs.collaborations DROP COLUMN id;
            ALTER TABLE labs.collaborations RENAME COLUMN id_new TO id;
            ALTER TABLE labs.collaborations DROP COLUMN lab_id;
            ALTER TABLE labs.collaborations RENAME COLUMN lab_id_new TO lab_id;
            ALTER TABLE labs.collaborations DROP COLUMN researcher_id;
            ALTER TABLE labs.collaborations RENAME COLUMN researcher_id_new TO researcher_id;
            ALTER TABLE labs.collaborations ADD PRIMARY KEY (id);
        """))
        
        # Recreate foreign keys
        session.execute(text("""
            ALTER TABLE labs.researchers ADD CONSTRAINT researchers_lab_id_fkey 
                FOREIGN KEY (lab_id) REFERENCES labs.labs(id);
            ALTER TABLE labs.collaborations ADD CONSTRAINT collaborations_lab_id_fkey 
                FOREIGN KEY (lab_id) REFERENCES labs.labs(id);
            ALTER TABLE labs.collaborations ADD CONSTRAINT collaborations_researcher_id_fkey 
                FOREIGN KEY (researcher_id) REFERENCES labs.researchers(id);
        """))
        
        session.commit()
        logger.info("✅ Successfully converted all IDs to UUID")
        
    except Exception as e:
        logger.error(f"❌ Error during migration: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()


def main():
    """Run migration"""
    logger.info("🔄 Starting Labs UUID migration...")
    migrate_to_uuid()


if __name__ == "__main__":
    main()
