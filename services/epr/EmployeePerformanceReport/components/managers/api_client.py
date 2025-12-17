"""
API Client for FastAPI Backend
Handles all HTTP requests to the Performance API
"""
import os
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
import json


class SyncAPIClient:
    """Synchronous client for making requests to the FastAPI backend"""
    
    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None):
        self.base_url = base_url or os.getenv("API_BASE_URL", "http://localhost:8003")
        self.token = token or os.getenv("API_TOKEN", "local")
        self.client = httpx.Client(timeout=30.0)
        self._use_api = os.getenv("USE_API", "false").lower() == "true"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def _request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to API"""
        if not self._use_api:
            return []
        
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        try:
            if method == "GET":
                response = self.client.get(url, headers=headers, params=params)
            elif method == "POST":
                response = self.client.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = self.client.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = self.client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return []
            print(f"API request failed: {e.response.status_code} - {e.response.text}")
            return []
        except Exception as e:
            print(f"API request error: {str(e)}")
            return []
    
    # Resource endpoints - dynamically generated
    _RESOURCES = {
        "employees": "/api/v1/employees",
        "tasks": "/api/v1/tasks",
        "projects": "/api/v1/projects",
        "performances": "/api/v1/performances",
        "goals": "/api/v1/goals",
        "feedback": "/api/v1/feedback",
        "notifications": "/api/v1/notifications",
        "reviews": "/api/v1/reviews",
        "skills": "/api/v1/skills"
    }
    
    def __getattr__(self, name: str):
        """Dynamically generate CRUD methods for resources"""
        # Parse method name: get_employees, create_task, update_project, etc.
        parts = name.split("_", 1)
        if len(parts) != 2:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        
        action, resource = parts[0], parts[1]
        
        # Handle plural resources (employees, tasks, etc.)
        resource_singular = resource.rstrip("s") if resource.endswith("s") else resource
        endpoint = self._RESOURCES.get(resource) or self._RESOURCES.get(resource_singular + "s")
        
        if not endpoint:
            raise AttributeError(f"Unknown resource: {resource}")
        
        # Generate method based on action
        if action == "get" and resource.endswith("s"):
            # GET all: get_employees(), get_tasks()
            def get_all(filter_param: Optional[str] = None, filter_value: Optional[str] = None):
                params = {filter_param: filter_value} if filter_param and filter_value else None
                return self._request("GET", endpoint, params=params)
            return get_all
        
        elif action == "get":
            # GET one: get_employee(id), get_task(id)
            def get_one(item_id: str):
                return self._request("GET", f"{endpoint}/{item_id}")
            return get_one
        
        elif action == "create":
            # POST: create_employee(data), create_task(data)
            def create(data: Dict[str, Any]):
                return self._request("POST", endpoint, data=data)
            return create
        
        elif action == "update":
            # PUT: update_employee(id, data), update_task(id, data)
            def update(item_id: str, data: Dict[str, Any]):
                return self._request("PUT", f"{endpoint}/{item_id}", data=data)
            return update
        
        elif action == "delete":
            # DELETE: delete_employee(id), delete_task(id)
            def delete(item_id: str):
                self._request("DELETE", f"{endpoint}/{item_id}")
                return True
            return delete
        
        raise AttributeError(f"Unknown action: {action}")
    
    # Special cases that don't follow standard pattern
    def get_goals(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get goals, optionally filtered by user"""
        if user_id:
            return self._request("GET", f"/api/v1/goals/user/{user_id}")
        return self._request("GET", "/api/v1/goals")
    
    def update_goal(self, goal_id: str, goal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update goal (special endpoint)"""
        return self._request("PUT", f"/api/v1/goals/{goal_id}/progress", data=goal_data)
    
    def get_feedback(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get feedback, optionally filtered by user"""
        if user_id:
            return self._request("GET", f"/api/v1/feedback/user/{user_id}")
        return self._request("GET", "/api/v1/feedback")
    
    def get_reviews(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get reviews, optionally filtered by user"""
        if user_id:
            return self._request("GET", f"/api/v1/reviews/user/{user_id}")
        return self._request("GET", "/api/v1/reviews")
    
    def get_skills(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get skills, optionally filtered by user"""
        if user_id:
            return self._request("GET", f"/api/v1/skills/user/{user_id}")
        return self._request("GET", "/api/v1/skills")
    
    def assess_skill(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create skill assessment"""
        return self._request("POST", "/api/v1/skills/assess", data=skill_data)
    
    def mark_notification_read(self, notification_id: str) -> Dict[str, Any]:
        """Mark notification as read"""
        return self._request("PUT", f"/api/v1/notifications/{notification_id}/read")
    
    def close(self):
        """Close the HTTP client"""
        self.client.close()

