"""
Skill Assessment API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
from api.database import get_db
from api.models import SkillAssessment
from api.dependencies import verify_atlas_token
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/skills", tags=["skills"])

class SkillAssessCreate(BaseModel):
    skill_name: str
    skill_category: str = None  # technical, soft, domain
    proficiency_level: str  # beginner, intermediate, advanced, expert
    proficiency_score: float  # 0-100
    assessment_method: str = None  # self, peer, manager, test

class SkillResponse(BaseModel):
    id: int
    user_id: str
    skill_name: str
    skill_category: str = None
    proficiency_level: str
    proficiency_score: float
    assessed_by: str = None
    assessment_method: str = None
    created_at: datetime

@router.get("/user/{user_id}", response_model=List[SkillResponse])
async def get_user_skills(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Get all skill assessments for a user"""
    skills = db.query(SkillAssessment).filter(
        SkillAssessment.user_id == user_id
    ).all()
    return skills

@router.post("/assess", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def assess_skills(
    assessment: SkillAssessCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Create a skill assessment"""
    user_id = str(current_user.get("user_id", current_user.get("id")))
    assessed_by = str(current_user.get("user_id", current_user.get("id")))
    
    db_skill = SkillAssessment(
        user_id=user_id,
        skill_name=assessment.skill_name,
        skill_category=assessment.skill_category,
        proficiency_level=assessment.proficiency_level,
        proficiency_score=assessment.proficiency_score,
        assessed_by=assessed_by,
        assessment_method=assessment.assessment_method
    )
    db.add(db_skill)
    db.commit()
    db.refresh(db_skill)
    return db_skill

@router.get("/gaps/{user_id}")
async def identify_skill_gaps(
    user_id: str,
    project_id: str = None,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Identify skill gaps for a user"""
    # Get user's current skills
    user_skills = db.query(SkillAssessment).filter(
        SkillAssessment.user_id == user_id
    ).all()
    
    # Get required skills (if project_id provided, get project requirements)
    # For now, return basic gap analysis
    skill_scores = {s.skill_name: s.proficiency_score for s in user_skills}
    
    # Identify gaps (skills below threshold)
    gaps = [
        {
            "skill_name": skill_name,
            "current_score": score,
            "recommended_level": "intermediate" if score < 50 else "advanced",
            "gap": max(0, 70 - score)  # Target 70+
        }
        for skill_name, score in skill_scores.items()
        if score < 70
    ]
    
    return {
        "user_id": user_id,
        "skill_gaps": gaps,
        "total_gaps": len(gaps),
        "current_skills_count": len(user_skills)
    }


