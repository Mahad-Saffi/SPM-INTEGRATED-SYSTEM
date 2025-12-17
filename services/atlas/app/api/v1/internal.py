from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, EmailStr
from sqlalchemy.future import select
from app.models.user import User
from app.config.database import SessionLocal
import os
import logging
import uuid

router = APIRouter()
logger = logging.getLogger(__name__)

SERVICE_SECRET = os.getenv("SERVICE_SECRET", "shared-secret-token")

class UserSync(BaseModel):
    id: str  # orchestrator user ID
    email: EmailStr
    name: str
    role: str = "developer"

def verify_service_token(x_service_token: str = Header(...)):
    """Verify the service authentication token"""
    if x_service_token != SERVICE_SECRET:
        raise HTTPException(status_code=401, detail="Invalid service token")
    return True

@router.post("/users/sync")
async def sync_user(
    user_data: UserSync,
    _: bool = Depends(verify_service_token)
):
    """
    Sync user from orchestrator to Atlas service.
    This endpoint is called by the orchestrator when a new user registers.
    """
    try:
        async with SessionLocal() as session:
            # Check if user already exists
            result = await session.execute(
                select(User).where(User.orchestrator_user_id == uuid.UUID(user_data.id))
            )
            existing_user = result.scalars().first()
            
            if existing_user:
                # Update existing user
                existing_user.email = user_data.email
                existing_user.username = user_data.name
                existing_user.role = user_data.role
                await session.commit()
                await session.refresh(existing_user)
                
                logger.info(f"Updated user {user_data.email} in Atlas")
                return {
                    "status": "updated",
                    "user_id": existing_user.id,
                    "orchestrator_user_id": str(existing_user.orchestrator_user_id)
                }
            
            # Create new user
            new_user = User(
                orchestrator_user_id=uuid.UUID(user_data.id),
                username=user_data.name,
                email=user_data.email,
                role=user_data.role,
                password_hash="",  # Synced users don't need password (auth via orchestrator)
                is_active=True
            )
            
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            
            logger.info(f"Created user {user_data.email} in Atlas")
            return {
                "status": "created",
                "user_id": new_user.id,
                "orchestrator_user_id": str(new_user.orchestrator_user_id)
            }
            
    except Exception as e:
        logger.error(f"Error syncing user to Atlas: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to sync user: {str(e)}")
