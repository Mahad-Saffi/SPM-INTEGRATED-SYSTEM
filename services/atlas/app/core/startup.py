"""
Startup checks and database initialization
"""
from sqlalchemy import inspect, text
from app.config.database import engine, SessionLocal
from app.models.user import Base
import logging

logger = logging.getLogger(__name__)

async def check_database_schema():
    """Check if database schema is up to date"""
    try:
        async with engine.begin() as conn:
            # Check if tables exist
            def check_tables(connection):
                inspector = inspect(connection)
                return inspector.get_table_names()
            
            tables = await conn.run_sync(check_tables)
            
            if not tables:
                logger.info("No tables found. Creating database schema...")
                await conn.run_sync(Base.metadata.create_all)
                logger.info("✅ Database schema created successfully")
                return True
            
            # Check if users table has password_hash column and github_id is nullable
            def check_columns(connection):
                inspector = inspect(connection)
                if 'users' in inspector.get_table_names():
                    columns = inspector.get_columns('users')
                    return columns
                return []
            
            columns = await conn.run_sync(check_columns)
            column_names = [col['name'] for col in columns]
            
            # Check if schema needs updates
            needs_migration = False
            
            if 'users' in tables:
                # Check if password_hash column exists
                if 'password_hash' not in column_names:
                    logger.warning("⚠️  Adding password_hash column...")
                    await conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
                    needs_migration = True
                
                # Check if github_id is nullable (we need to recreate table for SQLite)
                github_id_col = next((col for col in columns if col['name'] == 'github_id'), None)
                if github_id_col and not github_id_col.get('nullable', True):
                    logger.warning("⚠️  Migrating users table to make github_id nullable...")
                    # For SQLite, we need to recreate the table
                    await conn.execute(text("""
                        CREATE TABLE users_new (
                            id INTEGER PRIMARY KEY,
                            github_id VARCHAR(50) UNIQUE,
                            username VARCHAR(100) NOT NULL UNIQUE,
                            email VARCHAR(255) UNIQUE NOT NULL,
                            password_hash VARCHAR(255),
                            avatar_url VARCHAR(500),
                            role VARCHAR(50) NOT NULL DEFAULT 'developer',
                            is_active BOOLEAN DEFAULT 1,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP
                        )
                    """))
                    
                    # Copy data from old table
                    await conn.execute(text("""
                        INSERT INTO users_new (id, github_id, username, email, password_hash, avatar_url, role, is_active, created_at, updated_at)
                        SELECT id, github_id, username, email, password_hash, avatar_url, role, is_active, created_at, updated_at
                        FROM users
                    """))
                    
                    # Drop old table and rename new one
                    await conn.execute(text("DROP TABLE users"))
                    await conn.execute(text("ALTER TABLE users_new RENAME TO users"))
                    
                    # Recreate indexes
                    await conn.execute(text("CREATE INDEX ix_users_id ON users (id)"))
                    await conn.execute(text("CREATE UNIQUE INDEX ix_users_github_id ON users (github_id)"))
                    await conn.execute(text("CREATE INDEX ix_users_username ON users (username)"))
                    await conn.execute(text("CREATE UNIQUE INDEX ix_users_email ON users (email)"))
                    
                    needs_migration = True
                
                if needs_migration:
                    await conn.commit()
                    logger.info("✅ Database schema migrated successfully")
            
            logger.info(f"✅ Database check passed. Tables: {', '.join(tables)}")
            return True
            
    except Exception as e:
        logger.error(f"❌ Database check failed: {e}")
        return False

async def verify_database_connection():
    """Verify database connection is working"""
    try:
        async with SessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            logger.info("✅ Database connection verified")
            return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

async def startup_checks():
    """Run all startup checks"""
    logger.info("🚀 Running startup checks...")
    
    # Check database connection
    if not await verify_database_connection():
        raise Exception("Database connection failed")
    
    # Check database schema
    if not await check_database_schema():
        raise Exception("Database schema check failed")
    
    logger.info("✅ All startup checks passed!")
    return True
