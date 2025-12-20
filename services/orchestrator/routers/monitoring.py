"""
Monitoring router - proxy requests to WorkPulse service
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from auth.jwt_handler import get_current_user
from services.workpulse_client import workpulse_client

router = APIRouter(prefix="/api/v1/monitoring", tags=["Monitoring"])


class ActivityLog(BaseModel):
    activity_type: str  # e.g., "task_completed", "meeting", "code_review"
    description: str
    duration_minutes: Optional[int] = None
    timestamp: Optional[datetime] = None
    tags: Optional[list[str]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "activity_type": "task_completed",
                "description": "Completed login bug fix",
                "duration_minutes": 120,
                "timestamp": "2025-12-20T10:30:00Z",
                "tags": ["bug-fix", "urgent"]
            }
        }


@router.get("/activity/{user_id}")
async def get_user_activity(user_id: str, days: int = Query(7), current_user = Depends(get_current_user)):
    """Get user activity data"""
    return await workpulse_client.get_user_activity(user_id, days)


@router.get("/activity/{user_id}/today")
async def get_today_activity(user_id: str, current_user = Depends(get_current_user)):
    """Get today's activity"""
    return await workpulse_client.get_today_activity(user_id)


@router.post("/activity/log")
async def log_activity(activity_data: ActivityLog, current_user = Depends(get_current_user)):
    """Log user activity"""
    from uuid import UUID
    data_dict = activity_data.dict()
    
    # Map orchestrator schema to WorkPulse schema
    workpulse_data = {
        "orchestrator_user_id": current_user["sub"],
        "event": data_dict.get("activity_type", "custom"),
        "input_type": "manual",
        "application": "orchestrator",
        "window_title": data_dict.get("description", ""),
        "duration_seconds": (data_dict.get("duration_minutes", 0) or 0) * 60,
        "timestamp": data_dict.get("timestamp")
    }
    
    return await workpulse_client.log_activity(workpulse_data)


@router.get("/team/{org_id}")
async def get_team_activity(org_id: str, current_user = Depends(get_current_user)):
    """Get team activity summary"""
    return await workpulse_client.get_team_activity(org_id)


@router.get("/stats/{user_id}/productivity")
async def get_productivity_stats(user_id: str, current_user = Depends(get_current_user)):
    """Get productivity statistics"""
    return await workpulse_client.get_productivity_stats(user_id)
