from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(50), primary_key=True, index=True)
    orchestrator_user_id = Column(UUID(as_uuid=True), unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Activity(Base):
    __tablename__ = "activities"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.id"))
    orchestrator_user_id = Column(UUID(as_uuid=True), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event = Column(String)  # 'active', 'idle', 'keystroke', 'mouse_click', etc.
    input_type = Column(String)  # 'keyboard', 'mouse', 'system'
    application = Column(String, nullable=True)
    window_title = Column(String, nullable=True)
    duration_seconds = Column(Float, default=0)
    
    user = relationship("User", backref="activities")

class ProductivityStats(Base):
    __tablename__ = "productivity_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.id"))
    orchestrator_user_id = Column(UUID(as_uuid=True), index=True)
    date = Column(DateTime, index=True)
    total_active_time = Column(Float, default=0)  # seconds
    total_idle_time = Column(Float, default=0)  # seconds
    keystrokes = Column(Integer, default=0)
    mouse_clicks = Column(Integer, default=0)
    applications_used = Column(String)  # JSON string
    productivity_score = Column(Float, default=0)
    
    user = relationship("User", backref="stats")

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    orchestrator_org_id = Column(UUID(as_uuid=True), index=True, nullable=True)
    name = Column(String)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class TeamMember(Base):
    __tablename__ = "team_members"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    user_id = Column(String(50), ForeignKey("users.id"))
    role = Column(String, default="member")
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    team = relationship("Team", backref="members")
    user = relationship("User", backref="team_memberships")
