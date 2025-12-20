#!/usr/bin/env python3
"""
Initialize all databases with schema
Run this after Docker containers are up and healthy
"""
import asyncio
import sys
from pathlib import Path
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Override the config to use localhost instead of postgres
os.environ['DB_HOST'] = 'localhost'

from config_loader import get_config
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

config = get_config()


async def init_database(db_name: str, db_url: str) -> bool:
    """Initialize a single database"""
    try:
        print(f"\n{'='*60}")
        print(f"Initializing {db_name} database...")
        print(f"{'='*60}")
        
        # Create async engine
        engine = create_async_engine(db_url, echo=False)
        
        # Test connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"✅ Connected to {db_name}")
        
        # Import models based on service
        if db_name == "project_management":
            sys.path.insert(0, str(Path(__file__).parent / "services" / "orchestrator"))
            from database import Base
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print(f"✅ Created tables in {db_name}")
        
        elif db_name == "atlas":
            sys.path.insert(0, str(Path(__file__).parent / "services" / "atlas"))
            from app.models import Base
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print(f"✅ Created tables in {db_name}")
        
        elif db_name == "workpulse":
            sys.path.insert(0, str(Path(__file__).parent / "services" / "workpulse"))
            from app.models import Base
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print(f"✅ Created tables in {db_name}")
        
        elif db_name == "epr":
            sys.path.insert(0, str(Path(__file__).parent / "services" / "epr"))
            from api.models import Base
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print(f"✅ Created tables in {db_name}")
        
        elif db_name == "labs":
            sys.path.insert(0, str(Path(__file__).parent / "services" / "labs"))
            from app.models import Base
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print(f"✅ Created tables in {db_name}")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Error initializing {db_name}: {e}")
        return False


async def main():
    """Initialize all databases"""
    print("\n" + "="*60)
    print("PROJECT MANAGEMENT SYSTEM - DATABASE INITIALIZATION")
    print("="*60)
    
    databases = [
        ("project_management", config.DATABASE_URL.replace("@postgres", "@localhost")),
        ("atlas", config.atlas_database_url.replace("@postgres", "@localhost")),
        ("workpulse", config.workpulse_database_url.replace("@postgres", "@localhost")),
        ("epr", config.epr_database_url.replace("@postgres", "@localhost")),
        ("labs", config.labs_database_url.replace("@postgres", "@localhost")),
    ]
    
    results = []
    for db_name, db_url in databases:
        success = await init_database(db_name, db_url)
        results.append((db_name, success))
    
    # Summary
    print("\n" + "="*60)
    print("INITIALIZATION SUMMARY")
    print("="*60)
    
    for db_name, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{db_name:25} {status}")
    
    all_success = all(success for _, success in results)
    
    if all_success:
        print("\n✅ All databases initialized successfully!")
        print("\nNext steps:")
        print("1. Run tests: python COMPREHENSIVE_TEST_FLOW.py")
        print("2. Access services:")
        print("   - Orchestrator: http://localhost:9000")
        print("   - Atlas: http://localhost:8000")
        print("   - WorkPulse: http://localhost:8001")
        print("   - EPR: http://localhost:8003")
        print("   - Labs: http://localhost:8004")
        return 0
    else:
        print("\n❌ Some databases failed to initialize")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
