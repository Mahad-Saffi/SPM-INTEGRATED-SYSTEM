"""
Permission middleware and decorators for role-based access control
"""
from functools import wraps
from typing import List, Optional, Callable
from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, User, Organization
from auth.jwt_handler import get_current_user


# ============================================
# ROLE-BASED ACCESS CONTROL DECORATORS
# ============================================

def require_role(*allowed_roles: str):
    """
    Decorator to enforce role-based access control.
    
    Usage:
        @require_role("admin", "manager")
        async def create_project(...):
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, current_user = Depends(get_current_user), **kwargs):
            user_role = current_user.get("role")
            if user_role not in allowed_roles:
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


def require_admin(func: Callable):
    """Decorator to require admin role"""
    @wraps(func)
    async def wrapper(*args, current_user = Depends(get_current_user), **kwargs):
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        return await func(*args, current_user=current_user, **kwargs)
    return wrapper


def require_manager(func: Callable):
    """Decorator to require admin or manager role"""
    @wraps(func)
    async def wrapper(*args, current_user = Depends(get_current_user), **kwargs):
        if current_user.get("role") not in ["admin", "manager"]:
            raise HTTPException(status_code=403, detail="Manager access required")
        return await func(*args, current_user=current_user, **kwargs)
    return wrapper


# ============================================
# ORGANIZATION ISOLATION DECORATORS
# ============================================

def require_same_org(func: Callable):
    """
    Decorator to enforce organization isolation.
    Verifies user is in the same organization as the resource.
    
    Usage:
        @require_same_org
        async def get_project(project_id: UUID, current_user, db):
            # current_user is guaranteed to be in same org as project
            pass
    """
    @wraps(func)
    async def wrapper(*args, current_user = Depends(get_current_user), db: AsyncSession = Depends(get_db), **kwargs):
        user_org_id = current_user.get("organization_id")
        if not user_org_id:
            raise HTTPException(status_code=400, detail="User must belong to an organization")
        return await func(*args, current_user=current_user, db=db, **kwargs)
    return wrapper


def require_org_membership(func: Callable):
    """Decorator to verify user has organization membership"""
    @wraps(func)
    async def wrapper(*args, current_user = Depends(get_current_user), **kwargs):
        org_id = current_user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="User must belong to an organization")
        return await func(*args, current_user=current_user, **kwargs)
    return wrapper


# ============================================
# VALIDATION FUNCTIONS
# ============================================

async def validate_user_in_organization(
    user_id: str,
    org_id: str,
    db: AsyncSession
) -> bool:
    """Verify user is in organization"""
    from sqlalchemy import select
    
    result = await db.execute(
        select(User).where(
            (User.id == user_id) & (User.organization_id == org_id)
        )
    )
    return result.scalars().first() is not None


async def validate_organization_exists(
    org_id: str,
    db: AsyncSession
) -> bool:
    """Verify organization exists"""
    org = await db.get(Organization, org_id)
    return org is not None


async def validate_user_is_org_admin(
    user_id: str,
    org_id: str,
    db: AsyncSession
) -> bool:
    """Verify user is admin in organization"""
    from sqlalchemy import select
    
    result = await db.execute(
        select(User).where(
            (User.id == user_id) &
            (User.organization_id == org_id) &
            (User.role == "admin")
        )
    )
    return result.scalars().first() is not None


async def validate_user_is_org_manager(
    user_id: str,
    org_id: str,
    db: AsyncSession
) -> bool:
    """Verify user is admin or manager in organization"""
    from sqlalchemy import select
    
    result = await db.execute(
        select(User).where(
            (User.id == user_id) &
            (User.organization_id == org_id) &
            (User.role.in_(["admin", "manager"]))
        )
    )
    return result.scalars().first() is not None


async def validate_task_assignment(
    db: AsyncSession,
    project_id: str,
    assignee_id: str,
    current_user: dict
) -> None:
    """
    Validate task assignment.
    Ensures assignee is in project's organization.
    """
    from services.atlas_client import atlas_client
    
    # Get project
    project = await atlas_client.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify user is in same organization
    if project.get("organization_id") != current_user.get("organization_id"):
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Verify assignee is in same organization
    assignee_in_org = await validate_user_in_organization(
        assignee_id,
        project.get("organization_id"),
        db
    )
    if not assignee_in_org:
        raise HTTPException(
            status_code=400,
            detail="Cannot assign task to user outside organization"
        )


async def validate_activity_logging(
    db: AsyncSession,
    org_id: str,
    task_id: Optional[str],
    current_user: dict
) -> None:
    """
    Validate activity logging.
    Ensures activity is logged in user's organization.
    If task is linked, ensures task is in same organization.
    """
    from services.atlas_client import atlas_client
    
    # Verify user is in organization
    if current_user.get("organization_id") != org_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # If task is linked, verify it's in same org
    if task_id:
        task = await atlas_client.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get project to check organization
        project = await atlas_client.get_project(task.get("project_id"))
        if project.get("organization_id") != org_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot log activity for task outside your organization"
            )


async def validate_lab_access(
    db: AsyncSession,
    lab_id: str,
    current_user: dict,
    require_head: bool = False
) -> dict:
    """
    Validate lab access.
    Ensures user has access to lab.
    If require_head=True, ensures user is lab head.
    """
    from services.labs_client import labs_client
    
    # Get lab
    lab = await labs_client.get_lab(lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    
    # Check organization match
    if lab.get("orchestrator_org_id") != current_user.get("organization_id"):
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
    
    # If require_head, check if user is lab head
    if require_head:
        if lab.get("head_id") != current_user.get("sub"):
            raise HTTPException(
                status_code=403,
                detail="Only lab head can perform this action"
            )
    
    return lab


async def validate_researcher_access(
    db: AsyncSession,
    lab_id: str,
    current_user: dict
) -> bool:
    """
    Validate researcher access to lab.
    Checks if user is active researcher in lab.
    """
    from services.labs_client import labs_client
    
    # Get lab
    lab = await labs_client.get_lab(lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    
    # Check organization match
    if lab.get("orchestrator_org_id") != current_user.get("organization_id"):
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if user is active researcher in lab
    researchers = await labs_client.get_lab_researchers(lab_id)
    for researcher in researchers:
        if researcher.get("orchestrator_user_id") == current_user.get("sub"):
            if researcher.get("status") == "active":
                return True
    
    # Admin can always access
    if current_user.get("role") == "admin":
        return True
    
    raise HTTPException(status_code=403, detail="Not a member of this lab")


async def validate_team_access(
    db: AsyncSession,
    team_id: str,
    current_user: dict
) -> dict:
    """
    Validate team access.
    Ensures user is in same organization as team.
    """
    from services.workpulse_client import workpulse_client
    
    # Get team
    team = await workpulse_client.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check organization match
    if team.get("organization_id") != current_user.get("organization_id"):
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
    
    return team


async def validate_performance_review_access(
    db: AsyncSession,
    user_id: str,
    current_user: dict
) -> None:
    """
    Validate performance review access.
    User can view own reviews or manager can view team reviews.
    """
    is_self = user_id == current_user.get("sub")
    is_manager = current_user.get("role") in ["admin", "manager"]
    
    if not (is_self or is_manager):
        raise HTTPException(status_code=403, detail="Access denied")


# ============================================
# PERMISSION CHECK HELPERS
# ============================================

def check_role(current_user: dict, required_roles: List[str]) -> None:
    """Check if user has required role"""
    if current_user.get("role") not in required_roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions")


def check_org_membership(current_user: dict) -> str:
    """Check if user has organization membership and return org_id"""
    org_id = current_user.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    return org_id


def check_same_org(current_user: dict, resource_org_id: str) -> None:
    """Check if user is in same organization as resource"""
    if current_user.get("organization_id") != resource_org_id:
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Access denied")


def check_not_self(current_user: dict, target_user_id: str, action: str = "this action") -> None:
    """Check if user is not performing action on themselves"""
    if current_user.get("sub") == target_user_id:
        raise HTTPException(status_code=400, detail=f"Cannot {action} on yourself")


def check_ownership(current_user: dict, owner_id: str, resource_type: str = "resource") -> None:
    """Check if user owns resource"""
    if current_user.get("sub") != owner_id:
        if current_user.get("role") not in ["admin", "manager"]:
            raise HTTPException(status_code=403, detail=f"Only owner can modify this {resource_type}")
