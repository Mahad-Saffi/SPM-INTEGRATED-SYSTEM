from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Text, Index
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
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Lab(Base):
    """Lab model - research lab"""
    __tablename__ = "labs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    orchestrator_org_id = Column(UUID(as_uuid=True), index=True, nullable=False)  # REQUIRED - Organization
    orchestrator_user_id = Column(UUID(as_uuid=True), index=True, nullable=False)  # REQUIRED - Creator
    head_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)  # Lab head (user)
    name = Column(String, nullable=False)
    domain = Column(String)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    head = relationship("User")
    researchers = relationship("Researcher", back_populates="lab", cascade="all, delete-orphan")
    collaborations = relationship("Collaboration", back_populates="lab", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_labs_org', 'orchestrator_org_id'),
        Index('idx_labs_creator', 'orchestrator_user_id'),
    )


class Researcher(Base):
    """Researcher model - links users to labs"""
    __tablename__ = "researchers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    orchestrator_user_id = Column(UUID(as_uuid=True), index=True, nullable=True)  # Links to central user
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    field = Column(String)  # Research specialization
    lab_id = Column(UUID(as_uuid=True), ForeignKey("labs.id"), nullable=False, index=True)
    status = Column(String, default="pending")  # pending, active, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lab = relationship("Lab", back_populates="researchers")
    
    # Unique constraint: one researcher per user per lab
    __table_args__ = (
        Index('idx_researcher_per_lab', 'orchestrator_user_id', 'lab_id', unique=True, postgresql_where=orchestrator_user_id.isnot(None)),
        Index('idx_researchers_lab', 'lab_id'),
        Index('idx_researchers_user', 'orchestrator_user_id'),
    )


class Collaboration(Base):
    """Collaboration model - research collaborations"""
    __tablename__ = "collaborations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    lab_id = Column(UUID(as_uuid=True), ForeignKey("labs.id"), nullable=False, index=True)
    researcher_id = Column(UUID(as_uuid=True), ForeignKey("researchers.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="proposed")  # proposed, active, completed
    score = Column(String, default="0")  # Collaboration score
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lab = relationship("Lab", back_populates="collaborations")
    researcher = relationship("Researcher")
    
    # Indexes
    __table_args__ = (
        Index('idx_collaborations_lab', 'lab_id'),
        Index('idx_collaborations_researcher', 'researcher_id'),
    )
