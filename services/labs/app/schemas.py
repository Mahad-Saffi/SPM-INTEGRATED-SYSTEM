from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime

# Users
class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    orchestrator_user_id: Optional[UUID] = None

class UserResponse(UserBase):
    id: int
    orchestrator_user_id: Optional[UUID] = None
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Labs
class LabBase(BaseModel):
    name: str
    domain: Optional[str] = None
    description: Optional[str] = None

class LabCreate(LabBase):
    orchestrator_org_id: UUID  # REQUIRED - Organization
    orchestrator_user_id: Optional[UUID] = None  # Who created this lab

class LabResponse(LabBase):
    id: int
    orchestrator_org_id: UUID
    orchestrator_user_id: Optional[UUID] = None
    head_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Researchers
class ResearcherBase(BaseModel):
    name: str
    email: str
    field: Optional[str] = None
    lab_id: int

class ResearcherCreate(ResearcherBase):
    orchestrator_user_id: Optional[UUID] = None

class ResearcherResponse(ResearcherBase):
    id: int
    orchestrator_user_id: Optional[UUID] = None
    status: str = "pending"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Collaborations
class CollaborationBase(BaseModel):
    lab_id: int
    researcher_id: int
    title: str
    description: Optional[str] = None

class CollaborationCreate(CollaborationBase):
    pass

class CollaborationResponse(CollaborationBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
