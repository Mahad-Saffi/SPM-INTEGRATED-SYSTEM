import uuid
from sqlalchemy import Column, String, Text, ForeignKey, TIMESTAMP, func, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.user import Base

class Story(Base):
    __tablename__ = 'stories'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    epic_id = Column(UUID(as_uuid=True), ForeignKey('epics.id'), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    order = Column(Integer, default=0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

    epic = relationship("Epic", back_populates="stories")
    tasks = relationship("Task", back_populates="story", cascade="all, delete-orphan")
