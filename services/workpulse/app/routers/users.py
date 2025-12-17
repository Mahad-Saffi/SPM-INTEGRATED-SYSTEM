"""
User sync endpoint for WorkPulse
Allows orchestrator to create users
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid

from app.database import get_db
from app.models import User

router = APIRouter(prefix="/api/v1/users", tags=["users"])


class UserSync(BaseModel):
    orchestrator_user_id: str
    email: str
    name: str


@router.post("/sync")
async def sync_user(user_data: UserSync, db: Session = Depends(get_db)):
    """Create or update user from orchestrator"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        User.orchestrator_user_id == user_data.orchestrator_user_id
    ).first()
    
    if existing_user:
        # Update existing user
        existing_user.email = user_data.email
        existing_user.name = user_data.name
        db.commit()
        return {"status": "updated", "user_id": existing_user.id}
    
    # Create new user
    new_user = User(
        id=user_data.orchestrator_user_id,
        orchestrator_user_id=uuid.UUID(user_data.orchestrator_user_id),
        email=user_data.email,
        name=user_data.name
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"status": "created", "user_id": new_user.id}
