"""
Research router - proxy requests to Labs service
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr

from auth.jwt_handler import get_current_user
from services.labs_client import labs_client

router = APIRouter(prefix="/api/v1/research", tags=["Research"])


class LabCreate(BaseModel):
    name: str
    description: str
    organization_id: str  # Required: which organization this lab belongs to
    location: Optional[str] = None
    budget: Optional[float] = None
    research_focus: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "AI Research Lab",
                "description": "Artificial Intelligence research",
                "organization_id": "550e8400-e29b-41d4-a716-446655440000",
                "location": "Building A, Floor 3",
                "budget": 500000,
                "research_focus": "Machine Learning"
            }
        }


class ResearcherCreate(BaseModel):
    name: str
    email: EmailStr
    specialization: str
    lab_id: int
    years_experience: int
    education: Optional[str] = None
    publications: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Dr. Jane Smith",
                "email": "jane@example.com",
                "specialization": "Machine Learning",
                "lab_id": 1,
                "years_experience": 10,
                "education": "PhD in Computer Science",
                "publications": 25
            }
        }


@router.get("/labs")
async def get_labs(current_user = Depends(get_current_user)):
    """Get labs created by current user in their organization"""
    user_id = current_user.get("sub")  # Get user ID from JWT token
    return await labs_client.get_labs(user_id=user_id)


@router.get("/labs/{lab_id}")
async def get_lab(lab_id: int, current_user = Depends(get_current_user)):
    """Get a specific lab"""
    return await labs_client.get_lab(lab_id)


@router.post("/labs")
async def create_lab(lab_data: LabCreate, current_user = Depends(get_current_user)):
    """Create a new lab in a specific organization"""
    user_id = current_user.get("sub")
    org_id = lab_data.organization_id
    
    # Prepare lab data
    lab_dict = lab_data.dict()
    lab_dict["orchestrator_user_id"] = user_id  # Creator
    lab_dict["orchestrator_org_id"] = org_id
    # head_id will be set by the labs service after syncing the user
    
    return await labs_client.create_lab(lab_dict)


@router.get("/researchers")
async def get_researchers(current_user = Depends(get_current_user)):
    """Get all researchers"""
    return await labs_client.get_researchers()


@router.get("/labs/{lab_id}/researchers")
async def get_lab_researchers(lab_id: int, current_user = Depends(get_current_user)):
    """Get researchers for a lab"""
    return await labs_client.get_lab_researchers(lab_id)


@router.post("/researchers")
async def create_researcher(researcher_data: ResearcherCreate, current_user = Depends(get_current_user)):
    """Create a new researcher"""
    return await labs_client.create_researcher(researcher_data.dict())


@router.get("/collaborations")
async def get_collaborations(current_user = Depends(get_current_user)):
    """Get collaboration suggestions"""
    return await labs_client.get_collaborations()


@router.post("/collaborations/email")
async def generate_collaboration_email(lab_pair: str, current_user = Depends(get_current_user)):
    """Generate collaboration email"""
    return await labs_client.generate_collaboration_email(lab_pair)
