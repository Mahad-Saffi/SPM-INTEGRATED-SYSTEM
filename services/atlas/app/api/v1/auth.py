from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.future import select
from app.models.user import User
from app.config.database import SessionLocal
from app.services.auth_service import auth_service
from datetime import timedelta

router = APIRouter()

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

@router.post("/register", response_model=Token)
async def register(user_data: UserRegister):
    """Register a new user with email and password"""
    from app.services.organization_service import organization_service
    
    async with SessionLocal() as session:
        # Check if user exists
        result = await session.execute(
            select(User).where(
                (User.email == user_data.email) | (User.username == user_data.username)
            )
        )
        existing_user = result.scalars().first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already registered"
            )
        
        # Create new user
        hashed_password = auth_service.get_password_hash(user_data.password)
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            avatar_url=f"https://ui-avatars.com/api/?name={user_data.username}&background=random"
        )
        
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        
        # Create organization for the new user
        try:
            await organization_service.create_organization(
                name=f"{new_user.username}'s Team",
                description=f"Organization for {new_user.username}",
                owner_id=new_user.id
            )
        except Exception as e:
            print(f"Warning: Could not create organization: {e}")
        
        # Create access token
        access_token = auth_service.create_access_token(
            data={
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "role": new_user.role,
                "avatar_url": new_user.avatar_url
            },
            expires_delta=timedelta(days=7)
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "avatar_url": new_user.avatar_url,
                "role": new_user.role
            }
        }

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """Login with email and password"""
    async with SessionLocal() as session:
        # Find user by email
        result = await session.execute(
            select(User).where(User.email == credentials.email)
        )
        user = result.scalars().first()
        
        if not user or not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Verify password
        if not auth_service.verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        # Create access token
        access_token = auth_service.create_access_token(
            data={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "avatar_url": user.avatar_url
            },
            expires_delta=timedelta(days=7)
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "avatar_url": user.avatar_url,
                "role": user.role
            }
        }

@router.post("/demo-login", response_model=Token)
async def demo_login():
    """Quick demo login - creates/uses a demo user"""
    async with SessionLocal() as session:
        # Check if demo user exists
        result = await session.execute(
            select(User).where(User.email == "demo@atlas.ai")
        )
        user = result.scalars().first()
        
        if not user:
            # Create demo user
            hashed_password = auth_service.get_password_hash("demo123")
            user = User(
                username="demo_user",
                email="demo@atlas.ai",
                password_hash=hashed_password,
                avatar_url="https://ui-avatars.com/api/?name=Demo+User&background=4a90e2"
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        
        # Create access token
        access_token = auth_service.create_access_token(
            data={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "avatar_url": user.avatar_url
            },
            expires_delta=timedelta(days=7)
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "avatar_url": user.avatar_url,
                "role": user.role
            }
        }
