from fastapi import WebSocket
from typing import Dict, List, Set
import json
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        # user_id -> list of WebSocket connections
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # channel_id -> set of user_ids
        self.channel_members: Dict[int, Set[int]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """Connect a user's websocket"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        
        # Update user presence
        await self.update_presence(user_id, 'online')
        
        # Notify others that user is online
        await self.broadcast_presence_update(user_id, 'online')

    def disconnect(self, websocket: WebSocket, user_id: int):
        """Disconnect a user's websocket"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            
            # If no more connections, mark as offline
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        """Send message to a specific user"""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass  # Connection might be closed

    async def broadcast_to_channel(self, message: dict, channel_id: int, exclude_user: int = None):
        """Broadcast message to all users in a channel"""
        if channel_id in self.channel_members:
            for user_id in self.channel_members[channel_id]:
                if exclude_user and user_id == exclude_user:
                    continue
                await self.send_personal_message(message, user_id)

    async def broadcast_presence_update(self, user_id: int, status: str):
        """Broadcast user presence update to all connected users"""
        message = {
            'type': 'presence_update',
            'user_id': user_id,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Send to all connected users
        for uid in list(self.active_connections.keys()):
            if uid != user_id:
                await self.send_personal_message(message, uid)

    async def update_presence(self, user_id: int, status: str):
        """Update user presence in database"""
        from app.config.database import SessionLocal
        from app.models.message import UserPresence
        from sqlalchemy.future import select
        
        async with SessionLocal() as session:
            result = await session.execute(
                select(UserPresence).where(UserPresence.user_id == user_id)
            )
            presence = result.scalars().first()
            
            if presence:
                presence.status = status
                presence.last_seen = datetime.utcnow()
            else:
                presence = UserPresence(
                    user_id=user_id,
                    status=status,
                    last_seen=datetime.utcnow()
                )
                session.add(presence)
            
            await session.commit()

    def join_channel(self, user_id: int, channel_id: int):
        """Add user to channel"""
        if channel_id not in self.channel_members:
            self.channel_members[channel_id] = set()
        self.channel_members[channel_id].add(user_id)

    def leave_channel(self, user_id: int, channel_id: int):
        """Remove user from channel"""
        if channel_id in self.channel_members:
            self.channel_members[channel_id].discard(user_id)

    def get_online_users(self) -> List[int]:
        """Get list of currently online user IDs"""
        return list(self.active_connections.keys())

manager = ConnectionManager()
