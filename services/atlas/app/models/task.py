import uuid
from sqlalchemy import Column, String, Text, ForeignKey, TIMESTAMP, func, Integer, Index, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.user import Base

class Task(Base):
    """Task model - belongs to project and assigned to user"""
    __tablename__ = 'tasks'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    assignee_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    status = Column(String(20), nullable=False, default='To Do')  # To Do, In Progress, Done
    progress_percentage = Column(Integer, default=0)  # 0-100
    due_date = Column(Date, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="tasks", foreign_keys=[project_id])
    assignee = relationship("User", foreign_keys=[assignee_id])
    creator = relationship("User", foreign_keys=[created_by])
    
    # Indexes
    __table_args__ = (
        Index('idx_tasks_project', 'project_id'),
        Index('idx_tasks_assignee', 'assignee_id'),
        Index('idx_tasks_creator', 'created_by'),
    )
