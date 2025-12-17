"""
SQLAlchemy Models for Performance API
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from api.database import Base

class PerformanceReview(Base):
    """Performance review model"""
    __tablename__ = "performance_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, index=True, nullable=False)  # Atlas user ID
    reviewer_id = Column(String, index=True, nullable=False)  # Atlas user ID
    review_period_start = Column(DateTime, nullable=False)
    review_period_end = Column(DateTime, nullable=False)
    overall_rating = Column(Float, nullable=True)
    strengths = Column(Text, nullable=True)
    areas_for_improvement = Column(Text, nullable=True)
    status = Column(String, default="draft")  # draft, submitted, acknowledged
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PerformanceGoal(Base):
    """Performance goal model"""
    __tablename__ = "performance_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)  # Atlas user ID
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    goal_type = Column(String, nullable=False)  # quantitative, qualitative, skill_based
    target_value = Column(Float, nullable=True)
    current_value = Column(Float, default=0.0)
    start_date = Column(DateTime, nullable=False)
    target_date = Column(DateTime, nullable=False)
    status = Column(String, default="in_progress")  # in_progress, achieved, missed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PeerFeedback(Base):
    """Peer feedback model"""
    __tablename__ = "peer_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, index=True, nullable=False)  # Atlas user ID
    reviewer_id = Column(String, index=True, nullable=False)  # Atlas user ID
    project_id = Column(String, nullable=True)  # Atlas project ID
    feedback_type = Column(String, nullable=False)  # positive, constructive, general
    rating = Column(Float, nullable=False)  # 1-5 scale
    feedback_text = Column(Text, nullable=False)
    is_anonymous = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class SkillAssessment(Base):
    """Skill assessment model"""
    __tablename__ = "skill_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)  # Atlas user ID
    skill_name = Column(String, nullable=False)
    skill_category = Column(String, nullable=True)  # technical, soft, domain
    proficiency_level = Column(String, nullable=False)  # beginner, intermediate, advanced, expert
    proficiency_score = Column(Float, nullable=False)  # 0-100
    assessed_by = Column(String, nullable=True)  # Atlas user ID
    assessment_method = Column(String, nullable=True)  # self, peer, manager, test
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PerformanceMetric(Base):
    """Performance metrics model"""
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)  # Atlas user ID
    metric_date = Column(DateTime, nullable=False, index=True)
    tasks_completed = Column(Integer, default=0)
    tasks_on_time = Column(Integer, default=0)
    productivity_score = Column(Float, default=0.0)
    collaboration_score = Column(Float, default=0.0)
    overall_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Employee(Base):
    """Employee model"""
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    department = Column(String, nullable=True)
    position = Column(String, nullable=True)
    status = Column(String, default="active")  # active, inactive
    hire_date = Column(DateTime, nullable=True)
    skills = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Project(Base):
    """Project model"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="active")  # active, completed, on_hold
    deadline = Column(DateTime, nullable=True)
    manager = Column(String, nullable=True)  # Manager email or ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Task(Base):
    """Task model"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, in_progress, completed, cancelled
    priority = Column(String, default="medium")  # low, medium, high
    assigned_to = Column(String, nullable=True, index=True)  # Employee ID
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    created_by = Column(String, nullable=True)

class Performance(Base):
    """Performance evaluation model"""
    __tablename__ = "performances"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, index=True, nullable=False)  # Employee ID
    performance_score = Column(Float, nullable=False)
    completion_rate = Column(Float, nullable=False)
    on_time_rate = Column(Float, nullable=False)
    rank = Column(Integer, nullable=True)
    trend = Column(String, nullable=True)  # improving, declining, stable
    evaluation_date = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Notification(Base):
    """Notification model"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)  # User ID
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String, default="info")  # info, warning, success, error
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


