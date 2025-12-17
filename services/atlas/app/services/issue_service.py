from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, desc
from app.models.issue import Issue
from app.config.database import SessionLocal
from app.services.notification_service import notification_service
from datetime import datetime
import uuid

class IssueService:
    async def create_issue(
        self,
        project_id: str,
        reporter_id: int,
        title: str,
        description: str,
        issue_type: str = 'blocker',
        priority: str = 'medium',
        task_id: str = None
    ) -> dict:
        """Create a new issue"""
        async with SessionLocal() as session:
            # Convert project_id to UUID
            if isinstance(project_id, str):
                if len(project_id) == 32 and '-' not in project_id:
                    project_id = f"{project_id[:8]}-{project_id[8:12]}-{project_id[12:16]}-{project_id[16:20]}-{project_id[20:]}"
                project_uuid = uuid.UUID(project_id)
            else:
                project_uuid = project_id
            
            # Convert task_id if provided
            task_uuid = None
            if task_id:
                if isinstance(task_id, str):
                    if len(task_id) == 32 and '-' not in task_id:
                        task_id = f"{task_id[:8]}-{task_id[8:12]}-{task_id[12:16]}-{task_id[16:20]}-{task_id[20:]}"
                    task_uuid = uuid.UUID(task_id)
            
            issue = Issue(
                project_id=project_uuid,
                task_id=task_uuid,
                reporter_id=reporter_id,
                title=title,
                description=description,
                issue_type=issue_type,
                priority=priority
            )
            
            session.add(issue)
            await session.commit()
            await session.refresh(issue)
            
            # Notify project lead (get project owner)
            from app.models.project import Project
            result = await session.execute(
                select(Project).where(Project.id == project_uuid)
            )
            project = result.scalars().first()
            
            if project and project.owner_id != reporter_id:
                await notification_service.create_notification(
                    user_id=project.owner_id,
                    notification_type='new_issue',
                    title=f'🚨 New {issue_type.title()}: {title}',
                    message=f'Reported by user #{reporter_id}',
                    link=f'/issues/{issue.id}'
                )
            
            return {
                'id': issue.id,
                'title': issue.title,
                'description': issue.description,
                'issue_type': issue.issue_type,
                'priority': issue.priority,
                'status': issue.status,
                'created_at': issue.created_at.isoformat()
            }

    async def get_project_issues(self, project_id: str, status: str = None) -> list:
        """Get all issues for a project"""
        async with SessionLocal() as session:
            # Convert project_id to UUID
            if isinstance(project_id, str):
                if len(project_id) == 32 and '-' not in project_id:
                    project_id = f"{project_id[:8]}-{project_id[8:12]}-{project_id[12:16]}-{project_id[16:20]}-{project_id[20:]}"
                project_uuid = uuid.UUID(project_id)
            else:
                project_uuid = project_id
            
            query = select(Issue).where(Issue.project_id == project_uuid)
            
            if status:
                query = query.where(Issue.status == status)
            
            query = query.order_by(desc(Issue.created_at))
            result = await session.execute(query)
            issues = result.scalars().all()
            
            return [
                {
                    'id': issue.id,
                    'title': issue.title,
                    'description': issue.description,
                    'issue_type': issue.issue_type,
                    'priority': issue.priority,
                    'status': issue.status,
                    'reporter_id': issue.reporter_id,
                    'assignee_id': issue.assignee_id,
                    'created_at': issue.created_at.isoformat(),
                    'resolved_at': issue.resolved_at.isoformat() if issue.resolved_at else None
                }
                for issue in issues
            ]

    async def assign_issue(self, issue_id: int, assignee_id: int, assigner_id: int) -> dict:
        """Assign an issue to a user"""
        async with SessionLocal() as session:
            result = await session.execute(
                select(Issue).where(Issue.id == issue_id)
            )
            issue = result.scalars().first()
            
            if not issue:
                raise ValueError("Issue not found")
            
            issue.assignee_id = assignee_id
            issue.status = 'in_progress'
            
            await session.commit()
            await session.refresh(issue)
            
            # Notify assignee
            await notification_service.create_notification(
                user_id=assignee_id,
                notification_type='issue_assigned',
                title=f'📌 Issue Assigned: {issue.title}',
                message=f'{issue.issue_type.title()} - Priority: {issue.priority}',
                link=f'/issues/{issue.id}'
            )
            
            return {
                'id': issue.id,
                'assignee_id': issue.assignee_id,
                'status': issue.status
            }

    async def resolve_issue(self, issue_id: int, resolution: str, resolver_id: int) -> dict:
        """Resolve an issue"""
        async with SessionLocal() as session:
            result = await session.execute(
                select(Issue).where(Issue.id == issue_id)
            )
            issue = result.scalars().first()
            
            if not issue:
                raise ValueError("Issue not found")
            
            issue.status = 'resolved'
            issue.resolution = resolution
            issue.resolved_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(issue)
            
            # Notify reporter
            if issue.reporter_id != resolver_id:
                await notification_service.create_notification(
                    user_id=issue.reporter_id,
                    notification_type='issue_resolved',
                    title=f'✅ Issue Resolved: {issue.title}',
                    message=resolution[:100],
                    link=f'/issues/{issue.id}'
                )
            
            return {
                'id': issue.id,
                'status': issue.status,
                'resolution': issue.resolution,
                'resolved_at': issue.resolved_at.isoformat()
            }

issue_service = IssueService()
