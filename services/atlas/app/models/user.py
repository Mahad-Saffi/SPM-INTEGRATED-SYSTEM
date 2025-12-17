from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    orchestrator_user_id = Column(UUID(as_uuid=True), unique=True, index=True, nullable=True)
    github_id = Column(String(50), unique=True, nullable=True, index=True)
    username = Column(String(100), nullable=False, unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255), nullable=True)
    avatar_url = Column(String(500))
    role = Column(String(50), nullable=False, default='developer')
    is_active = Column(Boolean, default=True)
    invited_by = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
