"""
Project Management API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
from api.database import get_db
from api.models import Project
from api.dependencies import verify_atlas_token, require_manager
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])

class ProjectCreate(BaseModel):
    name: str
    description: str = None
    status: str = "active"
    deadline: datetime = None
    manager: str = None

class ProjectUpdate(BaseModel):
    name: str = None
    description: str = None
    status: str = None
    deadline: datetime = None
    manager: str = None

def project_to_dict(project: Project) -> Dict[str, Any]:
    """Convert Project model to dict"""
    return {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "deadline": project.deadline.isoformat() if project.deadline else None,
        "manager": project.manager,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None
    }

@router.get("", response_model=List[Dict[str, Any]])
async def get_projects(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Get all projects"""
    projects = db.query(Project).all()
    return [project_to_dict(proj) for proj in projects]

@router.get("/{project_id}", response_model=Dict[str, Any])
async def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Get project by ID"""
    try:
        p_id = int(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID")
    
    project = db.query(Project).filter(Project.id == p_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project_to_dict(project)

@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Create new project (manager only)"""
    require_manager(current_user)
    
    db_project = Project(
        name=project.name,
        description=project.description,
        status=project.status,
        deadline=project.deadline,
        manager=project.manager
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return project_to_dict(db_project)

@router.put("/{project_id}", response_model=Dict[str, Any])
async def update_project(
    project_id: str,
    project: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Update project (manager only)"""
    require_manager(current_user)
    
    try:
        p_id = int(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID")
    
    db_project = db.query(Project).filter(Project.id == p_id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.name is not None:
        db_project.name = project.name
    if project.description is not None:
        db_project.description = project.description
    if project.status is not None:
        db_project.status = project.status
    if project.deadline is not None:
        db_project.deadline = project.deadline
    if project.manager is not None:
        db_project.manager = project.manager
    
    db.commit()
    db.refresh(db_project)
    return project_to_dict(db_project)

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Delete project (manager only)"""
    require_manager(current_user)
    
    try:
        p_id = int(project_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project ID")
    
    project = db.query(Project).filter(Project.id == p_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()
    return None

