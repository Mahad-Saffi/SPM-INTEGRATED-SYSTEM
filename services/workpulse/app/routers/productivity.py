from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from uuid import UUID
from .. import models, schemas, database

router = APIRouter(prefix="/productivity", tags=["Productivity"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/user/{user_id}/stats")
def get_productivity_stats(
    user_id: UUID,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get productivity statistics for user"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Get activities
    activities = db.query(models.Activity).filter(
        and_(
            models.Activity.orchestrator_user_id == user_id,
            models.Activity.timestamp >= cutoff
        )
    ).all()
    
    # Calculate stats
    total_active = sum(a.duration_seconds for a in activities if a.event == 'active')
    total_idle = sum(a.duration_seconds for a in activities if a.event == 'idle')
    keystrokes = len([a for a in activities if a.input_type == 'keyboard'])
    mouse_clicks = len([a for a in activities if a.input_type == 'mouse'])
    
    # Calculate productivity score (0-100)
    total_time = total_active + total_idle
    if total_time > 0:
        productivity_score = min(100, (total_active / total_time) * 100)
    else:
        productivity_score = 0
    
    return {
        "user_id": user_id,
        "days": days,
        "total_active_time": total_active,
        "total_idle_time": total_idle,
        "productivity_score": round(productivity_score, 2),
        "keystrokes": keystrokes,
        "mouse_clicks": mouse_clicks,
        "total_activities": len(activities)
    }

@router.get("/user/{user_id}/today")
def get_today_stats(user_id: UUID, db: Session = Depends(get_db)):
    """Get today's productivity stats"""
    today = datetime.utcnow().date()
    
    activities = db.query(models.Activity).filter(
        and_(
            models.Activity.orchestrator_user_id == user_id,
            func.date(models.Activity.timestamp) == today
        )
    ).all()
    
    total_active = sum(a.duration_seconds for a in activities if a.event == 'active')
    total_idle = sum(a.duration_seconds for a in activities if a.event == 'idle')
    
    total_time = total_active + total_idle
    productivity_score = (total_active / total_time * 100) if total_time > 0 else 0
    
    return {
        "date": today.isoformat(),
        "total_active_time": total_active,
        "total_idle_time": total_idle,
        "productivity_score": round(productivity_score, 2),
        "total_activities": len(activities)
    }

@router.get("/team/{team_id}/stats")
def get_team_productivity(
    team_id: int,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get team productivity statistics"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Get team members
    team_members = db.query(models.TeamMember).filter(
        models.TeamMember.team_id == team_id
    ).all()
    
    user_ids = [m.user.orchestrator_user_id for m in team_members if m.user]
    
    # Get activities for all team members
    activities = db.query(models.Activity).filter(
        and_(
            models.Activity.orchestrator_user_id.in_(user_ids),
            models.Activity.timestamp >= cutoff
        )
    ).all()
    
    # Calculate aggregate stats
    total_active = sum(a.duration_seconds for a in activities if a.event == 'active')
    total_idle = sum(a.duration_seconds for a in activities if a.event == 'idle')
    
    total_time = total_active + total_idle
    avg_productivity = (total_active / total_time * 100) if total_time > 0 else 0
    
    return {
        "team_id": team_id,
        "days": days,
        "total_members": len(team_members),
        "total_active_time": total_active,
        "total_idle_time": total_idle,
        "average_productivity_score": round(avg_productivity, 2),
        "total_activities": len(activities)
    }
