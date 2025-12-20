"""
Database cleanup script for Orchestrator service
Removes all records from all tables
"""
import asyncio
import logging
from sqlalchemy import text
from database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def cleanup_database():
    """Delete all records from all tables"""
    async with AsyncSessionLocal() as session:
        try:
            # Get all tables
            result = await session.execute(
                text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema='public' AND table_type='BASE TABLE'
                """)
            )
            
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"Found {len(tables)} tables: {tables}")
            
            # Disable foreign key constraints temporarily
            await session.execute(text("SET session_replication_role = 'replica'"))
            
            # Delete all records from each table
            for table in tables:
                try:
                    await session.execute(text(f"DELETE FROM {table}"))
                    logger.info(f"✅ Cleared table: {table}")
                except Exception as e:
                    logger.warning(f"⚠️  Could not clear table {table}: {str(e)}")
            
            # Re-enable foreign key constraints
            await session.execute(text("SET session_replication_role = 'origin'"))
            
            await session.commit()
            logger.info("✅ Database cleanup completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {str(e)}")
            await session.rollback()
            raise


async def main():
    """Run cleanup"""
    logger.info("🔄 Starting Orchestrator database cleanup...")
    await cleanup_database()


if __name__ == "__main__":
    asyncio.run(main())
