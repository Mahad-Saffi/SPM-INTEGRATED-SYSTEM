"""
Task Management API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
from api.database import get_db
from api.models import Task
from api.dependencies import verify_atlas_token
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])

class TaskCreate(BaseModel):
    title: str
    description: str = None
    status: str = "pending"
    priority: str = "medium"
    assigned_to: str = None
    project_id: int = None
    due_date: datetime = None
    created_by: str = None

class TaskUpdate(BaseModel):
    title: str = None
    description: str = None
    status: str = None
    priority: str = None
    assigned_to: str = None
    project_id: int = None
    due_date: datetime = None

def task_to_dict(task: Task) -> Dict[str, Any]:
    """Convert Task model to dict"""
    return {
        "id": str(task.id),
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "assigned_to": task.assigned_to,
        "project_id": str(task.project_id) if task.project_id else None,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "created_by": task.created_by
    }

@router.get("", response_model=List[Dict[str, Any]])
async def get_tasks(
    employee_id: Optional[str] = Query(None, description="Filter by employee ID"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Get all tasks, optionally filtered by employee"""
    query = db.query(Task)
    if employee_id:
        query = query.filter(Task.assigned_to == employee_id)
    tasks = query.all()
    return [task_to_dict(task) for task in tasks]

@router.get("/{task_id}", response_model=Dict[str, Any])
async def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Get task by ID"""
    try:
        t_id = int(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID")
    
    task = db.query(Task).filter(Task.id == t_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task_to_dict(task)

@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Create new task"""
    user_id = str(current_user.get("user_id", current_user.get("id", "")))
    
    db_task = Task(
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        assigned_to=task.assigned_to,
        project_id=task.project_id,
        due_date=task.due_date,
        created_by=task.created_by or user_id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return task_to_dict(db_task)

@router.put("/{task_id}", response_model=Dict[str, Any])
async def update_task(
    task_id: str,
    task: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Update task"""
    try:
        t_id = int(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID")
    
    db_task = db.query(Task).filter(Task.id == t_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.title is not None:
        db_task.title = task.title
    if task.description is not None:
        db_task.description = task.description
    if task.status is not None:
        db_task.status = task.status
        if task.status == "completed" and not db_task.completed_at:
            db_task.completed_at = datetime.utcnow()
    if task.priority is not None:
        db_task.priority = task.priority
    if task.assigned_to is not None:
        db_task.assigned_to = task.assigned_to
    if task.project_id is not None:
        db_task.project_id = task.project_id
    if task.due_date is not None:
        db_task.due_date = task.due_date
    
    db.commit()
    db.refresh(db_task)
    return task_to_dict(db_task)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Delete task"""
    try:
        t_id = int(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID")
    
    task = db.query(Task).filter(Task.id == t_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(task)
    db.commit()
    return None

