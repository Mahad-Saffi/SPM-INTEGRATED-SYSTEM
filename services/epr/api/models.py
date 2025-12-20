"""
SQLAlchemy Models for Performance API
"""
from sqlalchemy import Column, String, Float, DateTime, Text, Boolean, ForeignKey, Integer, Date, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from api.database import Base
import uuid


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
    reviews = relationship("PerformanceReview", back_populates="employee", foreign_keys="PerformanceReview.orchestrator_user_id")
    goals = relationship("PerformanceGoal", back_populates="employee")
    feedback_received = relationship("PeerFeedback", back_populates="employee", foreign_keys="PeerFeedback.orchestrator_user_id")


class PerformanceReview(Base):
    """Performance review model"""
    __tablename__ = "performance_reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    orchestrator_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)  # Employee
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)  # Reviewer
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # For org isolation
    rating = Column(Integer, nullable=False)  # 1-5 scale
    comments = Column(Text, nullable=True)
    review_period_start = Column(Date, nullable=False)
    review_period_end = Column(Date, nullable=False)
    review_date = Column(Date, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = relationship("User", foreign_keys=[orchestrator_user_id], back_populates="reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    
    # Indexes
    __table_args__ = (
        Index('idx_performance_reviews_org', 'organization_id'),
        Index('idx_performance_reviews_user', 'orchestrator_user_id'),
        Index('idx_performance_reviews_reviewer', 'reviewer_id'),
    )


class PerformanceGoal(Base):
    """Performance goal model"""
    __tablename__ = "performance_goals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    orchestrator_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    target_date = Column(Date, nullable=False)
    status = Column(String, default="pending")  # pending, in_progress, completed, cancelled
    progress_percentage = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = relationship("User", back_populates="goals", foreign_keys=[orchestrator_user_id])


class PeerFeedback(Base):
    """Peer feedback model"""
    __tablename__ = "peer_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    orchestrator_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)  # Recipient
    from_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)  # Giver
    feedback = Column(Text, nullable=False)
    is_anonymous = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    employee = relationship("User", foreign_keys=[orchestrator_user_id], back_populates="feedback_received")
    from_user = relationship("User", foreign_keys=[from_user_id])


class SkillAssessment(Base):
    """Skill assessment model"""
    __tablename__ = "skill_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String, nullable=False, index=True)
    skill_name = Column(String, nullable=False)
    skill_category = Column(String, nullable=True)  # technical, soft, domain
    proficiency_level = Column(String, nullable=False)  # beginner, intermediate, advanced, expert
    proficiency_score = Column(Float, nullable=False)  # 0-100
    assessed_by = Column(String, nullable=True)
    assessment_method = Column(String, nullable=True)  # self, peer, manager, test
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Employee(Base):
    """Employee model"""
    __tablename__ = "employees"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String, nullable=False, unique=True, index=True)
    department = Column(String, nullable=True)
    position = Column(String, nullable=True)
    manager_id = Column(String, nullable=True)
    hire_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Task(Base):
    """Task model"""
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, in_progress, completed, cancelled
    priority = Column(String, default="medium")  # low, medium, high
    due_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Project(Base):
    """Project model"""
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    manager_id = Column(String, nullable=False, index=True)
    status = Column(String, default="active")  # active, completed, on_hold
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Performance(Base):
    """Performance model"""
    __tablename__ = "performances"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String, nullable=False, index=True)
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=False)
    period = Column(String, nullable=True)  # daily, weekly, monthly
    recorded_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    """Notification model"""
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String, nullable=True)  # review, goal, feedback, alert
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class PerformanceMetric(Base):
    """Performance metric model"""
    __tablename__ = "performance_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(String, nullable=False, index=True)
    metric_type = Column(String, nullable=False)  # productivity, quality, attendance, etc
    metric_value = Column(Float, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


