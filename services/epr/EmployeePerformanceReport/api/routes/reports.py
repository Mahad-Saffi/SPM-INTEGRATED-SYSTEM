"""
Performance Reports API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from api.database import get_db
from api.dependencies import verify_atlas_token
from api.services.atlas_client import AtlasClient
from api.services.performance_calculator import PerformanceCalculator
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

@router.get("/user/{user_id}/quarterly")
async def get_user_quarterly_report(
    user_id: str,
    quarter: int = None,  # 1-4, defaults to current
    year: int = None,  # defaults to current year
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Generate quarterly performance report for a user"""
    # Determine quarter dates
    now = datetime.now()
    if year is None:
        year = now.year
    if quarter is None:
        quarter = (now.month - 1) // 3 + 1
    
    quarter_start_month = (quarter - 1) * 3 + 1
    quarter_start = datetime(year, quarter_start_month, 1)
    quarter_end = quarter_start + timedelta(days=90)
    if quarter_end.month != quarter_start_month + 2:
        quarter_end = datetime(year, quarter_start_month + 3, 1) - timedelta(days=1)
    
    # Get performance data
    from api.models import PerformanceReview, PerformanceGoal, PeerFeedback, SkillAssessment
    
    reviews = db.query(PerformanceReview).filter(
        PerformanceReview.employee_id == user_id,
        PerformanceReview.review_period_start >= quarter_start,
        PerformanceReview.review_period_end <= quarter_end
    ).all()
    
    goals = db.query(PerformanceGoal).filter(
        PerformanceGoal.user_id == user_id,
        PerformanceGoal.start_date >= quarter_start,
        PerformanceGoal.target_date <= quarter_end
    ).all()
    
    feedback = db.query(PeerFeedback).filter(
        PeerFeedback.employee_id == user_id,
        PeerFeedback.created_at >= quarter_start,
        PeerFeedback.created_at <= quarter_end
    ).all()
    
    skills = db.query(SkillAssessment).filter(
        SkillAssessment.user_id == user_id,
        SkillAssessment.created_at >= quarter_start,
        SkillAssessment.created_at <= quarter_end
    ).all()
    
    # Calculate summary
    achieved_goals = [g for g in goals if g.status == "achieved"]
    avg_feedback = sum(f.rating for f in feedback) / len(feedback) if feedback else 0
    avg_skill = sum(s.proficiency_score for s in skills) / len(skills) if skills else 0
    
    return {
        "user_id": user_id,
        "period": {
            "quarter": quarter,
            "year": year,
            "start": quarter_start.isoformat(),
            "end": quarter_end.isoformat()
        },
        "summary": {
            "reviews_count": len(reviews),
            "goals_total": len(goals),
            "goals_achieved": len(achieved_goals),
            "goals_achievement_rate": len(achieved_goals) / len(goals) * 100 if goals else 0,
            "feedback_count": len(feedback),
            "average_feedback_rating": round(avg_feedback, 2),
            "skills_assessed": len(skills),
            "average_skill_score": round(avg_skill, 2)
        },
        "reviews": [{"id": r.id, "rating": r.overall_rating, "status": r.status} for r in reviews],
        "goals": [{"id": g.id, "title": g.title, "status": g.status} for g in goals],
        "feedback_summary": {
            "total": len(feedback),
            "positive": len([f for f in feedback if f.feedback_type == "positive"]),
            "constructive": len([f for f in feedback if f.feedback_type == "constructive"])
        }
    }

@router.get("/team/{org_id}/quarterly")
async def get_team_quarterly_report(
    org_id: str,
    quarter: int = None,
    year: int = None,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Generate quarterly team performance report"""
    from api.dependencies import require_manager
    require_manager(current_user)
    
    # Placeholder - would aggregate team data
    return {
        "organization_id": org_id,
        "period": {
            "quarter": quarter or ((datetime.now().month - 1) // 3 + 1),
            "year": year or datetime.now().year
        },
        "team_summary": {
            "total_employees": 0,
            "average_performance": 0.0,
            "top_performers": [],
            "improvement_areas": []
        }
    }


