from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Boolean, Text, Date, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from .database import Base


class User(Base):
    """User model - synced from Orchestrator"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    orchestrator_user_id = Column(UUID(as_uuid=True), unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    activities = relationship("Activity", back_populates="user", cascade="all, delete-orphan")
    team_memberships = relationship("TeamMember", back_populates="user", cascade="all, delete-orphan")


class Activity(Base):
    """Activity model - logs work activities"""
    __tablename__ = "activities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # For org isolation
    task_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Optional link to task
    description = Column(Text, nullable=False)
    duration_seconds = Column(Integer, default=0)
    logged_date = Column(Date, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="activities", foreign_keys=[user_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_activities_user', 'user_id'),
        Index('idx_activities_org', 'organization_id'),
        Index('idx_activities_task', 'task_id'),
    )


class Team(Base):
    """Team model - groups users within organization"""
    __tablename__ = "teams"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # For org isolation
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    leader_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    leader = relationship("User", foreign_keys=[leader_id])
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_teams_org', 'organization_id'),
        Index('idx_teams_creator', 'created_by'),
    )


class TeamMember(Base):
    """TeamMember model - links users to teams"""
    __tablename__ = "team_members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String, default="member")  # member, lead
    joined_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    team = relationship("Team", back_populates="members", foreign_keys=[team_id])
    user = relationship("User", back_populates="team_memberships", foreign_keys=[user_id])
    
    # Unique constraint: one user per team
    __table_args__ = (
        Index('idx_team_member_unique', 'user_id', 'team_id', unique=True),
        Index('idx_team_members_user', 'user_id'),
    )
