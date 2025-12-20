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


@router.get("/user/{user_id}/projects")
async def get_user_projects(
    user_id: str,
    _: bool = Depends(verify_service_token)
):
    """Get all projects for a user (internal endpoint)"""
    try:
        from app.services.project_service import project_service
        from app.models.user import User
        
        async with SessionLocal() as session:
            # Find user by orchestrator_user_id
            result = await session.execute(
                select(User).where(User.orchestrator_user_id == uuid.UUID(user_id))
            )
            user = result.scalars().first()
            
            if not user:
                return []
            
            projects = await project_service.get_user_projects(user.id)
            return projects
            
    except Exception as e:
        logger.error(f"Error getting user projects: {str(e)}")
        return []


@router.get("/user/{user_id}/tasks")
async def get_user_tasks(
    user_id: str,
    _: bool = Depends(verify_service_token)
):
    """Get all tasks for a user (internal endpoint)"""
    try:
        from app.services.task_service import task_service
        from app.models.user import User
        
        async with SessionLocal() as session:
            # Find user by orchestrator_user_id
            result = await session.execute(
                select(User).where(User.orchestrator_user_id == uuid.UUID(user_id))
            )
            user = result.scalars().first()
            
            if not user:
                return []
            
            tasks = await task_service.get_user_tasks(user.id)
            return tasks
            
    except Exception as e:
        logger.error(f"Error getting user tasks: {str(e)}")
        return []


@router.post("/tasks")
async def create_task_internal(
    task_data: dict,
    _: bool = Depends(verify_service_token)
):
    """Create a task (internal endpoint)"""
    try:
        from app.services.task_service import task_service
        
        task = await task_service.create_task(task_data)
        return task
            
    except Exception as e:
        logger.error(f"Error creating task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.get("/user/{user_id}/organizations")
async def get_user_organizations(
    user_id: str,
    _: bool = Depends(verify_service_token)
):
    """Get organizations for a user (internal endpoint)"""
    try:
        from app.models.user import User
        from app.models.organization import Organization
        
        async with SessionLocal() as session:
            # Find user by orchestrator_user_id
            result = await session.execute(
                select(User).where(User.orchestrator_user_id == uuid.UUID(user_id))
            )
            user = result.scalars().first()
            
            if not user:
                return []
            
            # Get user's organization
            if user.organization_id:
                org_result = await session.execute(
                    select(Organization).where(Organization.id == user.organization_id)
                )
                org = org_result.scalars().first()
                if org:
                    return [{
                        "id": org.id,
                        "name": org.name,
                        "description": org.description
                    }]
            
            return []
            
    except Exception as e:
        logger.error(f"Error getting user organizations: {str(e)}")
        return []


class ProjectCreateRequest(BaseModel):
    name: str
    description: str = ""
    owner_id: str
    organization_id: str
    lab_id: int = None


@router.post("/projects")
async def create_project_internal(
    project_data: ProjectCreateRequest,
    _: bool = Depends(verify_service_token)
):
    """Create a project (internal endpoint)"""
    try:
        from app.services.project_service import project_service
        
        project = await project_service.create_project(
            name=project_data.name,
            description=project_data.description,
            owner_id=project_data.owner_id,
            organization_id=project_data.organization_id,
            lab_id=project_data.lab_id
        )
        return project
            
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")
