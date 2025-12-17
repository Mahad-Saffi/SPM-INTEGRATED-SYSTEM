"""
Monitoring router - proxy requests to WorkPulse service
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from auth.jwt_handler import get_current_user
from services.workpulse_client import workpulse_client

router = APIRouter(prefix="/api/v1/monitoring", tags=["Monitoring"])


@router.get("/activity/{user_id}")
async def get_user_activity(user_id: str, days: int = Query(7), current_user = Depends(get_current_user)):
    """Get user activity data"""
    return await workpulse_client.get_user_activity(user_id, days)


@router.get("/activity/{user_id}/today")
async def get_today_activity(user_id: str, current_user = Depends(get_current_user)):
    """Get today's activity"""
    return await workpulse_client.get_today_activity(user_id)


@router.post("/activity/log")
async def log_activity(activity_data: dict, current_user = Depends(get_current_user)):
    """Log user activity"""
    activity_data["user_id"] = current_user["sub"]
    return await workpulse_client.log_activity(activity_data)


@router.get("/team/{org_id}")
async def get_team_activity(org_id: str, current_user = Depends(get_current_user)):
    """Get team activity summary"""
    return await workpulse_client.get_team_activity(org_id)


@router.get("/stats/{user_id}/productivity")
async def get_productivity_stats(user_id: str, current_user = Depends(get_current_user)):
    """Get productivity statistics"""
    return await workpulse_client.get_productivity_stats(user_id)
