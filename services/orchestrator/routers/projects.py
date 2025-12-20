"""
Projects router - proxy requests to Atlas service
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel
from uuid import UUID

from auth.jwt_handler import get_current_user
from middleware.permissions import (
    require_manager,
    check_org_membership,
    check_same_org,
    check_not_self,
    check_ownership,
    validate_task_assignment
)
from services.atlas_client import atlas_client
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/projects", tags=["Projects"])


class ProjectCreate(BaseModel):
    """Schema for creating a project"""
    name: str
    description: Optional[str] = None
    lab_id: Optional[UUID] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Mobile App",
                "description": "New mobile application",
                "lab_id": None
            }
        }


class ProjectUpdate(BaseModel):
    """Schema for updating a project"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class TaskCreate(BaseModel):
    """Schema for creating a task"""
    title: str
    description: Optional[str] = None
    assignee_id: Optional[UUID] = None
    due_date: Optional[str] = None
    status: str = "To Do"
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Design UI",
                "description": "Design the user interface",
                "assignee_id": None,
                "due_date": "2025-12-31",
                "status": "To Do"
            }
        }


class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    progress_percentage: Optional[int] = None
    assignee_id: Optional[UUID] = None


@router.post("/")
async def create_project(
    project_data: ProjectCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new project"""
    
    # Check role
    if current_user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admin or manager can create projects")
    
    # Check organization membership
    org_id = check_org_membership(current_user)
    
    # Call atlas service
    try:
        return await atlas_client.create_project({
            "name": project_data.name,
            "description": project_data.description,
            "owner_id": current_user.get("sub"),
            "organization_id": org_id,
            "lab_id": str(project_data.lab_id) if project_data.lab_id else None
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def get_projects(
    lab_id: Optional[UUID] = None,
    current_user = Depends(get_current_user)
):
    """Get projects in user's organization"""
    
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    try:
        return await atlas_client.get_projects(
            org_id=org_id,
            lab_id=str(lab_id) if lab_id else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}")
async def get_project(
    project_id: UUID,
    current_user = Depends(get_current_user)
):
    """Get project details"""
    
    try:
        project = await atlas_client.get_project(str(project_id))
        
        # Check organization isolation
        check_same_org(current_user, project.get("organization_id"))
        
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{project_id}")
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    current_user = Depends(get_current_user)
):
    """Update project"""
    
    try:
        project = await atlas_client.get_project(str(project_id))
        
        # Check organization isolation
        check_same_org(current_user, project.get("organization_id"))
        
        # Check ownership
        check_ownership(current_user, project.get("owner_id"), "project")
        
        return await atlas_client.update_project(
            str(project_id),
            project_data.dict(exclude_unset=True)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/tasks")
async def create_task(
    project_id: UUID,
    task_data: TaskCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create task in project"""
    
    # Check role
    if current_user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admin or manager can create tasks")
    
    try:
        project = await atlas_client.get_project(str(project_id))
        
        # Check organization isolation
        check_same_org(current_user, project.get("organization_id"))
        
        # Validate task assignment if assignee provided
        if task_data.assignee_id:
            await validate_task_assignment(
                db,
                str(project_id),
                str(task_data.assignee_id),
                current_user
            )
        
        return await atlas_client.create_task(str(project_id), {
            "title": task_data.title,
            "description": task_data.description,
            "assignee_id": str(task_data.assignee_id) if task_data.assignee_id else None,
            "created_by": current_user.get("sub"),
            "due_date": task_data.due_date,
            "status": task_data.status
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/tasks")
async def get_project_tasks(
    project_id: UUID,
    current_user = Depends(get_current_user)
):
    """Get project tasks"""
    
    try:
        project = await atlas_client.get_project(str(project_id))
        
        # Verify user is in same organization
        if project.get("organization_id") != current_user.get("organization_id"):
            if current_user.get("role") != "admin":
                raise HTTPException(status_code=403, detail="Access denied")
        
        return await atlas_client.get_project_tasks(str(project_id))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: UUID,
    task_data: TaskUpdate,
    current_user = Depends(get_current_user)
):
    """Update task"""
    
    try:
        task = await atlas_client.get_task(str(task_id))
        
        # Verify user is assignee or creator or admin/manager
        is_assignee = task.get("assignee_id") == current_user.get("sub")
        is_creator = task.get("created_by") == current_user.get("sub")
        is_manager = current_user.get("role") in ["admin", "manager"]
        
        if not (is_assignee or is_creator or is_manager):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return await atlas_client.update_task(
            str(task_id),
            task_data.dict(exclude_unset=True)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
