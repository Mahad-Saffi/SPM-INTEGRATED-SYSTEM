"""
Pydantic models for authentication
"""
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str = "member"


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: str
    is_active: bool
    organization_id: Optional[str] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    sub: str  # user_id
    email: str
    name: str
    role: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class OrganizationCreate(BaseModel):
    name: str
    description: Optional[str] = None


class OrganizationResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    owner_id: str
    is_active: bool

    class Config:
        from_attributes = True
