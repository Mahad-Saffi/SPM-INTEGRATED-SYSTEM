"""
Database migration script for Orchestrator service
Adds invitations table
"""
import asyncio
import logging
from sqlalchemy import text
from database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_create_invitations_table():
    """Create invitations table"""
    async with AsyncSessionLocal() as session:
        try:
            # Check if invitations table exists
            result = await session.execute(
                text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'invitations'
                    )
                """)
            )
            
            if result.scalar():
                logger.info("✅ invitations table already exists")
                return
            
            # Create invitations table
            await session.execute(
                text("""
                    CREATE TABLE invitations (
                        id VARCHAR(50) PRIMARY KEY,
                        email VARCHAR(255) NOT NULL,
                        organization_id VARCHAR(50) NOT NULL REFERENCES organizations(id),
                        role VARCHAR(50) DEFAULT 'member',
                        status VARCHAR(20) DEFAULT 'pending',
                        invited_by VARCHAR(50) NOT NULL REFERENCES users(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            )
            
            # Create index on email and status for faster queries
            await session.execute(
                text("""
                    CREATE INDEX idx_invitations_email_status 
                    ON invitations(email, status)
                """)
            )
            
            await session.commit()
            logger.info("✅ Successfully created invitations table")
            
        except Exception as e:
            logger.error(f"❌ Error creating invitations table: {str(e)}")
            await session.rollback()
            raise


async def main():
    """Run migration"""
    logger.info("🔄 Starting Orchestrator database migration...")
    await migrate_create_invitations_table()
    logger.info("✅ Migration completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
