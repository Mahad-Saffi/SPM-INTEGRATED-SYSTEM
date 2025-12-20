import uuid
from sqlalchemy import Column, String, Text, ForeignKey, TIMESTAMP, func, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.user import Base

class Epic(Base):
    """Epic model - groups stories within a project"""
    __tablename__ = 'epics'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    order = Column(Integer, default=0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="epics", foreign_keys=[project_id])
    stories = relationship("Story", back_populates="epic", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_epics_project', 'project_id'),
    )
