from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from pydantic import BaseModel
from app.core.security import get_current_user
from app.services.websocket_manager import manager
from app.models.message import Message, Channel, ChannelMember, UserPresence
from app.config.database import SessionLocal
from sqlalchemy.future import select
from sqlalchemy import and_, or_, desc
from datetime import datetime
import jwt
from starlette.config import Config

router = APIRouter()
config = Config(".env")

class SendMessageRequest(BaseModel):
    content: str
    channel_id: int = None
    recipient_id: int = None

class CreateChannelRequest(BaseModel):
    name: str
    description: str = ""
    channel_type: str = "public"

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """WebSocket endpoint for real-time chat"""
    try:
        # Verify JWT token
        payload = jwt.decode(token, config('JWT_SECRET_KEY'), algorithms=["HS256"])
        user_id = payload['id']
        
        await manager.connect(websocket, user_id)
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_json()
                
                # Handle different message types
                if data['type'] == 'message':
                    # Save message to database
                    async with SessionLocal() as session:
                        message = Message(
                            sender_id=user_id,
                            channel_id=data.get('channel_id'),
                            recipient_id=data.get('recipient_id'),
                            content=data['content']
                        )
                        session.add(message)
                        await session.commit()
                        await session.refresh(message)
                        
                        # Broadcast to channel or send to recipient
                        message_data = {
                            'type': 'message',
                            'id': message.id,
                            'sender_id': user_id,
                            'content': message.content,
                            'created_at': message.created_at.isoformat(),
                            'channel_id': message.channel_id,
                            'recipient_id': message.recipient_id
                        }
                        
                        if message.channel_id:
                            await manager.broadcast_to_channel(message_data, message.channel_id)
                        elif message.recipient_id:
                            await manager.send_personal_message(message_data, message.recipient_id)
                            await manager.send_personal_message(message_data, user_id)
                
                elif data['type'] == 'typing':
                    # Broadcast typing indicator
                    typing_data = {
                        'type': 'typing',
                        'user_id': user_id,
                        'channel_id': data.get('channel_id')
                    }
                    if data.get('channel_id'):
                        await manager.broadcast_to_channel(typing_data, data['channel_id'], exclude_user=user_id)
        
        except WebSocketDisconnect:
            manager.disconnect(websocket, user_id)
            await manager.update_presence(user_id, 'offline')
            await manager.broadcast_presence_update(user_id, 'offline')
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()

@router.get("/channels")
async def get_channels(current_user: dict = Depends(get_current_user)):
    """Get all channels user has access to"""
    async with SessionLocal() as session:
        # Get channels user is a member of
        result = await session.execute(
            select(Channel).join(ChannelMember).where(
                ChannelMember.user_id == current_user['id']
            )
        )
        channels = result.scalars().all()
        
        return [
            {
                'id': ch.id,
                'name': ch.name,
                'description': ch.description,
                'channel_type': ch.channel_type,
                'created_at': ch.created_at.isoformat()
            }
            for ch in channels
        ]

@router.post("/channels/{channel_id}/join")
async def join_channel(channel_id: int, current_user: dict = Depends(get_current_user)):
    """Join a public channel"""
    async with SessionLocal() as session:
        # Check if channel exists and is public
        result = await session.execute(
            select(Channel).where(Channel.id == channel_id)
        )
        channel = result.scalars().first()
        
        if not channel:
            return {"error": "Channel not found"}, 404
        
        if channel.channel_type == 'private':
            return {"error": "Cannot join private channel"}, 403
        
        # Check if already a member
        result = await session.execute(
            select(ChannelMember).where(
                and_(
                    ChannelMember.channel_id == channel_id,
                    ChannelMember.user_id == current_user['id']
                )
            )
        )
        existing = result.scalars().first()
        
        if existing:
            return {"message": "Already a member"}
        
        # Add as member
        member = ChannelMember(
            channel_id=channel_id,
            user_id=current_user['id'],
            role='member'
        )
        session.add(member)
        await session.commit()
        
        return {"message": "Joined channel successfully"}

