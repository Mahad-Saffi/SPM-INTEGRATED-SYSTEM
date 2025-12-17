from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.project import Project
from app.models.epic import Epic
from app.models.story import Story
from app.models.task import Task
from app.config.database import SessionLocal
import uuid

class ProjectService:
    async def get_user_projects(self, user_id: int) -> list:
        """Get all projects for a user's organization"""
        from app.services.organization_service import organization_service
        
        async with SessionLocal() as session:
            # Get user's organization
            org = await organization_service.get_user_organization(user_id)
            if not org:
                return []
            
            # Get all projects in the organization (org.id is already a UUID object)
            result = await session.execute(
                select(Project).where(Project.organization_id == org.id)
            )
            projects = result.scalars().all()
            return [
                {
                    "id": str(project.id),
                    "name": project.name,
                    "description": project.description,
                    "created_at": project.created_at.isoformat() if project.created_at else None,
                }
                for project in projects
            ]
    async def create_project_from_plan(self, plan: dict, owner_id: str, organization_id = None) -> Project:
        """
        Create a project with epics, stories, and tasks from AI-generated plan.
        Expected plan structure:
        {
            "project_name": "...",
            "description": "...",
            "epics": [
                {
                    "name": "...",
                    "description": "...",
                    "stories": [
                        {
                            "name": "...",
                            "description": "...",
                            "tasks": ["task1", "task2", ...] or [{"title": "...", "description": "..."}]
                        }
                    ]
                }
            ]
        }
        """
        async with SessionLocal() as session:
            async with session.begin():
                # owner_id is an integer from the user table
                # No conversion needed
                
                # Create project
                project = Project(
                    name=plan.get('project_name', 'Untitled Project'),
                    description=plan.get('description', ''),
                    owner_id=owner_id,
                    organization_id=organization_id
                )
                session.add(project)
                await session.flush()  # Get project ID

                # Create epics, stories, and tasks
                epics_data = plan.get('epics', [])
                for epic_idx, epic_data in enumerate(epics_data):
                    epic = Epic(
                        project_id=project.id,
                        name=epic_data.get('name', f'Epic {epic_idx + 1}'),
                        description=epic_data.get('description', ''),
                        order=epic_idx
                    )
                    session.add(epic)
                    await session.flush()  # Get epic ID

                    # Create stories
                    stories_data = epic_data.get('stories', [])
                    for story_idx, story_data in enumerate(stories_data):
                        story = Story(
                            epic_id=epic.id,
                            name=story_data.get('name', f'Story {story_idx + 1}'),
                            description=story_data.get('description', ''),
                            order=story_idx
                        )
                        session.add(story)
                        await session.flush()  # Get story ID

                        # Create tasks
                        tasks_data = story_data.get('tasks', [])
                        for task_idx, task_data in enumerate(tasks_data):
                            # Handle both string and dict task formats
                            if isinstance(task_data, str):
                                task_title = task_data
                                task_desc = ''
                            else:
                                task_title = task_data.get('title', f'Task {task_idx + 1}')
                                task_desc = task_data.get('description', '')
                            
                            task = Task(
                                project_id=project.id,
                                story_id=story.id,
                                title=task_title,
                                description=task_desc,
                                status='To Do',
                                order=task_idx
                            )
                            session.add(task)

                await session.commit()
                return project

    async def get_project_epics(self, project_id: str) -> list:
        """Get all epics with their stories and tasks for a project"""
        async with SessionLocal() as session:
            # Convert project_id to UUID
            if isinstance(project_id, str):
                if len(project_id) == 32 and '-' not in project_id:
                    project_id = f"{project_id[:8]}-{project_id[8:12]}-{project_id[12:16]}-{project_id[16:20]}-{project_id[20:]}"
                project_uuid = uuid.UUID(project_id)
            else:
                project_uuid = project_id
            
            # Get all epics for the project
            result = await session.execute(
                select(Epic).where(Epic.project_id == project_uuid).order_by(Epic.order)
            )
            epics = result.scalars().all()
            
            epic_list = []
            for epic in epics:
                # Get stories for this epic
                story_result = await session.execute(
                    select(Story).where(Story.epic_id == epic.id).order_by(Story.order)
                )
                stories = story_result.scalars().all()
                
                story_list = []
                for story in stories:
                    # Get tasks for this story
                    task_result = await session.execute(
                        select(Task).where(Task.story_id == story.id).order_by(Task.order)
                    )
                    tasks = task_result.scalars().all()
                    
                    story_list.append({
                        "id": str(story.id),
                        "name": story.name,
                        "description": story.description,
                        "order": story.order,
                        "tasks": [
                            {
                                "id": str(task.id),
                                "title": task.title,
                                "status": task.status,
                                "assignee_id": task.assignee_id,
                                "progress_percentage": task.progress_percentage or 0
                            }
                            for task in tasks
                        ]
                    })
                
                epic_list.append({
                    "id": str(epic.id),
                    "name": epic.name,
                    "description": epic.description,
                    "order": epic.order,
                    "stories": story_list
                })
            
            return epic_list


project_service = ProjectService()
