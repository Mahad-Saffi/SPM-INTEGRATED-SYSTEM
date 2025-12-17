"""
Performance Evaluation API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
from api.database import get_db
from api.models import Performance
from api.dependencies import verify_atlas_token
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/performances", tags=["performances"])

class PerformanceCreate(BaseModel):
    employee_id: str
    performance_score: float
    completion_rate: float
    on_time_rate: float
    rank: int = None
    trend: str = None

def performance_to_dict(perf: Performance) -> Dict[str, Any]:
    """Convert Performance model to dict"""
    return {
        "id": str(perf.id),
        "employee_id": perf.employee_id,
        "performance_score": perf.performance_score,
        "completion_rate": perf.completion_rate,
        "on_time_rate": perf.on_time_rate,
        "rank": perf.rank,
        "trend": perf.trend,
        "evaluation_date": perf.evaluation_date.isoformat() if perf.evaluation_date else None,
        "created_at": perf.created_at.isoformat() if perf.created_at else None,
        "updated_at": perf.updated_at.isoformat() if perf.updated_at else None
    }

@router.get("", response_model=List[Dict[str, Any]])
async def get_performances(
    employee_id: Optional[str] = Query(None, description="Filter by employee ID"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Get all performance evaluations, optionally filtered by employee"""
    query = db.query(Performance)
    if employee_id:
        query = query.filter(Performance.employee_id == employee_id)
    performances = query.order_by(Performance.evaluation_date.desc()).all()
    return [performance_to_dict(perf) for perf in performances]

@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_performance(
    performance: PerformanceCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Create new performance evaluation"""
    db_performance = Performance(
        employee_id=performance.employee_id,
        performance_score=performance.performance_score,
        completion_rate=performance.completion_rate,
        on_time_rate=performance.on_time_rate,
        rank=performance.rank,
        trend=performance.trend
    )
    db.add(db_performance)
    db.commit()
    db.refresh(db_performance)
    return performance_to_dict(db_performance)