@router.post("/channels")
async def create_channel(
    request: CreateChannelRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new channel"""
    async with SessionLocal() as session:
        channel = Channel(
            name=request.name,
            description=request.description,
            channel_type=request.channel_type,
            created_by=current_user['id']
        )
        session.add(channel)
        await session.flush()
        
        # Add creator as admin member
        member = ChannelMember(
            channel_id=channel.id,
            user_id=current_user['id'],
            role='admin'
        )
        session.add(member)
        await session.commit()
        await session.refresh(channel)
        
        return {
            'id': channel.id,
            'name': channel.name,
            'description': channel.description,
            'channel_type': channel.channel_type
        }

@router.get("/channels/{channel_id}/messages")
async def get_channel_messages(
    channel_id: int,
    limit: int = Query(50, le=100),
    search: str = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get messages from a channel with optional search"""
    async with SessionLocal() as session:
        query = select(Message).where(Message.channel_id == channel_id)
        
        # Add search filter if provided
        if search:
            query = query.where(Message.content.contains(search))
        
        query = query.order_by(desc(Message.created_at)).limit(limit)
        result = await session.execute(query)
        messages = result.scalars().all()
        
        return [
            {
                'id': msg.id,
                'sender_id': msg.sender_id,
                'content': msg.content,
                'created_at': msg.created_at.isoformat(),
                'is_edited': msg.is_edited
            }
            for msg in reversed(messages)
        ]

@router.get("/search")
async def search_messages(
    query: str = Query(..., min_length=2),
    limit: int = Query(20, le=50),
    current_user: dict = Depends(get_current_user)
):
    """Search messages across all channels and DMs"""
    async with SessionLocal() as session:
        # Search in channels user is member of
        result = await session.execute(
            select(Message).join(Channel).join(ChannelMember).where(
                and_(
                    ChannelMember.user_id == current_user['id'],
                    Message.content.contains(query)
                )
            ).order_by(desc(Message.created_at)).limit(limit)
        )
        channel_messages = result.scalars().all()
        
        # Search in DMs
        result = await session.execute(
            select(Message).where(
                and_(
                    or_(
                        Message.sender_id == current_user['id'],
                        Message.recipient_id == current_user['id']
                    ),
                    Message.content.contains(query)
                )
            ).order_by(desc(Message.created_at)).limit(limit)
        )
        dm_messages = result.scalars().all()
        
        all_messages = list(channel_messages) + list(dm_messages)
        all_messages.sort(key=lambda x: x.created_at, reverse=True)
        
        return [
            {
                'id': msg.id,
                'sender_id': msg.sender_id,
                'content': msg.content,
                'channel_id': msg.channel_id,
                'recipient_id': msg.recipient_id,
                'created_at': msg.created_at.isoformat(),
                'type': 'channel' if msg.channel_id else 'dm'
            }
            for msg in all_messages[:limit]
        ]

@router.get("/online-users")
async def get_online_users(current_user: dict = Depends(get_current_user)):
    """Get list of currently online users"""
    online_user_ids = manager.get_online_users()
    
    async with SessionLocal() as session:
        from app.models.user import User
        result = await session.execute(
            select(User).where(User.id.in_(online_user_ids))
        )
        users = result.scalars().all()
        
        return [
            {
                'id': user.id,
                'username': user.username,
                'avatar_url': user.avatar_url
            }
            for user in users
        ]

@router.get("/direct-messages/{user_id}")
async def get_direct_messages(
    user_id: int,
    limit: int = Query(50, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get direct messages with a specific user"""
    async with SessionLocal() as session:
        result = await session.execute(
            select(Message).where(
                or_(
                    and_(
                        Message.sender_id == current_user['id'],
                        Message.recipient_id == user_id
                    ),
                    and_(
                        Message.sender_id == user_id,
                        Message.recipient_id == current_user['id']
                    )
                )
            ).order_by(desc(Message.created_at)).limit(limit)
        )
        messages = result.scalars().all()
        
        return [
            {
                'id': msg.id,
                'sender_id': msg.sender_id,
                'recipient_id': msg.recipient_id,
                'content': msg.content,
                'created_at': msg.created_at.isoformat(),
                'is_edited': msg.is_edited
            }
            for msg in reversed(messages)
        ]

@router.get("/conversations")
async def get_conversations(current_user: dict = Depends(get_current_user)):
    """Get list of users with whom current user has DM conversations"""
    async with SessionLocal() as session:
        from app.models.user import User
        
        # Get unique user IDs from DMs
        result = await session.execute(
            select(Message.sender_id, Message.recipient_id).where(
                or_(
                    Message.sender_id == current_user['id'],
                    Message.recipient_id == current_user['id']
                )
            ).distinct()
        )
        
        user_ids = set()
        for row in result:
            if row[0] != current_user['id']:
                user_ids.add(row[0])
            if row[1] and row[1] != current_user['id']:
                user_ids.add(row[1])
        
        if not user_ids:
            return []
        
        # Get user details
        result = await session.execute(
            select(User).where(User.id.in_(user_ids))
        )
        users = result.scalars().all()
        
        return [
            {
                'id': user.id,
                'username': user.username,
                'avatar_url': user.avatar_url
            }
            for user in users
        ]
