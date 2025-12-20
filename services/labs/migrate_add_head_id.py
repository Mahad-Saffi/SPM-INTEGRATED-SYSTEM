"""
Database migration script for Labs service
Adds head_id column to labs table
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


def migrate_add_head_id():
    """Add head_id column to labs table if it doesn't exist"""
    session = SessionLocal()
    try:
        # Check if head_id column already exists
        result = session.execute(
            text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema='labs' AND table_name='labs' AND column_name='head_id'
            """)
        )
        
        if result.fetchone():
            logger.info("✅ head_id column already exists in labs table")
            return
        
        # Add head_id column with foreign key
        session.execute(
            text("""
                ALTER TABLE labs.labs 
                ADD COLUMN head_id INTEGER REFERENCES labs.users(id)
            """)
        )
        session.commit()
        logger.info("✅ Successfully added head_id column to labs table")
        
    except Exception as e:
        logger.error(f"❌ Error adding head_id column: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()


def main():
    """Run migration"""
    logger.info("🔄 Starting Labs database migration...")
    migrate_add_head_id()
    logger.info("✅ Migration completed successfully")


if __name__ == "__main__":
    main()
