#!/usr/bin/env python3
"""
Database migration script to add organization support
"""

import sqlite3
import sys

def migrate_database(db_path='backend/atlas.db'):
    """Add organization tables and columns"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔄 Starting database migration...")
    
    try:
        # 1. Create organizations table
        print("📋 Creating organizations table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS organizations (
                id TEXT PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                owner_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users(id)
            )
        ''')
        print("✅ Organizations table created")
        
        # 2. Create organization_members table
        print("📋 Creating organization_members table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS organization_members (
                id TEXT PRIMARY KEY,
                organization_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                role VARCHAR(50) NOT NULL,
                description TEXT,
                invited_by INTEGER NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (organization_id) REFERENCES organizations(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (invited_by) REFERENCES users(id)
            )
        ''')
        print("✅ Organization_members table created")
        
        # 3. Add invited_by column to users table
        print("📋 Adding invited_by column to users table...")
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN invited_by INTEGER')
            print("✅ invited_by column added to users")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("⚠️  invited_by column already exists")
            else:
                raise
        
        # 4. Add organization_id column to projects table
        print("📋 Adding organization_id column to projects table...")
        try:
            cursor.execute('ALTER TABLE projects ADD COLUMN organization_id TEXT')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_organization ON projects(organization_id)')
            print("✅ organization_id column added to projects")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("⚠️  organization_id column already exists")
            else:
                raise
        
        # Commit changes
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("\n📝 Next steps:")
        print("1. Restart the backend server")
        print("2. New users will automatically get an organization")
        print("3. Existing users need to create an organization manually")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
