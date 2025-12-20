"""
Authentication router - handles login, registration, and token management
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import logging

from database import get_db, User, Organization, Invitation
from auth.jwt_handler import (
    create_access_token, 
    verify_password, 
    get_password_hash, 
    get_current_user, 
    create_user_token,
    generate_user_id
)
from auth.models import UserCreate, UserResponse, TokenResponse, OrganizationCreate, OrganizationResponse, UserLogin, InvitationCreate, InvitationResponse
from services.user_sync import user_sync_service

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user"""
    
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user_id = generate_user_id()
    new_user = User(
        id=user_id,
        email=user_data.email,
        name=user_data.name,
        hashed_password=get_password_hash(user_data.password),
        role=user_data.role,
        is_active=True
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Create organization for the user
    org_id = str(uuid.uuid4())
    org = Organization(
        id=org_id,
        name=f"{user_data.name}'s Organization",
        owner_id=user_id
    )
    db.add(org)
    await db.commit()
    
    # Update user's organization
    new_user.organization_id = org_id
    await db.commit()
    
    # Sync user to all microservices
    sync_data = {
        "id": new_user.id,
        "email": new_user.email,
        "name": new_user.name,
        "role": new_user.role,
        "organization_id": new_user.organization_id
    }
    sync_results = await user_sync_service.sync_user_to_all_services(sync_data)
    logger.info(f"User sync results: {sync_results}")
    
    # Create token
    token = create_user_token(str(user_id), user_data.email, user_data.name, user_data.role, str(org_id))
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(new_user.id),
            "email": new_user.email,
            "name": new_user.name,
            "role": new_user.role,
            "organization_id": str(new_user.organization_id) if new_user.organization_id else None,
            "is_active": new_user.is_active
        },
        "user_id": str(new_user.id)
    }


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login user with email and password"""
    
    # Find user
    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalars().first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")
    
    # Create token with organization_id (convert UUIDs to strings)
    token = create_user_token(str(user.id), user.email, user.name, user.role, str(user.organization_id) if user.organization_id else None)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "organization_id": str(user.organization_id) if user.organization_id else None,
            "is_active": user.is_active
        }
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Get current user information"""
    
    result = await db.execute(select(User).where(User.id == current_user["sub"]))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "organization_id": str(user.organization_id) if user.organization_id else None,
        "is_active": user.is_active
    }


@router.post("/organizations", response_model=OrganizationResponse)
async def create_organization(
    org_data: OrganizationCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new organization"""
    
    org_id = str(uuid.uuid4())
    new_org = Organization(
        id=org_id,
        name=org_data.name,
        description=org_data.description,
        owner_id=current_user["sub"]
    )
    
    db.add(new_org)
    await db.commit()
    await db.refresh(new_org)
    
    return {
        "id": str(new_org.id),
        "name": new_org.name,
        "description": new_org.description,
        "owner_id": str(new_org.owner_id),
        "is_active": new_org.is_active
    }


@router.get("/organizations/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get organization details"""
    
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalars().first()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return {
        "id": str(org.id),
        "name": org.name,
        "description": org.description,
        "owner_id": str(org.owner_id),
        "is_active": org.is_active
    }


@router.get("/organizations")
async def get_user_organizations(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all organizations for current user (owned or member of)"""
    
    user_id = current_user["sub"]
    
    # Get organizations owned by user
    result = await db.execute(
        select(Organization).where(Organization.owner_id == user_id)
    )
    organizations = result.scalars().all()
    
    return [
        {
            "id": org.id,
            "name": org.name,
            "description": org.description,
            "owner_id": org.owner_id,
            "is_active": org.is_active,
            "role": "owner"
        }
        for org in organizations
    ]


@router.post("/invitations")
async def send_invitation(
    invitation_data: InvitationCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send invitation to join organization"""
    
    user_id = current_user["sub"]
    org_id = invitation_data.organization_id
    
    # Verify user owns the organization
    result = await db.execute(
        select(Organization).where(
            (Organization.id == org_id) & (Organization.owner_id == user_id)
        )
    )
    org = result.scalars().first()
    
    if not org:
        raise HTTPException(status_code=403, detail="You don't have permission to invite users to this organization")
    
    # Create invitation
    invitation_id = str(uuid.uuid4())
    new_invitation = Invitation(
        id=invitation_id,
        email=invitation_data.email,
        organization_id=org_id,
        role=invitation_data.role,
        invited_by=user_id,
        status="pending"
    )
    
    db.add(new_invitation)
    await db.commit()
    await db.refresh(new_invitation)
    
    # TODO: Send email to invitation_data.email with acceptance link
    
    return {
        "id": new_invitation.id,
        "email": new_invitation.email,
        "organization_id": new_invitation.organization_id,
        "role": new_invitation.role,
        "status": new_invitation.status,
        "invited_by": new_invitation.invited_by,
        "created_at": new_invitation.created_at.isoformat()
    }


@router.get("/invitations")
async def get_user_invitations(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get pending invitations for current user"""
    
    email = current_user["email"]
    
    # Get pending invitations for this email
    result = await db.execute(
        select(Invitation).where(
            (Invitation.email == email) & (Invitation.status == "pending")
        )
    )
    invitations = result.scalars().all()
    
    return [
        {
            "id": inv.id,
            "email": inv.email,
            "organization_id": inv.organization_id,
            "role": inv.role,
            "status": inv.status,
            "invited_by": inv.invited_by,
            "created_at": inv.created_at.isoformat()
        }
        for inv in invitations
    ]


@router.post("/invitations/{invitation_id}/accept")
async def accept_invitation(
    invitation_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Accept organization invitation"""
    
    user_id = current_user["sub"]
    email = current_user["email"]
    
    # Get invitation
    result = await db.execute(
        select(Invitation).where(Invitation.id == invitation_id)
    )
    invitation = result.scalars().first()
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    if invitation.email != email:
        raise HTTPException(status_code=403, detail="This invitation is not for you")
    
    if invitation.status != "pending":
        raise HTTPException(status_code=400, detail="Invitation is no longer pending")
    
    # Update user's organization
    user = await db.get(User, user_id)
    user.organization_id = invitation.organization_id
    user.role = invitation.role
    
    # Update invitation status
    invitation.status = "accepted"
    
    await db.commit()
    
    # Sync user to all microservices with new organization
    sync_data = {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "organization_id": user.organization_id
    }
    sync_results = await user_sync_service.sync_user_to_all_services(sync_data)
    logger.info(f"User sync results after invitation acceptance: {sync_results}")
    
    return {
        "message": "Invitation accepted",
        "organization_id": invitation.organization_id,
        "role": invitation.role
    }


@router.post("/invitations/{invitation_id}/reject")
async def reject_invitation(
    invitation_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reject organization invitation"""
    
    email = current_user["email"]
    
    # Get invitation
    result = await db.execute(
        select(Invitation).where(Invitation.id == invitation_id)
    )
    invitation = result.scalars().first()
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    if invitation.email != email:
        raise HTTPException(status_code=403, detail="This invitation is not for you")
    
    if invitation.status != "pending":
        raise HTTPException(status_code=400, detail="Invitation is no longer pending")
    
    # Update invitation status
    invitation.status = "rejected"
    await db.commit()
    
    return {"message": "Invitation rejected"}
