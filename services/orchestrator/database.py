"""
Database configuration and session management
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timedelta
from config import settings
import uuid

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,
)

# Create session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create base class for models
Base = declarative_base()


async def get_db():
    """Dependency for getting database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ============================================
# CORE MODELS
# ============================================

class User(Base):
    """User model - central user management"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(200), nullable=False)
    role = Column(String(50), default="member")  # admin, manager, member
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - explicitly specify foreign_keys to avoid ambiguity
    organization = relationship("Organization", foreign_keys=[organization_id], back_populates="members")
    owned_organizations = relationship("Organization", foreign_keys="Organization.owner_id", back_populates="owner")
    invitations_sent = relationship("Invitation", foreign_keys="Invitation.invited_by", back_populates="invited_by_user")
    
    # Unique constraint: user can only be in one organization
    __table_args__ = (
        Index('idx_user_single_org', 'id', 'organization_id', unique=True, postgresql_where=organization_id.isnot(None)),
    )


class Organization(Base):
    """Organization model for multi-tenancy"""
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_organizations")
    members = relationship("User", foreign_keys=[User.organization_id], back_populates="organization")
    invitations = relationship("Invitation", back_populates="organization")


class Invitation(Base):
    """Organization invitation model"""
    __tablename__ = "invitations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), index=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    role = Column(String(50), default="member")  # admin, manager, member
    status = Column(String(20), default="pending")  # pending, accepted, rejected
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="invitations")
    invited_by_user = relationship("User", foreign_keys=[invited_by], back_populates="invitations_sent")
    
    # Unique constraint: one pending invitation per email per org
    __table_args__ = (
        Index('idx_invitation_unique', 'email', 'organization_id', unique=True, postgresql_where=status == 'pending'),
    )


class ServiceHealth(Base):
    """Track health status of microservices"""
    __tablename__ = "service_health"
    
    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String(50), unique=True, index=True)
    status = Column(String(20), default="unknown")  # healthy, unhealthy, unreachable
    last_checked = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    error_message = Column(String(500), nullable=True)
