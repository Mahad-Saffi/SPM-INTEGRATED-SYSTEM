import uuid
from sqlalchemy import Column, String, ForeignKey, TIMESTAMP, func, Text, Index, UUID as SQLUUID
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.user import Base

class Organization(Base):
    """Organization model - synced from Orchestrator"""
    __tablename__ = 'organizations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    orchestrator_org_id = Column(UUID(as_uuid=True), unique=True, index=True, nullable=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    is_active = Column(SQLUUID, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id])
    projects = relationship("Project", back_populates="organization", cascade="all, delete-orphan")
    members = relationship("OrganizationMember", cascade="all, delete-orphan")


class OrganizationMember(Base):
    """Organization member model - tracks users in organizations"""
    __tablename__ = 'organization_members'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    role = Column(String(50), nullable=False, default='member')  # owner, admin, manager, member
    description = Column(Text, nullable=True)
    invited_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

    # Relationships
    organization = relationship("Organization", foreign_keys=[organization_id])
    user = relationship("User", foreign_keys=[user_id], backref="organization_memberships")
    inviter = relationship("User", foreign_keys=[invited_by])

    # Indexes
    __table_args__ = (
        Index('idx_org_member_unique', 'organization_id', 'user_id', unique=True),
        Index('idx_org_member_org', 'organization_id'),
        Index('idx_org_member_user', 'user_id'),
    )
