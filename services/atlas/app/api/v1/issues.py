from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from app.core.security import get_current_user
from app.services.issue_service import issue_service

router = APIRouter()

class CreateIssueRequest(BaseModel):
    project_id: str
    title: str
    description: str
    issue_type: str = 'blocker'
    priority: str = 'medium'
    task_id: str = None

class AssignIssueRequest(BaseModel):
    assignee_id: int

class ResolveIssueRequest(BaseModel):
    resolution: str

@router.post("")
async def create_issue(
    request: CreateIssueRequest,
    current_user: dict = Depends(get_current_user)
):
    """Report a new issue"""
    issue = await issue_service.create_issue(
        project_id=request.project_id,
        reporter_id=current_user['id'],
        title=request.title,
        description=request.description,
        issue_type=request.issue_type,
        priority=request.priority,
        task_id=request.task_id
    )
    return issue

@router.get("/project/{project_id}")
async def get_project_issues(
    project_id: str,
    status: str = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get all issues for a project"""
    issues = await issue_service.get_project_issues(project_id, status)
    return issues

@router.post("/{issue_id}/assign")
async def assign_issue(
    issue_id: int,
    request: AssignIssueRequest,
    current_user: dict = Depends(get_current_user)
):
    """Assign an issue to a user (triage)"""
    result = await issue_service.assign_issue(
        issue_id=issue_id,
        assignee_id=request.assignee_id,
        assigner_id=current_user['id']
    )
    return result

@router.post("/{issue_id}/resolve")
async def resolve_issue(
    issue_id: int,
    request: ResolveIssueRequest,
    current_user: dict = Depends(get_current_user)
):
    """Resolve an issue"""
    result = await issue_service.resolve_issue(
        issue_id=issue_id,
        resolution=request.resolution,
        resolver_id=current_user['id']
    )
    return result
