from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from app.core.security import get_current_user
from app.services.organization_service import organization_service

router = APIRouter()


class OrganizationCreate(BaseModel):
    name: str
    description: Optional[str] = None


class TeamMemberAdd(BaseModel):
    email: EmailStr
    password: str
    username: str
    role: str
    description: Optional[str] = None


class TeamMemberResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    description: Optional[str]
    invited_by_username: str
    joined_at: str


@router.post("/create")
async def create_organization(
    org_data: OrganizationCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new organization (automatically done on signup)"""
    try:
        # Check if user already has an organization
        existing_org = await organization_service.get_user_organization(current_user['id'])
        if existing_org:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has an organization"
            )
        
        org = await organization_service.create_organization(
            name=org_data.name,
            description=org_data.description or "",
            owner_id=current_user['id']
        )
        
        return {
            "id": str(org.id),
            "name": org.name,
            "description": org.description,
            "owner_id": org.owner_id,
            "created_at": org.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/my-organization")
async def get_my_organization(current_user: dict = Depends(get_current_user)):
    """Get the organization of the current user"""
    org = await organization_service.get_user_organization(current_user['id'])
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No organization found. Please create one first."
        )
    
    return {
        "id": str(org.id),
        "name": org.name,
        "description": org.description,
        "owner_id": org.owner_id,
        "is_owner": org.owner_id == current_user['id'],
        "created_at": org.created_at.isoformat()
    }


@router.get("/members")
async def get_team_members(current_user: dict = Depends(get_current_user)):
    """Get all team members in user's organization"""
    org = await organization_service.get_user_organization(current_user['id'])
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No organization found"
        )
    
    members = await organization_service.get_organization_members(str(org.id))
    
    return [
        {
            "id": member.user.id,
            "username": member.user.username,
            "email": member.user.email,
            "role": member.role,
            "description": member.description,
            "invited_by": member.inviter.username,
            "invited_by_id": member.invited_by,
            "joined_at": member.joined_at.isoformat()
        }
        for member in members
    ]


@router.post("/add-member")
async def add_team_member(
    member_data: TeamMemberAdd,
    current_user: dict = Depends(get_current_user)
):
    """Add a new team member to the organization"""
    # Get user's organization
    org = await organization_service.get_user_organization(current_user['id'])
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No organization found. Please create one first."
        )
    
    # Check if user is owner
    is_owner = await organization_service.is_organization_owner(str(org.id), current_user['id'])
    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owner can add members"
        )
    
    try:
        result = await organization_service.add_team_member(
            organization_id=str(org.id),
            email=member_data.email,
            password=member_data.password,
            username=member_data.username,
            role=member_data.role,
            description=member_data.description or "",
            invited_by=current_user['id']
        )
        
        return {
            "message": "Team member added successfully",
            "user": {
                "id": result["user"].id,
                "username": result["user"].username,
                "email": result["user"].email,
                "role": result["member"].role
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/remove-member/{user_id}")
async def remove_team_member(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Remove a team member from the organization"""
    org = await organization_service.get_user_organization(current_user['id'])
    
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No organization found"
        )
    
    # Check if user is owner
    is_owner = await organization_service.is_organization_owner(str(org.id), current_user['id'])
    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owner can remove members"
        )
    
    # Can't remove yourself
    if user_id == current_user['id']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself from the organization"
        )
    
    try:
        result = await organization_service.remove_team_member(str(org.id), user_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
