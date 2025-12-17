"""
Atlas API Client - Fetch task, project, and issue data from Atlas
"""
import httpx
from typing import List, Dict, Optional, Any
import os

ATLAS_API_URL = os.getenv("ATLAS_API_URL", "http://localhost:8000")

class AtlasClient:
    """Client to interact with Atlas API"""
    
    def __init__(self, base_url: str = ATLAS_API_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_user_tasks(self, user_id: int, token: str) -> List[Dict[str, Any]]:
        """
        Fetch all tasks assigned to a user from Atlas
        Returns list of tasks with status, project_id, etc.
        """
        headers = {"Authorization": f"Bearer {token}"}
        all_tasks = []
        
        try:
            # Get all projects
            projects_response = await self.client.get(
                f"{self.base_url}/api/v1/projects",
                headers=headers
            )
            projects_response.raise_for_status()
            projects = projects_response.json()
            
            # Get tasks for each project
            for project in projects:
                try:
                    tasks_response = await self.client.get(
                        f"{self.base_url}/api/v1/projects/{project['id']}/tasks",
                        headers=headers
                    )
                    tasks_response.raise_for_status()
                    tasks = tasks_response.json()
                    
                    # Filter tasks assigned to user
                    user_tasks = [
                        t for t in tasks 
                        if t.get('assignee_id') == user_id or t.get('assigned_to') == user_id
                    ]
                    all_tasks.extend(user_tasks)
                except httpx.HTTPError:
                    continue  # Skip projects with errors
            
            return all_tasks
        except httpx.HTTPError as e:
            print(f"Error fetching tasks from Atlas: {e}")
            return []
    
    async def get_project_contributions(self, user_id: int, token: str) -> List[Dict[str, Any]]:
        """Get projects user contributed to"""
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/projects",
                headers=headers
            )
            response.raise_for_status()
            projects = response.json()
            
            # Filter projects where user is a member
            user_projects = [
                p for p in projects 
                if user_id in p.get('member_ids', []) or 
                   user_id == p.get('owner_id') or
                   user_id in [m.get('id') for m in p.get('members', [])]
            ]
            return user_projects
        except httpx.HTTPError as e:
            print(f"Error fetching projects from Atlas: {e}")
            return []
    
    async def get_project_issues(self, project_id: int, token: str) -> List[Dict[str, Any]]:
        """Get issues for a project"""
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/issues/project/{project_id}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error fetching issues from Atlas: {e}")
            return []
    
    async def get_user_info(self, user_id: int, token: str) -> Optional[Dict[str, Any]]:
        """Get user information from Atlas"""
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/users/{user_id}",
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            return None
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


