from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: str
    name: Optional[str] = None

class UserCreate(UserBase):
    orchestrator_user_id: UUID

class UserResponse(UserBase):
    id: int
    orchestrator_user_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

# Activity schemas
class ActivityBase(BaseModel):
    event: str
    input_type: Optional[str] = None
    application: Optional[str] = None
    window_title: Optional[str] = None
    duration_seconds: Optional[float] = 0

class ActivityCreate(ActivityBase):
    orchestrator_user_id: UUID
    timestamp: Optional[datetime] = None

class ActivityResponse(ActivityBase):
    id: int
    orchestrator_user_id: UUID
    timestamp: datetime
    
    class Config:
        from_attributes = True

# Productivity stats schemas
class ProductivityStatsBase(BaseModel):
    date: datetime
    total_active_time: float
    total_idle_time: float
    keystrokes: int
    mouse_clicks: int
    productivity_score: float

class ProductivityStatsCreate(ProductivityStatsBase):
    orchestrator_user_id: UUID
    applications_used: Optional[str] = None

class ProductivityStatsResponse(ProductivityStatsBase):
    id: int
    orchestrator_user_id: UUID
    applications_used: Optional[str] = None
    
    class Config:
        from_attributes = True

# Team schemas
class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None

class TeamCreate(TeamBase):
    orchestrator_org_id: Optional[UUID] = None

class TeamResponse(TeamBase):
    id: int
    orchestrator_org_id: Optional[UUID] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Dashboard response
class DashboardResponse(BaseModel):
    today_active_time: float
    today_idle_time: float
    productivity_score: float
    total_activities: int
    recent_activities: List[ActivityResponse]
