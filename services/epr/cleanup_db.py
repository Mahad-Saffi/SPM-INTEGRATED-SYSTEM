"""
Database cleanup script for EPR service
Removes all records from all tables
"""
import logging
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://paperless:paperless@localhost:5432/project_management"
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"options": "-c search_path=performance,public"}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def cleanup_database():
    """Delete all records from all tables"""
    session = SessionLocal()
    try:
        # Get all tables
        result = session.execute(
            text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema='performance' AND table_type='BASE TABLE'
            """)
        )
        
        tables = [row[0] for row in result.fetchall()]
        logger.info(f"Found {len(tables)} tables: {tables}")
        
        # Disable foreign key constraints temporarily
        session.execute(text("SET session_replication_role = 'replica'"))
        
        # Delete all records from each table
        for table in tables:
            try:
                session.execute(text(f"DELETE FROM performance.{table}"))
                logger.info(f"✅ Cleared table: {table}")
            except Exception as e:
                logger.warning(f"⚠️  Could not clear table {table}: {str(e)}")
        
        # Re-enable foreign key constraints
        session.execute(text("SET session_replication_role = 'origin'"))
        
        session.commit()
        logger.info("✅ Database cleanup completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()


def main():
    """Run cleanup"""
    logger.info("🔄 Starting EPR database cleanup...")
    cleanup_database()


if __name__ == "__main__":
    main()
