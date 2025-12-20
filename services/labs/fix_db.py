"""
Fix Labs database - create schema and tables properly
"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:secure_password@localhost:5432/project_management"
)

def fix_database():
    """Create labs schema and all tables"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Create schema
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS labs"))
        conn.commit()
        print("✅ Schema 'labs' created/verified")
        
        # Check existing tables in labs schema
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'labs'
        """))
        existing_tables = [row[0] for row in result]
        print(f"📋 Existing tables in labs schema: {existing_tables}")
        
        # Check if users table exists in public schema (might be there by mistake)
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'users'
        """))
        public_users = [row[0] for row in result]
        if public_users:
            print(f"⚠️  Found 'users' table in public schema")
        
        # Create users table in labs schema if not exists
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS labs.users (
                id SERIAL PRIMARY KEY,
                orchestrator_user_id UUID UNIQUE,
                name VARCHAR NOT NULL,
                email VARCHAR UNIQUE NOT NULL,
                hashed_password VARCHAR NOT NULL,
                is_active BOOLEAN DEFAULT TRUE
            )
        """))
        conn.commit()
        print("✅ Created/verified labs.users table")
        
        # Create labs table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS labs.labs (
                id SERIAL PRIMARY KEY,
                orchestrator_org_id UUID,
                name VARCHAR NOT NULL,
                domain VARCHAR,
                description VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
        print("✅ Created/verified labs.labs table")
        
        # Create researchers table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS labs.researchers (
                id SERIAL PRIMARY KEY,
                orchestrator_user_id UUID,
                name VARCHAR NOT NULL,
                field VARCHAR,
                lab_id INTEGER REFERENCES labs.labs(id)
            )
        """))
        conn.commit()
        print("✅ Created/verified labs.researchers table")
        
        # Create collaborations table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS labs.collaborations (
                id SERIAL PRIMARY KEY,
                lab_id INTEGER REFERENCES labs.labs(id),
                researcher_id INTEGER REFERENCES labs.researchers(id),
                title VARCHAR NOT NULL,
                description VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
        print("✅ Created/verified labs.collaborations table")
        
        # Verify all tables
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'labs'
        """))
        tables = [row[0] for row in result]
        print(f"\n📋 Final tables in labs schema: {tables}")

if __name__ == "__main__":
    print("🔧 Fixing Labs database...")
    fix_database()
    print("\n✅ Database fix complete!")
