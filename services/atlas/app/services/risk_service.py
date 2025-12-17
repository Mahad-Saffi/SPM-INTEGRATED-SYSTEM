from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from app.models.task import Task
from app.config.database import SessionLocal
from datetime import datetime, timedelta
from app.services.notification_service import notification_service

class RiskService:
    def calculate_task_risk(self, task: Task) -> str:
        """
        Calculate risk level for a task based on:
        - Due date proximity
        - Progress vs time elapsed
        - Status
        """
        if task.status == 'Done':
            return 'low'
        
        risk_score = 0
        
        # Check due date
        if task.due_date:
            now = datetime.utcnow()
            days_until_due = (task.due_date.replace(tzinfo=None) - now).days
            
            if days_until_due < 0:
                # Overdue
                risk_score += 50
            elif days_until_due <= 1:
                # Due within 1 day
                risk_score += 30
            elif days_until_due <= 3:
                # Due within 3 days
                risk_score += 20
            elif days_until_due <= 7:
                # Due within a week
                risk_score += 10
        
        # Check progress
        if task.progress_percentage < 25 and task.status == 'In Progress':
            risk_score += 15
        elif task.progress_percentage < 50 and task.status == 'In Progress':
            risk_score += 10
        
        # Check if task is stuck (in progress but no progress)
        if task.status == 'In Progress' and task.progress_percentage == 0:
            risk_score += 20
        
        # Determine risk level
        if risk_score >= 40:
            return 'high'
        elif risk_score >= 20:
            return 'medium'
        else:
            return 'low'

    async def detect_delays_and_update_risks(self) -> dict:
        """
        Scan all active tasks and update risk levels.
        Send notifications for high-risk tasks.
        """
        async with SessionLocal() as session:
            # Get all non-completed tasks
            result = await session.execute(
                select(Task).where(Task.status.in_(['To Do', 'In Progress']))
            )
            tasks = result.scalars().all()
            
            high_risk_count = 0
            medium_risk_count = 0
            notifications_sent = 0
            
            for task in tasks:
                old_risk = task.risk_level
                new_risk = self.calculate_task_risk(task)
                
                # Update risk level if changed
                if old_risk != new_risk:
                    task.risk_level = new_risk
                    
                    # Send notification if risk increased to high
                    if new_risk == 'high' and old_risk != 'high' and task.assignee_id:
                        await notification_service.create_notification(
                            user_id=task.assignee_id,
                            notification_type='task_at_risk',
                            title='⚠️ Task At Risk',
                            message=f'Task "{task.title}" is at high risk of delay',
                            link='/task-board'
                        )
                        notifications_sent += 1
                
                if new_risk == 'high':
                    high_risk_count += 1
                elif new_risk == 'medium':
                    medium_risk_count += 1
            
            await session.commit()
            
            return {
                'tasks_scanned': len(tasks),
                'high_risk': high_risk_count,
                'medium_risk': medium_risk_count,
                'notifications_sent': notifications_sent
            }

    async def get_project_risks(self, project_id: str) -> dict:
        """Get risk summary for a project"""
        async with SessionLocal() as session:
            import uuid
            
            # Convert project_id to UUID
            if isinstance(project_id, str):
                if len(project_id) == 32 and '-' not in project_id:
                    project_id = f"{project_id[:8]}-{project_id[8:12]}-{project_id[12:16]}-{project_id[16:20]}-{project_id[20:]}"
                project_uuid = uuid.UUID(project_id)
            else:
                project_uuid = project_id
            
            result = await session.execute(
                select(Task).where(
                    and_(
                        Task.project_id == project_uuid,
                        Task.status.in_(['To Do', 'In Progress'])
                    )
                )
            )
            tasks = result.scalars().all()
            
            high_risk = [t for t in tasks if t.risk_level == 'high']
            medium_risk = [t for t in tasks if t.risk_level == 'medium']
            low_risk = [t for t in tasks if t.risk_level == 'low']
            
            return {
                'total_active_tasks': len(tasks),
                'high_risk_count': len(high_risk),
                'medium_risk_count': len(medium_risk),
                'low_risk_count': len(low_risk),
                'high_risk_tasks': [
                    {
                        'id': str(t.id),
                        'title': t.title,
                        'due_date': t.due_date.isoformat() if t.due_date else None,
                        'progress': t.progress_percentage
                    }
                    for t in high_risk
                ]
            }

risk_service = RiskService()
