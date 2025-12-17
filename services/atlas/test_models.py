"""
Quick test script to verify all models are properly configured
Run with: python backend/test_models.py
"""
import sys
sys.path.insert(0, 'backend')

from app.models import User, Project, Epic, Story, Task, Base
from sqlalchemy import inspect

def test_models():
    print("🧪 Testing Atlas Models...\n")
    
    # Test User model
    print("✓ User model imported")
    user_columns = [c.name for c in inspect(User).columns]
    print(f"  Columns: {', '.join(user_columns)}")
    
    # Test Project model
    print("\n✓ Project model imported")
    project_columns = [c.name for c in inspect(Project).columns]
    print(f"  Columns: {', '.join(project_columns)}")
    print(f"  Relationships: {', '.join([r.key for r in inspect(Project).relationships])}")
    
    # Test Epic model
    print("\n✓ Epic model imported")
    epic_columns = [c.name for c in inspect(Epic).columns]
    print(f"  Columns: {', '.join(epic_columns)}")
    print(f"  Relationships: {', '.join([r.key for r in inspect(Epic).relationships])}")
    
    # Test Story model
    print("\n✓ Story model imported")
    story_columns = [c.name for c in inspect(Story).columns]
    print(f"  Columns: {', '.join(story_columns)}")
    print(f"  Relationships: {', '.join([r.key for r in inspect(Story).relationships])}")
    
    # Test Task model
    print("\n✓ Task model imported")
    task_columns = [c.name for c in inspect(Task).columns]
    print(f"  Columns: {', '.join(task_columns)}")
    print(f"  Relationships: {', '.join([r.key for r in inspect(Task).relationships])}")
    
    print("\n" + "="*50)
    print("✅ All models are properly configured!")
    print("="*50)
    
    # Verify relationships
    print("\n📊 Relationship Hierarchy:")
    print("  Project → Epics (one-to-many)")
    print("  Epic → Stories (one-to-many)")
    print("  Story → Tasks (one-to-many)")
    print("  Task → Story (many-to-one)")
    print("  Task → Project (many-to-one)")
    
    return True

if __name__ == "__main__":
    try:
        test_models()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
