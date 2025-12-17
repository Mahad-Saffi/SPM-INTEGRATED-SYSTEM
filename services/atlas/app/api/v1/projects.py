from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.core.security import get_current_user
from app.services.task_service import task_service
from app.services.project_service import project_service
from app.services.risk_service import risk_service
from typing import Optional
from datetime import datetime

router = APIRouter()

class TaskUpdateRequest(BaseModel):
    estimate_hours: Optional[int] = None
    progress_percentage: Optional[int] = None
    due_date: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[int] = None

class BulkTaskAssignRequest(BaseModel):
    task_ids: list[str]
    assigned_to: int

@router.get("")
async def get_user_projects(current_user: dict = Depends(get_current_user)):
    """Get all projects for the current user"""
    projects = await project_service.get_user_projects(current_user['id'])
    return projects

@router.get("/{project_id}/tasks")
async def get_project_tasks(project_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user['id']
    tasks = await task_service.get_tasks_for_user_in_project(project_id, user_id)
    return tasks

@router.get("/{project_id}/risks")
async def get_project_risks(project_id: str, current_user: dict = Depends(get_current_user)):
    """Get risk summary for a project"""
    risks = await risk_service.get_project_risks(project_id)
    return risks

@router.post("/tasks/{task_id}/complete")
async def complete_task(task_id: str, current_user: dict = Depends(get_current_user)):
    """Mark a task as complete and trigger automated task assignment"""
    task = await task_service.complete_task(task_id, current_user['id'])
    return {"message": "Task completed successfully", "task": task}

@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: str,
    update: TaskUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update task estimate, progress, or due date"""
    task = await task_service.update_task_details(task_id, update.dict(exclude_none=True))
    return {"message": "Task updated successfully", "task": task}

@router.post("/tasks/bulk-assign")
async def bulk_assign_tasks(
    request: BulkTaskAssignRequest,
    current_user: dict = Depends(get_current_user)
):
    """Assign multiple tasks to a user at once"""
    results = await task_service.bulk_assign_tasks(request.task_ids, request.assigned_to)
    return {
        "message": f"Successfully assigned {results['success_count']} tasks",
        "success_count": results['success_count'],
        "failed_count": results['failed_count'],
        "failed_tasks": results['failed_tasks']
    }

@router.post("/detect-delays")
async def detect_delays(current_user: dict = Depends(get_current_user)):
    """Manually trigger delay detection (normally runs on schedule)"""
    result = await risk_service.detect_delays_and_update_risks()
    return result

@router.get("/{project_id}/epics")
async def get_project_epics(project_id: str, current_user: dict = Depends(get_current_user)):
    """Get all epics with stories and tasks for a project"""
    epics = await project_service.get_project_epics(project_id)
    return epics
