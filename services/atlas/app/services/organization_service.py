from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.organization import Organization, OrganizationMember
from app.models.user import User
from app.config.database import SessionLocal
from app.services.auth_service import auth_service
import uuid

class OrganizationService:
    
    async def create_organization(self, name: str, description: str, owner_id: int):
        """Create a new organization"""
        async with SessionLocal() as session:
            org = Organization(
                name=name,
                description=description,
                owner_id=owner_id
            )
            session.add(org)
            await session.flush()  # Get org.id before creating member
            
            # Add owner as first member
            member = OrganizationMember(
                organization_id=org.id,
                user_id=owner_id,
                role="owner",
                description="Organization owner",
                invited_by=owner_id
            )
            session.add(member)
            
            await session.commit()
            await session.refresh(org)
            return org
    
    async def get_user_organization(self, user_id: int):
        """Get the organization where user is a member"""
        async with SessionLocal() as session:
            result = await session.execute(
                select(Organization)
                .join(OrganizationMember)
                .where(OrganizationMember.user_id == user_id)
                .options(selectinload(Organization.members))
            )
            return result.scalars().first()
    
    async def get_organization_members(self, organization_id: str):
        """Get all members of an organization"""
        import uuid as uuid_lib
        async with SessionLocal() as session:
            # Convert string to UUID if needed
            org_uuid = uuid_lib.UUID(organization_id) if isinstance(organization_id, str) else organization_id
            result = await session.execute(
                select(OrganizationMember)
                .where(OrganizationMember.organization_id == org_uuid)
                .options(
                    selectinload(OrganizationMember.user),
                    selectinload(OrganizationMember.inviter)
                )
            )
            return result.scalars().all()
    
    async def add_team_member(
        self, 
        organization_id: str,
        email: str,
        password: str,
        username: str,
        role: str,
        description: str,
        invited_by: int
    ):
        """Add a new team member to organization"""
        import uuid as uuid_lib
        async with SessionLocal() as session:
            # Convert string to UUID if needed
            org_uuid = uuid_lib.UUID(organization_id) if isinstance(organization_id, str) else organization_id
            # Check if user with email already exists
            result = await session.execute(
                select(User).where(User.email == email)
            )
            existing_user = result.scalars().first()
            
            if existing_user:
                # User exists, just add to organization
                user = existing_user
            else:
                # Create new user
                hashed_password = auth_service.get_password_hash(password)
                user = User(
                    username=username,
                    email=email,
                    password_hash=hashed_password,
                    role=role,
                    invited_by=invited_by,
                    avatar_url=f"https://ui-avatars.com/api/?name={username}&background=random"
                )
                session.add(user)
                await session.flush()  # Get user.id
            
            # Check if already a member
            result = await session.execute(
                select(OrganizationMember).where(
                    OrganizationMember.organization_id == org_uuid,
                    OrganizationMember.user_id == user.id
                )
            )
            existing_member = result.scalars().first()
            
            if existing_member:
                raise ValueError("User is already a member of this organization")
            
            # Add as organization member
            member = OrganizationMember(
                organization_id=org_uuid,
                user_id=user.id,
                role=role,
                description=description,
                invited_by=invited_by
            )
            session.add(member)
            
            await session.commit()
            await session.refresh(member)
            await session.refresh(user)
            
            return {
                "user": user,
                "member": member
            }
    
    async def remove_team_member(self, organization_id: str, user_id: int):
        """Remove a team member from organization"""
        import uuid as uuid_lib
        async with SessionLocal() as session:
            # Convert string to UUID if needed
            org_uuid = uuid_lib.UUID(organization_id) if isinstance(organization_id, str) else organization_id
            result = await session.execute(
                select(OrganizationMember).where(
                    OrganizationMember.organization_id == org_uuid,
                    OrganizationMember.user_id == user_id
                )
            )
            member = result.scalars().first()
            
            if not member:
                raise ValueError("Member not found")
            
            await session.delete(member)
            await session.commit()
            
            return {"message": "Member removed successfully"}
    
    async def is_organization_owner(self, organization_id: str, user_id: int) -> bool:
        """Check if user is the owner of the organization"""
        import uuid as uuid_lib
        async with SessionLocal() as session:
            # Convert string to UUID if needed
            org_uuid = uuid_lib.UUID(organization_id) if isinstance(organization_id, str) else organization_id
            result = await session.execute(
                select(Organization).where(
                    Organization.id == org_uuid,
                    Organization.owner_id == user_id
                )
            )
            return result.scalars().first() is not None
    
    async def get_organization_by_id(self, organization_id: str):
        """Get organization by ID"""
        import uuid as uuid_lib
        async with SessionLocal() as session:
            # Convert string to UUID if needed
            org_uuid = uuid_lib.UUID(organization_id) if isinstance(organization_id, str) else organization_id
            result = await session.execute(
                select(Organization)
                .where(Organization.id == org_uuid)
                .options(selectinload(Organization.members))
            )
            return result.scalars().first()

organization_service = OrganizationService()
