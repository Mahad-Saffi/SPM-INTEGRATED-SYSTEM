from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from app.config.database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # For DMs
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default='text')  # text, file, system
    is_edited = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    channel_type = Column(String(20), default='public')  # public, private, dm
    project_id = Column(String(100), nullable=True)  # Optional: link to project
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class ChannelMember(Base):
    __tablename__ = "channel_members"

    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(20), default='member')  # admin, member
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class UserPresence(Base):
    __tablename__ = "user_presence"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    status = Column(String(20), default='offline')  # online, offline, away
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
