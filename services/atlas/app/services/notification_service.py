from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, desc
from app.models.notification import Notification
from app.config.database import SessionLocal
from datetime import datetime

class NotificationService:
    async def create_notification(
        self,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        link: str = None
    ) -> Notification:
        """Create a new notification for a user"""
        async with SessionLocal() as session:
            notification = Notification(
                user_id=user_id,
                type=notification_type,
                title=title,
                message=message,
                link=link
            )
            session.add(notification)
            await session.commit()
            await session.refresh(notification)
            return notification

    async def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50
    ) -> list:
        """Get notifications for a user"""
        async with SessionLocal() as session:
            query = select(Notification).where(Notification.user_id == user_id)
            
            if unread_only:
                query = query.where(Notification.read == False)
            
            query = query.order_by(desc(Notification.created_at)).limit(limit)
            
            result = await session.execute(query)
            notifications = result.scalars().all()
            
            return [
                {
                    "id": notif.id,
                    "type": notif.type,
                    "title": notif.title,
                    "message": notif.message,
                    "link": notif.link,
                    "read": notif.read,
                    "created_at": notif.created_at.isoformat() if notif.created_at else None,
                    "read_at": notif.read_at.isoformat() if notif.read_at else None,
                }
                for notif in notifications
            ]

    async def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Mark a notification as read"""
        async with SessionLocal() as session:
            result = await session.execute(
                select(Notification).where(
                    and_(
                        Notification.id == notification_id,
                        Notification.user_id == user_id
                    )
                )
            )
            notification = result.scalars().first()
            
            if notification:
                notification.read = True
                notification.read_at = datetime.utcnow()
                await session.commit()
                return True
            return False

    async def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user"""
        async with SessionLocal() as session:
            result = await session.execute(
                select(Notification).where(
                    and_(
                        Notification.user_id == user_id,
                        Notification.read == False
                    )
                )
            )
            notifications = result.scalars().all()
            
            count = 0
            for notification in notifications:
                notification.read = True
                notification.read_at = datetime.utcnow()
                count += 1
            
            await session.commit()
            return count

    async def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications"""
        async with SessionLocal() as session:
            result = await session.execute(
                select(Notification).where(
                    and_(
                        Notification.user_id == user_id,
                        Notification.read == False
                    )
                )
            )
            notifications = result.scalars().all()
            return len(notifications)

    async def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """Delete a notification"""
        async with SessionLocal() as session:
            result = await session.execute(
                select(Notification).where(
                    and_(
                        Notification.id == notification_id,
                        Notification.user_id == user_id
                    )
                )
            )
            notification = result.scalars().first()
            
            if notification:
                await session.delete(notification)
                await session.commit()
                return True
            return False

notification_service = NotificationService()
