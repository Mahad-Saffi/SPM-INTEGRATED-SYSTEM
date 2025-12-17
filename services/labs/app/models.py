from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    orchestrator_user_id = Column(UUID(as_uuid=True), unique=True, index=True, nullable=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

class Lab(Base):
    __tablename__ = "labs"
    id = Column(Integer, primary_key=True, index=True)
    orchestrator_org_id = Column(UUID(as_uuid=True), index=True, nullable=True)
    name = Column(String, nullable=False)
    domain = Column(String)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Researcher(Base):
    __tablename__ = "researchers"
    id = Column(Integer, primary_key=True, index=True)
    orchestrator_user_id = Column(UUID(as_uuid=True), index=True, nullable=True)
    name = Column(String, nullable=False)
    field = Column(String)
    lab_id = Column(Integer, ForeignKey("labs.id"))
    lab = relationship("Lab")

class Collaboration(Base):
    __tablename__ = "collaborations"
    id = Column(Integer, primary_key=True, index=True)
    lab_id = Column(Integer, ForeignKey("labs.id"))
    researcher_id = Column(Integer, ForeignKey("researchers.id"))
    title = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    lab = relationship("Lab")
    researcher = relationship("Researcher")
