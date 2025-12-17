"""
Supabase Client for Database Operations
Replaces local JSON files and API calls with direct Supabase access
"""
import os
from typing import Dict, Any, Optional, List
from supabase import create_client, Client
from datetime import datetime
import json

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system environment variables


class SupabaseClient:
    """Client for Supabase database operations"""
    
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables.\n"
                "Create a .env file with:\n"
                "SUPABASE_URL=https://your-project.supabase.co\n"
                "SUPABASE_ANON_KEY=your-anon-key"
            )
        
        self.client: Client = create_client(supabase_url, supabase_key)
    
    # Employees
    def get_employees(self) -> List[Dict[str, Any]]:
        """Get all employees"""
        response = self.client.table("employees").select("*").execute()
        return [self._format_item(item) for item in response.data]
    
    def get_employee(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get employee by ID"""
        response = self.client.table("employees").select("*").eq("id", employee_id).execute()
        return self._format_item(response.data[0]) if response.data else None
    
    def get_employee_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get employee by email"""
        response = self.client.table("employees").select("*").eq("email", email).execute()
        return self._format_item(response.data[0]) if response.data else None
    
    def create_employee(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create employee"""
        # Handle skills as JSONB
        employee_data = data.copy()
        if "skills" in employee_data and isinstance(employee_data["skills"], dict):
            employee_data["skills"] = json.dumps(employee_data["skills"])
        response = self.client.table("employees").insert(employee_data).execute()
        return self._format_item(response.data[0])
    
    def update_employee(self, employee_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update employee"""
        employee_data = data.copy()
        if "skills" in employee_data and isinstance(employee_data["skills"], dict):
            employee_data["skills"] = json.dumps(employee_data["skills"])
        response = self.client.table("employees").update(employee_data).eq("id", employee_id).execute()
        return self._format_item(response.data[0]) if response.data else {}
    
    def delete_employee(self, employee_id: str) -> bool:
        """Delete employee"""
        self.client.table("employees").delete().eq("id", employee_id).execute()
        return True
    
    # Tasks
    def get_tasks(self, employee_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all tasks, optionally filtered by employee"""
        query = self.client.table("tasks").select("*")
        if employee_id:
            query = query.eq("assigned_to", employee_id)
        response = query.execute()
        return [self._format_item(item) for item in response.data]
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        response = self.client.table("tasks").select("*").eq("id", task_id).execute()
        return self._format_item(response.data[0]) if response.data else None
    
    def create_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create task"""
        # Convert string IDs to UUIDs if needed
        task_data = self._prepare_data(data, ["assigned_to", "project_id"])
        response = self.client.table("tasks").insert(task_data).execute()
        return self._format_item(response.data[0])
    
    def update_task(self, task_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update task"""
        task_data = self._prepare_data(data, ["assigned_to", "project_id"])
        response = self.client.table("tasks").update(task_data).eq("id", task_id).execute()
        return self._format_item(response.data[0]) if response.data else {}
    
    def delete_task(self, task_id: str) -> bool:
        """Delete task"""
        self.client.table("tasks").delete().eq("id", task_id).execute()
        return True
    
    # Projects
    def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects"""
        response = self.client.table("projects").select("*").execute()
        return [self._format_item(item) for item in response.data]
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID"""
        response = self.client.table("projects").select("*").eq("id", project_id).execute()
        return self._format_item(response.data[0]) if response.data else None
    
    def create_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create project"""
        response = self.client.table("projects").insert(data).execute()
        return self._format_item(response.data[0])
    
    def update_project(self, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update project"""
        response = self.client.table("projects").update(data).eq("id", project_id).execute()
        return self._format_item(response.data[0]) if response.data else {}
    
    def delete_project(self, project_id: str) -> bool:
        """Delete project"""
        self.client.table("projects").delete().eq("id", project_id).execute()
        return True
    
    # Performances
    def get_performances(self, employee_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get performances, optionally filtered by employee"""
        query = self.client.table("performances").select("*").order("evaluation_date", desc=True)
        if employee_id:
            query = query.eq("employee_id", employee_id)
        response = query.execute()
        return [self._format_item(item) for item in response.data]
    
    def create_performance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create performance evaluation"""
        response = self.client.table("performances").insert(data).execute()
        return self._format_item(response.data[0])
    
    # Goals
    def get_goals(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get goals, optionally filtered by user"""
        query = self.client.table("performance_goals").select("*")
        if user_id:
            query = query.eq("user_id", user_id)
        response = query.execute()
        return [self._format_item(item) for item in response.data]
    
    def create_goal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create goal"""
        # Convert user_id to UUID format if needed
        goal_data = self._prepare_data(data, ["user_id"])
        response = self.client.table("performance_goals").insert(goal_data).execute()
        return self._format_item(response.data[0])
    
    def update_goal(self, goal_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update goal"""
        response = self.client.table("performance_goals").update(data).eq("id", goal_id).execute()
        return self._format_item(response.data[0]) if response.data else {}
    
    # Feedback
    def get_feedback(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get feedback, optionally filtered by user"""
        query = self.client.table("peer_feedback").select("*")
        if user_id:
            query = query.eq("employee_id", user_id)
        response = query.execute()
        return [self._format_item(item) for item in response.data]
    
    def create_feedback(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create feedback"""
        # Convert IDs to UUID format
        feedback_data = self._prepare_data(data, ["employee_id", "reviewer_id", "project_id"])
        response = self.client.table("peer_feedback").insert(feedback_data).execute()
        return self._format_item(response.data[0])
    
    # Notifications
    def get_notifications(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get notifications, optionally filtered by user"""
        query = self.client.table("notifications").select("*").order("created_at", desc=True)
        if user_id:
            query = query.eq("user_id", user_id)
        response = query.execute()
        return [self._format_item(item) for item in response.data]
    
    def create_notification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create notification"""
        response = self.client.table("notifications").insert(data).execute()
        return self._format_item(response.data[0])
    
    def mark_notification_read(self, notification_id: str) -> Dict[str, Any]:
        """Mark notification as read"""
        response = self.client.table("notifications").update({"is_read": True}).eq("id", notification_id).execute()
        return self._format_item(response.data[0]) if response.data else {}
    
    # Reviews
    def get_reviews(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get reviews, optionally filtered by user"""
        query = self.client.table("performance_reviews").select("*")
        if user_id:
            query = query.eq("employee_id", user_id)
        response = query.execute()
        return [self._format_item(item) for item in response.data]
    
    def create_review(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create review"""
        response = self.client.table("performance_reviews").insert(data).execute()
        return self._format_item(response.data[0])
    
    # Skills
    def get_skills(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get skills, optionally filtered by user"""
        query = self.client.table("skill_assessments").select("*")
        if user_id:
            query = query.eq("user_id", user_id)
        response = query.execute()
        return [self._format_item(item) for item in response.data]
    
    def assess_skill(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create skill assessment"""
        response = self.client.table("skill_assessments").insert(data).execute()
        return self._format_item(response.data[0])
    
    def _prepare_data(self, data: Dict[str, Any], uuid_fields: List[str]) -> Dict[str, Any]:
        """Prepare data for Supabase insertion (handle UUIDs)"""
        prepared = {}
        for key, value in data.items():
            if key in uuid_fields and value:
                # Keep UUID as string (Supabase handles it)
                prepared[key] = value
            elif value is not None:
                prepared[key] = value
        return prepared
    
    def _format_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Format database item to match expected format"""
        from datetime import datetime
        formatted = {}
        for key, value in item.items():
            # Convert UUID to string (keep as is)
            if isinstance(value, str):
                formatted[key] = value
            # Convert datetime to ISO string
            elif isinstance(value, datetime):
                formatted[key] = value.isoformat()
            # Keep JSONB as dict
            elif isinstance(value, dict):
                formatted[key] = value
            # Convert Decimal to float
            elif hasattr(value, '__float__'):
                formatted[key] = float(value)
            else:
                formatted[key] = value
        return formatted

