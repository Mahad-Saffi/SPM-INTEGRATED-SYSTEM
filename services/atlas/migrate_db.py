"""
Database migration script for Atlas service
Adds lab_id column to projects table
"""
import asyncio
import logging
from sqlalchemy import text
from app.config.database import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_add_lab_id():
    """Add lab_id column to projects table if it doesn't exist"""
    async with SessionLocal() as session:
        try:
            # Check if lab_id column already exists
            result = await session.execute(
                text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='projects' AND column_name='lab_id'
                """)
            )
            
            if result.fetchone():
                logger.info("✅ lab_id column already exists in projects table")
                return
            
            # Add lab_id column
            await session.execute(
                text("ALTER TABLE projects ADD COLUMN lab_id INTEGER")
            )
            await session.commit()
            logger.info("✅ Successfully added lab_id column to projects table")
            
        except Exception as e:
            logger.error(f"❌ Error adding lab_id column: {str(e)}")
            await session.rollback()
            raise


async def main():
    """Run all migrations"""
    logger.info("🔄 Starting Atlas database migrations...")
    
    try:
        await migrate_add_lab_id()
        logger.info("✅ All migrations completed successfully")
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
