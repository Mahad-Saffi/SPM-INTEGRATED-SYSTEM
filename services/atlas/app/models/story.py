import uuid
from sqlalchemy import Column, String, Text, ForeignKey, TIMESTAMP, func, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.user import Base

class Story(Base):
    """Story model - groups tasks within an epic"""
    __tablename__ = 'stories'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    epic_id = Column(UUID(as_uuid=True), ForeignKey('epics.id'), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    order = Column(Integer, default=0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

    # Relationships
    epic = relationship("Epic", back_populates="stories", foreign_keys=[epic_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_stories_epic', 'epic_id'),
    )
