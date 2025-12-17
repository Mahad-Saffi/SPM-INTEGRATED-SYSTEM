from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List
from datetime import datetime, timedelta
from uuid import UUID
from .. import models, schemas, database

router = APIRouter(prefix="/activity", tags=["Activity"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.ActivityResponse)
def log_activity(activity: schemas.ActivityCreate, db: Session = Depends(get_db)):
    """Log user activity"""
    # Get or create user
    user = db.query(models.User).filter(
        models.User.orchestrator_user_id == activity.orchestrator_user_id
    ).first()
    
    if not user:
        user = models.User(
            orchestrator_user_id=activity.orchestrator_user_id,
            email=f"user_{activity.orchestrator_user_id}@workpulse.local"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Create activity
    db_activity = models.Activity(
        user_id=user.id,
        orchestrator_user_id=activity.orchestrator_user_id,
        timestamp=activity.timestamp or datetime.utcnow(),
        event=activity.event,
        input_type=activity.input_type,
        application=activity.application,
        window_title=activity.window_title,
        duration_seconds=activity.duration_seconds
    )
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity

@router.get("/user/{user_id}", response_model=List[schemas.ActivityResponse])
def get_user_activity(
    user_id: UUID,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get activity log for a user"""
    activities = db.query(models.Activity).filter(
        models.Activity.orchestrator_user_id == user_id
    ).order_by(models.Activity.timestamp.desc()).limit(limit).all()
    
    return activities

@router.get("/user/{user_id}/today", response_model=List[schemas.ActivityResponse])
def get_today_activity(user_id: UUID, db: Session = Depends(get_db)):
    """Get today's activity for a user"""
    today = datetime.utcnow().date()
    activities = db.query(models.Activity).filter(
        and_(
            models.Activity.orchestrator_user_id == user_id,
            func.date(models.Activity.timestamp) == today
        )
    ).order_by(models.Activity.timestamp.desc()).all()
    
    return activities

@router.get("/team/{team_id}", response_model=List[schemas.ActivityResponse])
def get_team_activity(
    team_id: int,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get team activity for the last N hours"""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Get team member user IDs
    team_members = db.query(models.TeamMember).filter(
        models.TeamMember.team_id == team_id
    ).all()
    
    user_ids = [member.user.orchestrator_user_id for member in team_members if member.user]
    
    activities = db.query(models.Activity).filter(
        and_(
            models.Activity.orchestrator_user_id.in_(user_ids),
            models.Activity.timestamp >= cutoff
        )
    ).order_by(models.Activity.timestamp.desc()).all()
    
    return activities

@router.delete("/user/{user_id}")
def clear_user_activity(user_id: UUID, db: Session = Depends(get_db)):
    """Clear all activity for a user (admin only)"""
    deleted = db.query(models.Activity).filter(
        models.Activity.orchestrator_user_id == user_id
    ).delete()
    db.commit()
    return {"deleted": deleted, "message": "Activity cleared"}
