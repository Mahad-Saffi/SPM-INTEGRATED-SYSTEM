"""
Performance router - proxy requests to EPR service
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import date

from auth.jwt_handler import get_current_user
from services.epr_client import epr_client

router = APIRouter(prefix="/api/v1/performance", tags=["Performance"])


class ReviewCreate(BaseModel):
    """Schema for creating performance review"""
    rating: int
    comments: Optional[str] = None
    review_period_start: date
    review_period_end: date
    
    class Config:
        json_schema_extra = {
            "example": {
                "rating": 4,
                "comments": "Great work this quarter",
                "review_period_start": "2025-10-01",
                "review_period_end": "2025-12-31"
            }
        }


class GoalCreate(BaseModel):
    """Schema for creating performance goal"""
    title: str
    description: Optional[str] = None
    target_date: date
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Complete project X",
                "description": "Finish the mobile app project",
                "target_date": "2025-12-31"
            }
        }


class GoalUpdate(BaseModel):
    """Schema for updating performance goal"""
    status: Optional[str] = None
    progress_percentage: Optional[int] = None


class FeedbackCreate(BaseModel):
    """Schema for giving peer feedback"""
    feedback: str
    is_anonymous: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "feedback": "Great collaboration on the project",
                "is_anonymous": False
            }
        }


# ============================================
# PERFORMANCE REVIEW ENDPOINTS
# ============================================

@router.post("/users/{user_id}/reviews")
async def create_review(
    user_id: UUID,
    review_data: ReviewCreate,
    current_user = Depends(get_current_user)
):
    """Create performance review"""
    
    # Verify user is admin or manager
    if current_user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admin or manager can create reviews")
    
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    # Verify cannot review self
    if str(user_id) == current_user.get("sub"):
        raise HTTPException(status_code=400, detail="Cannot review yourself")
    
    try:
        return await epr_client.create_review({
            "orchestrator_user_id": str(user_id),
            "reviewer_id": current_user.get("sub"),
            "organization_id": org_id,
            "rating": review_data.rating,
            "comments": review_data.comments,
            "review_period_start": review_data.review_period_start,
            "review_period_end": review_data.review_period_end
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/reviews")
async def get_reviews(
    user_id: UUID,
    current_user = Depends(get_current_user)
):
    """Get performance reviews"""
    
    # Verify user can view reviews
    is_self = str(user_id) == current_user.get("sub")
    is_manager = current_user.get("role") in ["admin", "manager"]
    
    if not (is_self or is_manager):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        return await epr_client.get_reviews(str(user_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# PERFORMANCE GOAL ENDPOINTS
# ============================================

@router.post("/users/{user_id}/goals")
async def create_goal(
    user_id: UUID,
    goal_data: GoalCreate,
    current_user = Depends(get_current_user)
):
    """Create performance goal"""
    
    # Verify user can create goals for themselves or is admin/manager
    is_self = str(user_id) == current_user.get("sub")
    is_manager = current_user.get("role") in ["admin", "manager"]
    
    if not (is_self or is_manager):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        return await epr_client.create_goal({
            "orchestrator_user_id": str(user_id),
            "title": goal_data.title,
            "description": goal_data.description,
            "target_date": goal_data.target_date
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/goals")
async def get_goals(
    user_id: UUID,
    current_user = Depends(get_current_user)
):
    """Get performance goals"""
    
    # Verify user can view goals
    is_self = str(user_id) == current_user.get("sub")
    is_manager = current_user.get("role") in ["admin", "manager"]
    
    if not (is_self or is_manager):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        return await epr_client.get_goals(str(user_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/users/{user_id}/goals/{goal_id}")
async def update_goal(
    user_id: UUID,
    goal_id: UUID,
    goal_data: GoalUpdate,
    current_user = Depends(get_current_user)
):
    """Update performance goal"""
    
    # Verify user can update goals
    is_self = str(user_id) == current_user.get("sub")
    is_manager = current_user.get("role") in ["admin", "manager"]
    
    if not (is_self or is_manager):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        return await epr_client.update_goal(
            str(goal_id),
            goal_data.dict(exclude_unset=True)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# PEER FEEDBACK ENDPOINTS
# ============================================

@router.post("/users/{user_id}/feedback")
async def give_feedback(
    user_id: UUID,
    feedback_data: FeedbackCreate,
    current_user = Depends(get_current_user)
):
    """Give peer feedback"""
    
    # Verify cannot give feedback to self
    if str(user_id) == current_user.get("sub"):
        raise HTTPException(status_code=400, detail="Cannot give feedback to yourself")
    
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    try:
        return await epr_client.give_feedback({
            "orchestrator_user_id": str(user_id),
            "from_user_id": current_user.get("sub"),
            "feedback": feedback_data.feedback,
            "is_anonymous": feedback_data.is_anonymous
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/feedback")
async def get_feedback(
    user_id: UUID,
    current_user = Depends(get_current_user)
):
    """Get peer feedback"""
    
    # Verify user can view feedback
    is_self = str(user_id) == current_user.get("sub")
    is_manager = current_user.get("role") in ["admin", "manager"]
    
    if not (is_self or is_manager):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        return await epr_client.get_feedback(str(user_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
