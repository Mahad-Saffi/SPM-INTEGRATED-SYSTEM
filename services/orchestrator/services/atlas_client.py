"""
Atlas AI Scrum Master service client
"""
from .base_client import BaseServiceClient
from config import settings
from typing import Optional, Dict, Any, List


class AtlasClient(BaseServiceClient):
    """Client for Atlas AI Scrum Master service"""
    
    def __init__(self):
        super().__init__(settings.atlas_service_url, "atlas")
    
    async def get_user_projects(self, user_id: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all projects for a user"""
        result = await self.get(f"/api/v1/internal/user/{user_id}/projects", token)
        return result if isinstance(result, list) else []
    
    async def get_projects(self, org_id: str, lab_id: Optional[str] = None, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all projects in an organization"""
        params = {"org_id": org_id}
        if lab_id:
            params["lab_id"] = lab_id
        result = await self.get(f"/api/v1/internal/projects", token, params=params)
        return result if isinstance(result, list) else []
    
    async def get_project(self, project_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        """Get a specific project"""
        return await self.get(f"/api/v1/internal/projects/{project_id}", token)
    
    async def create_project(self, project_data: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        """Create a new project"""
        return await self.post("/api/v1/internal/projects", project_data, token)
    
    async def update_project(self, project_id: str, project_data: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        """Update a project"""
        return await self.put(f"/api/v1/internal/projects/{project_id}", project_data, token)
    
    async def get_project_tasks(self, project_id: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tasks for a project"""
        result = await self.get(f"/api/v1/projects/{project_id}/tasks", token)
        return result if isinstance(result, list) else []
    
    async def get_user_tasks(self, user_id: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all tasks assigned to user"""
        result = await self.get(f"/api/v1/internal/user/{user_id}/tasks", token)
        return result if isinstance(result, list) else []
    
    async def create_task(self, project_id: str, task_data: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        """Create a new task"""
        return await self.post(f"/api/v1/internal/projects/{project_id}/tasks", task_data, token)
    
    async def get_task(self, task_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        """Get a specific task"""
        return await self.get(f"/api/v1/internal/tasks/{task_id}", token)
    
    async def update_task(self, task_id: str, task_data: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        """Update a task"""
        return await self.put(f"/api/v1/internal/tasks/{task_id}", task_data, token)
    
    async def get_issues(self, project_id: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get issues for a project"""
        result = await self.get(f"/api/v1/issues/project/{project_id}", token)
        return result if isinstance(result, list) else []
    
    async def get_organizations(self, user_id: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get organizations for user"""
        result = await self.get(f"/api/v1/internal/user/{user_id}/organizations", token)
        return result if isinstance(result, list) else []


# Global instance
atlas_client = AtlasClient()
