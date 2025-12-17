"""
Goal Management API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
from api.database import get_db
from api.models import PerformanceGoal
from api.dependencies import verify_atlas_token
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/goals", tags=["goals"])

class GoalCreate(BaseModel):
    title: str
    description: str = None
    goal_type: str  # quantitative, qualitative, skill_based
    target_value: float = None
    start_date: datetime
    target_date: datetime

class GoalUpdate(BaseModel):
    current_value: float = None
    status: str = None  # in_progress, achieved, missed

class GoalResponse(BaseModel):
    id: int
    user_id: str
    title: str
    description: str = None
    goal_type: str
    target_value: float = None
    current_value: float
    start_date: datetime
    target_date: datetime
    status: str
    created_at: datetime

@router.get("/user/{user_id}", response_model=List[GoalResponse])
async def get_user_goals(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Get all goals for a user"""
    goals = db.query(PerformanceGoal).filter(
        PerformanceGoal.user_id == user_id
    ).all()
    return goals

@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    goal: GoalCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Create a new performance goal"""
    user_id = str(current_user.get("user_id", current_user.get("id")))
    
    db_goal = PerformanceGoal(
        user_id=user_id,
        title=goal.title,
        description=goal.description,
        goal_type=goal.goal_type,
        target_value=goal.target_value,
        start_date=goal.start_date,
        target_date=goal.target_date,
        status="in_progress"
    )
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal

@router.put("/{goal_id}/progress", response_model=GoalResponse)
async def update_goal_progress(
    goal_id: int,
    update: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Update goal progress"""
    goal = db.query(PerformanceGoal).filter(PerformanceGoal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Check ownership
    user_id = str(current_user.get("user_id", current_user.get("id")))
    if goal.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this goal")
    
    if update.current_value is not None:
        goal.current_value = update.current_value
    if update.status:
        goal.status = update.status
    
    db.commit()
    db.refresh(goal)
    return goal


