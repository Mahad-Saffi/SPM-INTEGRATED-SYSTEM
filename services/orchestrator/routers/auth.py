"""
Authentication router - handles login, registration, and token management
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import logging

from database import get_db, User, Organization
from auth.jwt_handler import (
    create_access_token, 
    verify_password, 
    get_password_hash, 
    get_current_user, 
    create_user_token,
    generate_user_id
)
from auth.models import UserCreate, UserResponse, TokenResponse, OrganizationCreate, OrganizationResponse, UserLogin
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
    token = create_user_token(user_id, user_data.email, user_data.name, user_data.role)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "name": new_user.name,
            "role": new_user.role,
            "organization_id": new_user.organization_id,
            "is_active": new_user.is_active
        },
        "user_id": new_user.id
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
    
    # Create token
    token = create_user_token(user.id, user.email, user.name, user.role)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "organization_id": user.organization_id,
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
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "organization_id": user.organization_id,
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
        "id": new_org.id,
        "name": new_org.name,
        "description": new_org.description,
        "owner_id": new_org.owner_id,
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
        "id": org.id,
        "name": org.name,
        "description": org.description,
        "owner_id": org.owner_id,
        "is_active": org.is_active
    }
