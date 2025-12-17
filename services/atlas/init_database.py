#!/usr/bin/env python3
"""
Initialize fresh database with all tables
"""

import asyncio
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config.database import engine
from app.models.user import Base
from app.models.project import Project
from app.models.epic import Epic
from app.models.story import Story
from app.models.task import Task
from app.models.notification import Notification
from app.models.message import Message, Channel, ChannelMember, UserPresence
from app.models.issue import Issue
from app.models.organization import Organization, OrganizationMember

async def init_db():
    """Create all tables"""
    print("🔄 Initializing database...")
    
    async with engine.begin() as conn:
        # Drop all tables (fresh start)
        print("🗑️  Dropping existing tables...")
        await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables
        print("📋 Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database initialized successfully!")
    print("\n📊 Tables created:")
    print("  - users")
    print("  - organizations")
    print("  - organization_members")
    print("  - projects")
    print("  - epics")
    print("  - stories")
    print("  - tasks")
    print("  - notifications")
    print("  - messages")
    print("  - channels")
    print("  - channel_members")
    print("  - user_presence")
    print("  - issues")

if __name__ == "__main__":
    asyncio.run(init_db())
