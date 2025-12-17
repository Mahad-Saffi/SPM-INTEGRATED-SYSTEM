"""
Projects router - proxy requests to Atlas service
"""
from fastapi import APIRouter, Depends
from typing import List, Dict, Any

from auth.jwt_handler import get_current_user
from services.atlas_client import atlas_client

router = APIRouter(prefix="/api/v1/projects", tags=["Projects"])


@router.get("/")
async def get_user_projects(current_user = Depends(get_current_user)):
    """Get all projects for current user"""
    return await atlas_client.get_user_projects(current_user["sub"])


@router.get("/{project_id}/tasks")
async def get_project_tasks(project_id: str, current_user = Depends(get_current_user)):
    """Get tasks for a project"""
    return await atlas_client.get_project_tasks(project_id)


@router.get("/{project_id}/issues")
async def get_project_issues(project_id: str, current_user = Depends(get_current_user)):
    """Get issues for a project"""
    return await atlas_client.get_issues(project_id)


@router.post("/tasks")
async def create_task(task_data: Dict[str, Any], current_user = Depends(get_current_user)):
    """Create a new task"""
    task_data["created_by"] = current_user["sub"]
    return await atlas_client.create_task(task_data)
