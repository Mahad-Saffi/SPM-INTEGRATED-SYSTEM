"""
Performance router - proxy requests to EPR service
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any

from auth.jwt_handler import get_current_user
from services.epr_client import epr_client

router = APIRouter(prefix="/api/v1/performance", tags=["Performance"])


@router.get("/user/{user_id}/score")
async def get_performance_score(user_id: str, current_user = Depends(get_current_user)):
    """Get user's performance score"""
    return await epr_client.get_performance_score(user_id)


@router.get("/user/{user_id}/goals")
async def get_user_goals(user_id: str, current_user = Depends(get_current_user)):
    """Get user's goals"""
    return await epr_client.get_user_goals(user_id)


@router.post("/goals")
async def create_goal(goal_data: Dict[str, Any], current_user = Depends(get_current_user)):
    """Create a new goal"""
    goal_data["user_id"] = current_user["sub"]
    return await epr_client.create_goal(goal_data)


@router.get("/user/{user_id}/reviews")
async def get_reviews(user_id: str, current_user = Depends(get_current_user)):
    """Get performance reviews"""
    return await epr_client.get_reviews(user_id)


@router.get("/user/{user_id}/feedback")
async def get_feedback(user_id: str, current_user = Depends(get_current_user)):
    """Get peer feedback"""
    return await epr_client.get_feedback(user_id)


@router.get("/user/{user_id}/skills")
async def get_skills(user_id: str, current_user = Depends(get_current_user)):
    """Get user skills"""
    return await epr_client.get_skills(user_id)


@router.get("/team/{org_id}/performance")
async def get_team_performance(org_id: str, current_user = Depends(get_current_user)):
    """Get team performance metrics"""
    return await epr_client.get_team_performance(org_id)
