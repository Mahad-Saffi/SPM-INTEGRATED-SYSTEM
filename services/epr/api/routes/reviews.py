"""
Performance Review API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
from api.database import get_db
from api.models import PerformanceReview
from api.dependencies import verify_atlas_token, require_manager
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])

class ReviewCreate(BaseModel):
    employee_id: str
    review_period_start: datetime
    review_period_end: datetime
    overall_rating: float = None
    strengths: str = None
    areas_for_improvement: str = None

class ReviewResponse(BaseModel):
    id: int
    employee_id: str
    reviewer_id: str
    review_period_start: datetime
    review_period_end: datetime
    overall_rating: float = None
    strengths: str = None
    areas_for_improvement: str = None
    status: str
    created_at: datetime

@router.get("/user/{user_id}", response_model=List[ReviewResponse])
async def get_user_reviews(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Get all performance reviews for a user"""
    reviews = db.query(PerformanceReview).filter(
        PerformanceReview.employee_id == user_id
    ).all()
    return reviews

@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Create a new performance review (manager only)"""
    require_manager(current_user)
    
    db_review = PerformanceReview(
        employee_id=review.employee_id,
        reviewer_id=str(current_user.get("user_id", current_user.get("id"))),
        review_period_start=review.review_period_start,
        review_period_end=review.review_period_end,
        overall_rating=review.overall_rating,
        strengths=review.strengths,
        areas_for_improvement=review.areas_for_improvement,
        status="draft"
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

@router.get("/pending", response_model=List[ReviewResponse])
async def get_pending_reviews(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Get pending reviews for manager"""
    require_manager(current_user)
    
    reviews = db.query(PerformanceReview).filter(
        PerformanceReview.status == "draft"
    ).all()
    return reviews


