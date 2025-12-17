from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from app.models.task import Task
from app.config.database import SessionLocal
import uuid
from datetime import datetime

class TaskService:
    async def get_tasks_for_user_in_project(self, project_id: str, user_id: str) -> list:
        async with SessionLocal() as session:
            # Convert project_id to UUID, handling both formats
            try:
                if isinstance(project_id, str):
                    # Add hyphens if missing
                    if len(project_id) == 32 and '-' not in project_id:
                        project_id = f"{project_id[:8]}-{project_id[8:12]}-{project_id[12:16]}-{project_id[16:20]}-{project_id[20:]}"
                    project_uuid = uuid.UUID(project_id)
                else:
                    project_uuid = project_id
                
                result = await session.execute(
                    select(Task).where(Task.project_id == project_uuid)
                )
                tasks = result.scalars().all()
                
                # Convert to dict for JSON serialization
                return [
                    {
                        "id": str(task.id),
                        "title": task.title,
                        "description": task.description,
                        "status": task.status,
                        "assignee_id": task.assignee_id,
                        "project_id": str(task.project_id),
                        "order": task.order,
                        "due_date": task.due_date.isoformat() if task.due_date else None,
                        "estimate_hours": task.estimate_hours,
                        "progress_percentage": task.progress_percentage,
                        "risk_level": task.risk_level
                    }
                    for task in tasks
                ]
            except Exception as e:
                print(f"Error getting tasks: {e}")
                return []

    async def complete_task(self, task_id: str, user_id: str) -> dict:
        """
        Mark a task as complete and automatically assign the next task to the user.
        """
        try:
            async with SessionLocal() as session:
                # Convert task_id to UUID, handling both formats
                if isinstance(task_id, str):
                    # Add hyphens if missing
                    if len(task_id) == 32 and '-' not in task_id:
                        task_id = f"{task_id[:8]}-{task_id[8:12]}-{task_id[12:16]}-{task_id[16:20]}-{task_id[20:]}"
                    task_uuid = uuid.UUID(task_id)
                else:
                    task_uuid = task_id
                
                user_id_int = int(user_id) if isinstance(user_id, str) else user_id
                
                # Get the task
                result = await session.execute(
                    select(Task).where(Task.id == task_uuid)
                )
                task = result.scalars().first()
                
                if not task:
                    raise ValueError(f"Task not found with id: {task_id}")
                
                # Mark as complete
                task.status = "Done"
                # Don't set updated_at manually, let the database handle it
                
                # Find next unassigned task in the same project
                next_task_result = await session.execute(
                    select(Task).where(
                        and_(
                            Task.project_id == task.project_id,
                            Task.status == "To Do",
                            Task.assignee_id.is_(None)
                        )
                    ).order_by(Task.order).limit(1)
                )
                next_task = next_task_result.scalars().first()
                
                # Auto-assign next task to the same user
                next_task_info = None
                if next_task:
                    next_task.assignee_id = user_id_int
                    next_task.status = "In Progress"
                    next_task_info = {
                        "id": str(next_task.id),
                        "title": next_task.title
                    }
                
                # Commit changes
                await session.commit()
                
                # Refresh to get updated values
                await session.refresh(task)
                if next_task:
                    await session.refresh(next_task)
                
                # Create notification for next task assignment
                if next_task:
                    from app.services.notification_service import notification_service
                    await notification_service.create_notification(
                        user_id=user_id_int,
                        notification_type="task_assigned",
                        title="New Task Assigned",
                        message=f"You've been assigned: {next_task.title}",
                        link=f"/task-board"
                    )
                
                return {
                    "id": str(task.id),
                    "title": task.title,
                    "status": task.status,
                    "next_task": next_task_info
                }
        except Exception as e:
            print(f"Error completing task: {e}")
            raise

    async def update_task_details(self, task_id: str, updates: dict) -> dict:
        """Update task estimate, progress, or due date"""
        try:
            async with SessionLocal() as session:
                # Convert task_id to UUID
                if isinstance(task_id, str):
                    if len(task_id) == 32 and '-' not in task_id:
                        task_id = f"{task_id[:8]}-{task_id[8:12]}-{task_id[12:16]}-{task_id[16:20]}-{task_id[20:]}"
                    task_uuid = uuid.UUID(task_id)
                else:
                    task_uuid = task_id
                
                result = await session.execute(
                    select(Task).where(Task.id == task_uuid)
                )
                task = result.scalars().first()
                
                if not task:
                    raise ValueError(f"Task not found with id: {task_id}")
                
                # Update fields
                if 'estimate_hours' in updates:
                    task.estimate_hours = updates['estimate_hours']
                if 'progress_percentage' in updates:
                    task.progress_percentage = max(0, min(100, updates['progress_percentage']))
                if 'due_date' in updates:
                    from datetime import datetime
                    task.due_date = datetime.fromisoformat(updates['due_date'].replace('Z', '+00:00'))
                if 'status' in updates:
                    task.status = updates['status']
                if 'assigned_to' in updates:
                    task.assignee_id = updates['assigned_to']
                
                # Recalculate risk
                from app.services.risk_service import risk_service
                task.risk_level = risk_service.calculate_task_risk(task)
                
                await session.commit()
                await session.refresh(task)
                
                return {
                    "id": str(task.id),
                    "title": task.title,
                    "status": task.status,
                    "assigned_to": task.assignee_id,
                    "estimate_hours": task.estimate_hours,
                    "progress_percentage": task.progress_percentage,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "risk_level": task.risk_level
                }
        except Exception as e:
            print(f"Error updating task: {e}")
            raise
    
    async def bulk_assign_tasks(self, task_ids: list[str], assigned_to: int) -> dict:
        """Assign multiple tasks to a user at once"""
        success_count = 0
        failed_count = 0
        failed_tasks = []
        
        async with SessionLocal() as session:
            for task_id in task_ids:
                try:
                    # Convert task_id to UUID
                    if isinstance(task_id, str):
                        if len(task_id) == 32 and '-' not in task_id:
                            task_id = f"{task_id[:8]}-{task_id[8:12]}-{task_id[12:16]}-{task_id[16:20]}-{task_id[20:]}"
                        task_uuid = uuid.UUID(task_id)
                    else:
                        task_uuid = task_id
                    
                    result = await session.execute(
                        select(Task).where(Task.id == task_uuid)
                    )
                    task = result.scalars().first()
                    
                    if task:
                        task.assignee_id = assigned_to
                        success_count += 1
                    else:
                        failed_count += 1
                        failed_tasks.append({"task_id": str(task_id), "reason": "Task not found"})
                
                except Exception as e:
                    failed_count += 1
                    failed_tasks.append({"task_id": str(task_id), "reason": str(e)})
            
            await session.commit()
        
        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "failed_tasks": failed_tasks
        }

task_service = TaskService()
