"""
Notification API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
from api.database import get_db
from api.models import Notification
from api.dependencies import verify_atlas_token
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])

class NotificationCreate(BaseModel):
    user_id: str
    title: str
    message: str
    type: str = "info"

def notification_to_dict(notif: Notification) -> Dict[str, Any]:
    """Convert Notification model to dict"""
    return {
        "id": str(notif.id),
        "user_id": notif.user_id,
        "title": notif.title,
        "message": notif.message,
        "type": notif.type,
        "is_read": notif.is_read,
        "created_at": notif.created_at.isoformat() if notif.created_at else None
    }

@router.get("", response_model=List[Dict[str, Any]])
async def get_notifications(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Get all notifications, optionally filtered by user"""
    query = db.query(Notification)
    if user_id:
        query = query.filter(Notification.user_id == user_id)
    notifications = query.order_by(Notification.created_at.desc()).all()
    return [notification_to_dict(notif) for notif in notifications]

@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Create new notification"""
    db_notification = Notification(
        user_id=notification.user_id,
        title=notification.title,
        message=notification.message,
        type=notification.type
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return notification_to_dict(db_notification)

@router.put("/{notification_id}/read", response_model=Dict[str, Any])
async def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(verify_atlas_token)
):
    """Mark notification as read"""
    try:
        notif_id = int(notification_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid notification ID")
    
    notification = db.query(Notification).filter(Notification.id == notif_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification_to_dict(notification)

