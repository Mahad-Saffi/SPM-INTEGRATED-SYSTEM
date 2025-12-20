"""
Database migration script for Labs service
Adds email, status, created_at, and updated_at columns to researchers table
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


def migrate_researcher_columns():
    """Add email, status, created_at, updated_at columns to researchers table"""
    session = SessionLocal()
    try:
        # Check if email column exists
        result = session.execute(
            text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema='labs' AND table_name='researchers' AND column_name='email'
            """)
        )
        
        if result.fetchone():
            logger.info("✅ email column already exists")
        else:
            session.execute(
                text("""
                    ALTER TABLE labs.researchers 
                    ADD COLUMN email VARCHAR UNIQUE NOT NULL DEFAULT 'unknown@labs.local'
                """)
            )
            logger.info("✅ Added email column")
        
        # Check if status column exists
        result = session.execute(
            text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema='labs' AND table_name='researchers' AND column_name='status'
            """)
        )
        
        if result.fetchone():
            logger.info("✅ status column already exists")
        else:
            session.execute(
                text("""
                    ALTER TABLE labs.researchers 
                    ADD COLUMN status VARCHAR DEFAULT 'pending'
                """)
            )
            logger.info("✅ Added status column")
        
        # Check if created_at column exists
        result = session.execute(
            text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema='labs' AND table_name='researchers' AND column_name='created_at'
            """)
        )
        
        if result.fetchone():
            logger.info("✅ created_at column already exists")
        else:
            session.execute(
                text("""
                    ALTER TABLE labs.researchers 
                    ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """)
            )
            logger.info("✅ Added created_at column")
        
        # Check if updated_at column exists
        result = session.execute(
            text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema='labs' AND table_name='researchers' AND column_name='updated_at'
            """)
        )
        
        if result.fetchone():
            logger.info("✅ updated_at column already exists")
        else:
            session.execute(
                text("""
                    ALTER TABLE labs.researchers 
                    ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """)
            )
            logger.info("✅ Added updated_at column")
        
        session.commit()
        logger.info("✅ All migrations completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error during migration: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()


def main():
    """Run migration"""
    logger.info("🔄 Starting Labs researcher columns migration...")
    migrate_researcher_columns()


if __name__ == "__main__":
    main()
