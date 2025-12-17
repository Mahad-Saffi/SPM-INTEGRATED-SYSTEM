from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from app.core.security import get_current_user
from app.services.notification_service import notification_service

router = APIRouter()

class MarkAsReadRequest(BaseModel):
    notification_id: int

@router.get("")
async def get_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get notifications for the current user"""
    notifications = await notification_service.get_user_notifications(
        user_id=current_user['id'],
        unread_only=unread_only,
        limit=limit
    )
    return notifications

@router.get("/unread-count")
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    """Get count of unread notifications"""
    count = await notification_service.get_unread_count(current_user['id'])
    return {"count": count}

@router.post("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Mark a specific notification as read"""
    success = await notification_service.mark_as_read(notification_id, current_user['id'])
    if success:
        return {"message": "Notification marked as read"}
    return {"error": "Notification not found"}, 404

@router.post("/mark-all-read")
async def mark_all_as_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read"""
    count = await notification_service.mark_all_as_read(current_user['id'])
    return {"message": f"Marked {count} notifications as read", "count": count}

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Delete a notification"""
    success = await notification_service.delete_notification(notification_id, current_user['id'])
    if success:
        return {"message": "Notification deleted"}
    return {"error": "Notification not found"}, 404
