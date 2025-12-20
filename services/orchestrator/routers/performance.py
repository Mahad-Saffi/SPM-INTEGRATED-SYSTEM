"""
Performance router - proxy requests to EPR service
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import date

from auth.jwt_handler import get_current_user
from services.epr_client import epr_client

router = APIRouter(prefix="/api/v1/performance", tags=["Performance"])


class GoalCreate(BaseModel):
    title: str
    description: str
    target_value: float
    metric: str  # e.g., "bug_reduction_percentage", "code_coverage"
    due_date: date
    priority: str = "medium"  # low, medium, high
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Improve code quality",
                "description": "Reduce bugs by 50%",
                "target_value": 50,
                "metric": "bug_reduction_percentage",
                "due_date": "2025-12-31",
                "priority": "high"
            }
        }


@router.get("/user/{user_id}/score")
async def get_performance_score(user_id: str, current_user = Depends(get_current_user)):
    """Get user's performance score"""
    return await epr_client.get_performance_score(user_id)


@router.get("/user/{user_id}/goals")
async def get_user_goals(user_id: str, current_user = Depends(get_current_user)):
    """Get user's goals"""
    return await epr_client.get_user_goals(user_id)


@router.post("/goals")
async def create_goal(goal_data: GoalCreate, current_user = Depends(get_current_user)):
    """Create a new goal"""
    from datetime import datetime
    data_dict = goal_data.dict()
    data_dict["user_id"] = current_user["sub"]
    
    # Convert date to datetime for EPR service
    if "due_date" in data_dict and data_dict["due_date"]:
        due_date = data_dict.pop("due_date")
        data_dict["target_date"] = datetime.combine(due_date, datetime.min.time()).isoformat()
        data_dict["start_date"] = datetime.now().isoformat()
    
    # Add goal_type if not present
    if "goal_type" not in data_dict:
        data_dict["goal_type"] = "quantitative"
    
    # Add current_value if not present
    if "current_value" not in data_dict:
        data_dict["current_value"] = 0
    
    return await epr_client.create_goal(data_dict)


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
