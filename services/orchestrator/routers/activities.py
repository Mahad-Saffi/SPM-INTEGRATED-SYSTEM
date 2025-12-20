"""
Activities router - proxy requests to WorkPulse service
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession

from auth.jwt_handler import get_current_user
from middleware.permissions import (
    check_org_membership,
    check_same_org,
    validate_activity_logging
)
from services.workpulse_client import workpulse_client
from database import get_db

router = APIRouter(prefix="/api/v1", tags=["Activities"])


class ActivityCreate(BaseModel):
    """Schema for logging activity"""
    description: str
    duration_seconds: int
    task_id: Optional[UUID] = None
    logged_date: Optional[date] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "description": "Worked on UI design",
                "duration_seconds": 3600,
                "task_id": None,
                "logged_date": "2025-12-20"
            }
        }


class TeamCreate(BaseModel):
    """Schema for creating a team"""
    name: str
    description: Optional[str] = None
    leader_id: Optional[UUID] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Frontend Team",
                "description": "Frontend development team",
                "leader_id": None
            }
        }


class TeamMemberCreate(BaseModel):
    """Schema for adding team member"""
    user_id: UUID
    role: str = "member"
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "uuid",
                "role": "member"
            }
        }


# ============================================
# ACTIVITY ENDPOINTS
# ============================================

@router.post("/activities")
async def log_activity(
    activity_data: ActivityCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Log activity"""
    
    org_id = check_org_membership(current_user)
    
    try:
        # Validate activity logging
        await validate_activity_logging(
            db,
            org_id,
            str(activity_data.task_id) if activity_data.task_id else None,
            current_user
        )
        
        return await workpulse_client.log_activity({
            "user_id": current_user.get("sub"),
            "organization_id": org_id,
            "task_id": str(activity_data.task_id) if activity_data.task_id else None,
            "description": activity_data.description,
            "duration_seconds": activity_data.duration_seconds,
            "logged_date": activity_data.logged_date
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activities")
async def get_activities(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Get user's activities"""
    
    try:
        return await workpulse_client.get_activities(
            user_id=current_user.get("sub"),
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activities/team")
async def get_team_activities(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Get team activities"""
    
    # Verify user is admin or manager
    if current_user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    try:
        return await workpulse_client.get_team_activities(
            org_id=org_id,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# TEAM ENDPOINTS
# ============================================

@router.post("/teams")
async def create_team(
    team_data: TeamCreate,
    current_user = Depends(get_current_user)
):
    """Create team"""
    
    # Verify user is admin or manager
    if current_user.get("role") not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admin or manager can create teams")
    
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    try:
        return await workpulse_client.create_team({
            "name": team_data.name,
            "description": team_data.description,
            "organization_id": org_id,
            "created_by": current_user.get("sub"),
            "leader_id": str(team_data.leader_id) if team_data.leader_id else None
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams")
async def get_teams(current_user = Depends(get_current_user)):
    """Get teams in organization"""
    
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    try:
        return await workpulse_client.get_teams(org_id=org_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teams/{team_id}/members")
async def add_team_member(
    team_id: UUID,
    member_data: TeamMemberCreate,
    current_user = Depends(get_current_user)
):
    """Add member to team"""
    
    try:
        team = await workpulse_client.get_team(str(team_id))
        
        # Verify user is in same organization
        if team.get("organization_id") != current_user.get("organization_id"):
            if current_user.get("role") != "admin":
                raise HTTPException(status_code=403, detail="Access denied")
        
        return await workpulse_client.add_team_member(str(team_id), {
            "user_id": str(member_data.user_id),
            "role": member_data.role
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
