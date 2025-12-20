import uuid
from sqlalchemy import Column, String, Text, ForeignKey, TIMESTAMP, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.user import Base

class Project(Base):
    """Project model - belongs to organization and optionally to lab"""
    __tablename__ = 'projects'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False, index=True)
    lab_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Optional association with a lab
    status = Column(String(50), default='active')  # active, completed, archived
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id])
    organization = relationship("Organization", back_populates="projects")
    epics = relationship("Epic", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_projects_org', 'organization_id'),
        Index('idx_projects_owner', 'owner_id'),
        Index('idx_projects_lab', 'lab_id'),
    )
