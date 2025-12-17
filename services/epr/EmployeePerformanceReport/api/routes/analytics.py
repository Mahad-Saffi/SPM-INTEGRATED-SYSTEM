"""
Performance Analytics API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from api.database import get_db
from api.dependencies import verify_atlas_token, require_manager
from api.services.atlas_client import AtlasClient
from api.services.performance_calculator import PerformanceCalculator
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

@router.get("/user/{user_id}/performance")
async def get_user_performance(
    user_id: str,
    time_period: str = "quarterly",  # monthly, quarterly, yearly
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token),
    authorization: Optional[str] = Header(None)
):
    """Get comprehensive performance data for a user"""
    # Extract token from authorization header
    token = None
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
    
    # Initialize services
    atlas_client = AtlasClient()
    calculator = PerformanceCalculator(atlas_client)
    
    try:
        # Calculate performance score
        performance_data = await calculator.calculate_performance_score(
            int(user_id),
            token or "",  # You'll need to extract token from request
            time_period
        )
        
        # Get historical metrics
        from api.models import PerformanceMetric
        metrics = db.query(PerformanceMetric).filter(
            PerformanceMetric.user_id == user_id
        ).order_by(PerformanceMetric.metric_date.desc()).limit(12).all()
        
        # Format trends
        trends = [
            {
                "date": m.metric_date.isoformat(),
                "overall_score": m.overall_score,
                "productivity": m.productivity_score,
                "collaboration": m.collaboration_score
            }
            for m in metrics
        ]
        
        return {
            **performance_data,
            "trends": trends,
            "period": time_period
        }
    finally:
        await atlas_client.close()

@router.get("/team/{org_id}/performance")
async def get_team_performance(
    org_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Get team performance analytics (manager only)"""
    require_manager(current_user)
    
    # Get all users in organization (from Atlas)
    # For now, return placeholder
    return {
        "organization_id": org_id,
        "team_size": 0,
        "average_performance": 0.0,
        "top_performers": [],
        "needs_attention": []
    }

@router.post("/predict")
async def predict_performance_trend(
    user_id: str,
    prediction_months: int = 3,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Predict performance trend for a user"""
    from api.models import PerformanceMetric
    
    # Get historical data
    metrics = db.query(PerformanceMetric).filter(
        PerformanceMetric.user_id == user_id
    ).order_by(PerformanceMetric.metric_date.desc()).limit(6).all()
    
    if len(metrics) < 2:
        raise HTTPException(
            status_code=400,
            detail="Insufficient historical data for prediction"
        )
    
    # Simple linear trend prediction
    recent_scores = [m.overall_score for m in metrics[:3]]
    avg_score = sum(recent_scores) / len(recent_scores)
    
    # Calculate trend
    if len(recent_scores) >= 2:
        trend = recent_scores[0] - recent_scores[-1]
        predicted_score = avg_score + (trend * prediction_months)
    else:
        predicted_score = avg_score
    
    return {
        "user_id": user_id,
        "current_score": recent_scores[0] if recent_scores else 0,
        "predicted_score": max(0, min(100, predicted_score)),
        "prediction_months": prediction_months,
        "trend": "improving" if trend > 0 else "declining" if trend < 0 else "stable"
    }

