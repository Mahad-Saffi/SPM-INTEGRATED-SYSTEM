"""
Supabase Data Manager
Uses Supabase PostgreSQL database directly
"""
import os
from typing import Dict, Any, Optional, List
from components.managers.supabase_client import SupabaseClient


class HybridDataManager:
    """Data Manager that uses Supabase database"""
    
    def __init__(self, data_dir: str = "data", use_api: Optional[bool] = None):
        # Always use Supabase - no fallback to JSON
        try:
            self.supabase_client = SupabaseClient()
            self.use_supabase = True
        except Exception as e:
            print(f"Failed to initialize Supabase: {e}")
            print("Please set SUPABASE_URL and SUPABASE_ANON_KEY in environment variables")
            raise
        
        # Initialize CRUD methods dynamically
        self._init_crud_methods()
    
    # Mapping of filename to Supabase method name
    _LOAD_MAPPING = {
        "employees": "get_employees",
        "tasks": "get_tasks",
        "projects": "get_projects",
        "performances": "get_performances",
        "goals": "get_goals",
        "feedback": "get_feedback",
        "notifications": "get_notifications"
    }
    
    def load_data(self, filename: str) -> Optional[Any]:
        """Load data from Supabase"""
        if not self.use_supabase:
            return []
        
        try:
            method_name = self._LOAD_MAPPING.get(filename)
            if method_name:
                method = getattr(self.supabase_client, method_name)
                data = method()
                return data if data else []
        except Exception as e:
            print(f"Supabase load failed for {filename}: {e}")
            return []
        
        return []
    
    def save_data(self, filename: str, data: Any) -> bool:
        """Save data to Supabase (for backward compatibility)"""
        # Individual creates/updates are handled by CRUD methods
        # This method is kept for backward compatibility but doesn't do bulk saves
        return True
    
    def _init_crud_methods(self):
        """Initialize CRUD methods for all resources using Supabase"""
        resources = ["task", "employee", "project", "goal", "feedback", "performance", "notification"]
        
        for resource_name in resources:
            # Create method
            def make_create(rname):
                def create(data: Dict[str, Any]) -> Dict[str, Any]:
                    if self.use_supabase:
                        method = getattr(self.supabase_client, f"create_{rname}")
                        return method(data)
                    raise Exception("Supabase not initialized")
                return create
            
            # Update method
            def make_update(rname):
                def update(item_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
                    if self.use_supabase:
                        method = getattr(self.supabase_client, f"update_{rname}")
                        return method(item_id, data)
                    raise Exception("Supabase not initialized")
                return update
            
            # Delete method
            def make_delete(rname):
                def delete(item_id: str) -> bool:
                    if self.use_supabase:
                        method = getattr(self.supabase_client, f"delete_{rname}")
                        return method(item_id)
                    raise Exception("Supabase not initialized")
                return delete
            
            setattr(self, f"create_{resource_name}", make_create(resource_name))
            setattr(self, f"update_{resource_name}", make_update(resource_name))
            setattr(self, f"delete_{resource_name}", make_delete(resource_name))
    
    def get_employee_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get employee by email"""
        if self.use_supabase:
            return self.supabase_client.get_employee_by_email(email)
        return None
    
    def get_employee_by_id(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get employee by ID"""
        if self.use_supabase:
            return self.supabase_client.get_employee(employee_id)
        return None

