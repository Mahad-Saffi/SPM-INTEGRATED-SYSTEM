"""
Data isolation middleware - ensures organization-level data isolation
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException

from database import User, Organization


# ============================================
# ORGANIZATION ISOLATION VALIDATORS
# ============================================

async def verify_user_org_isolation(
    db: AsyncSession,
    user_id: str,
    org_id: str
) -> None:
    """
    Verify user belongs to organization.
    Prevents cross-org access.
    """
    result = await db.execute(
        select(User).where(
            (User.id == user_id) &
            (User.organization_id == org_id)
        )
    )
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=403,
            detail="User does not belong to this organization"
        )


async def verify_org_exists(
    db: AsyncSession,
    org_id: str
) -> Organization:
    """
    Verify organization exists.
    """
    org = await db.get(Organization, org_id)
    
    if not org:
        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )
    
    return org


async def verify_org_is_active(
    db: AsyncSession,
    org_id: str
) -> None:
    """
    Verify organization is active.
    Prevents access to deleted organizations.
    """
    org = await db.get(Organization, org_id)
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    if not org.is_active:
        raise HTTPException(status_code=403, detail="Organization is inactive")


async def verify_user_is_active(
    db: AsyncSession,
    user_id: str
) -> User:
    """
    Verify user is active.
    Prevents access by inactive users.
    """
    user = await db.get(User, user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive")
    
    return user


async def verify_multiple_users_same_org(
    db: AsyncSession,
    user_ids: List[str],
    org_id: str
) -> None:
    """
    Verify multiple users belong to same organization.
    Used for bulk operations like team creation.
    """
    result = await db.execute(
        select(User).where(
            (User.id.in_(user_ids)) &
            (User.organization_id == org_id)
        )
    )
    users = result.scalars().all()
    
    if len(users) != len(user_ids):
        raise HTTPException(
            status_code=400,
            detail="Not all users belong to this organization"
        )


# ============================================
# RESOURCE ISOLATION VALIDATORS
# ============================================

async def verify_project_org_isolation(
    db: AsyncSession,
    project_id: str,
    org_id: str
) -> dict:
    """
    Verify project belongs to organization.
    Used by Atlas service.
    """
    from services.atlas_client import atlas_client
    
    project = await atlas_client.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.get("organization_id") != org_id:
        raise HTTPException(
            status_code=403,
            detail="Project does not belong to this organization"
        )
    
    return project


async def verify_lab_org_isolation(
    db: AsyncSession,
    lab_id: str,
    org_id: str
) -> dict:
    """
    Verify lab belongs to organization.
    Used by Labs service.
    """
    from services.labs_client import labs_client
    
    lab = await labs_client.get_lab(lab_id)
    
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    
    if lab.get("orchestrator_org_id") != org_id:
        raise HTTPException(
            status_code=403,
            detail="Lab does not belong to this organization"
        )
    
    return lab


async def verify_team_org_isolation(
    db: AsyncSession,
    team_id: str,
    org_id: str
) -> dict:
    """
    Verify team belongs to organization.
    Used by WorkPulse service.
    """
    from services.workpulse_client import workpulse_client
    
    team = await workpulse_client.get_team(team_id)
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if team.get("organization_id") != org_id:
        raise HTTPException(
            status_code=403,
            detail="Team does not belong to this organization"
        )
    
    return team


# ============================================
# CROSS-ORG PREVENTION
# ============================================

async def prevent_cross_org_project_access(
    db: AsyncSession,
    project_id: str,
    user_org_id: str
) -> None:
    """
    Prevent user from accessing projects outside their organization.
    """
    from services.atlas_client import atlas_client
    
    project = await atlas_client.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.get("organization_id") != user_org_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot access projects outside your organization"
        )


async def prevent_cross_org_lab_access(
    db: AsyncSession,
    lab_id: str,
    user_org_id: str
) -> None:
    """
    Prevent user from accessing labs outside their organization.
    """
    from services.labs_client import labs_client
    
    lab = await labs_client.get_lab(lab_id)
    
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    
    if lab.get("orchestrator_org_id") != user_org_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot access labs outside your organization"
        )


async def prevent_cross_org_team_access(
    db: AsyncSession,
    team_id: str,
    user_org_id: str
) -> None:
    """
    Prevent user from accessing teams outside their organization.
    """
    from services.workpulse_client import workpulse_client
    
    team = await workpulse_client.get_team(team_id)
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if team.get("organization_id") != user_org_id:
        raise HTTPException(
            status_code=403,
            detail="Cannot access teams outside your organization"
        )


async def prevent_cross_org_task_assignment(
    db: AsyncSession,
    project_id: str,
    assignee_id: str,
    user_org_id: str
) -> None:
    """
    Prevent assigning tasks to users outside organization.
    """
    from services.atlas_client import atlas_client
    
    # Verify project is in user's org
    project = await atlas_client.get_project(project_id)
    if project.get("organization_id") != user_org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify assignee is in user's org
    assignee = await db.get(User, assignee_id)
    if not assignee or assignee.organization_id != user_org_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot assign task to user outside organization"
        )


async def prevent_cross_org_activity_logging(
    db: AsyncSession,
    task_id: str,
    user_org_id: str
) -> None:
    """
    Prevent logging activities for tasks outside organization.
    """
    from services.atlas_client import atlas_client
    
    task = await atlas_client.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get project to check organization
    project = await atlas_client.get_project(task.get("project_id"))
    if project.get("organization_id") != user_org_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot log activity for task outside your organization"
        )


# ============================================
# BULK OPERATION ISOLATION
# ============================================

async def verify_bulk_user_org_isolation(
    db: AsyncSession,
    user_ids: List[str],
    org_id: str
) -> List[User]:
    """
    Verify all users in bulk operation belong to organization.
    """
    result = await db.execute(
        select(User).where(
            (User.id.in_(user_ids)) &
            (User.organization_id == org_id)
        )
    )
    users = result.scalars().all()
    
    if len(users) != len(user_ids):
        missing_count = len(user_ids) - len(users)
        raise HTTPException(
            status_code=400,
            detail=f"{missing_count} user(s) do not belong to this organization"
        )
    
    return users


async def verify_bulk_project_org_isolation(
    db: AsyncSession,
    project_ids: List[str],
    org_id: str
) -> None:
    """
    Verify all projects in bulk operation belong to organization.
    """
    from services.atlas_client import atlas_client
    
    for project_id in project_ids:
        project = await atlas_client.get_project(project_id)
        if not project or project.get("organization_id") != org_id:
            raise HTTPException(
                status_code=400,
                detail=f"Project {project_id} does not belong to this organization"
            )


# ============================================
# AUDIT LOGGING
# ============================================

async def log_cross_org_access_attempt(
    db: AsyncSession,
    user_id: str,
    user_org_id: str,
    resource_org_id: str,
    resource_type: str,
    resource_id: str
) -> None:
    """
    Log cross-organization access attempts for security audit.
    """
    # This would be implemented with a proper audit logging system
    # For now, just log to console
    print(f"⚠️ SECURITY: Cross-org access attempt detected!")
    print(f"   User: {user_id} (Org: {user_org_id})")
    print(f"   Resource: {resource_type} {resource_id} (Org: {resource_org_id})")


async def log_inactive_user_access_attempt(
    db: AsyncSession,
    user_id: str
) -> None:
    """
    Log access attempts by inactive users.
    """
    print(f"⚠️ SECURITY: Inactive user access attempt!")
    print(f"   User: {user_id}")


async def log_inactive_org_access_attempt(
    db: AsyncSession,
    org_id: str,
    user_id: str
) -> None:
    """
    Log access attempts to inactive organizations.
    """
    print(f"⚠️ SECURITY: Inactive organization access attempt!")
    print(f"   Organization: {org_id}")
    print(f"   User: {user_id}")
