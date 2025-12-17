"""
Peer Feedback API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
from api.database import get_db
from api.models import PeerFeedback
from api.dependencies import verify_atlas_token
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])

class FeedbackCreate(BaseModel):
    employee_id: str
    project_id: str = None
    feedback_type: str  # positive, constructive, general
    rating: float  # 1-5 scale
    feedback_text: str
    is_anonymous: bool = False

class FeedbackResponse(BaseModel):
    id: int
    employee_id: str
    reviewer_id: str
    project_id: str = None
    feedback_type: str
    rating: float
    feedback_text: str
    is_anonymous: bool
    created_at: datetime

@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Submit peer feedback"""
    reviewer_id = str(current_user.get("user_id", current_user.get("id")))
    
    db_feedback = PeerFeedback(
        employee_id=feedback.employee_id,
        reviewer_id=reviewer_id,
        project_id=feedback.project_id,
        feedback_type=feedback.feedback_type,
        rating=feedback.rating,
        feedback_text=feedback.feedback_text,
        is_anonymous=feedback.is_anonymous
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback

@router.get("/user/{user_id}", response_model=List[FeedbackResponse])
async def get_user_feedback(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Get all feedback for a user"""
    feedback = db.query(PeerFeedback).filter(
        PeerFeedback.employee_id == user_id
    ).all()
    return feedback

