"""
API-backed Data Manager
Uses FastAPI backend instead of JSON files
Implements the same interface as DataManager for drop-in replacement
"""
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from components.managers.api_client import SyncAPIClient


class APIDataManager:
    """Data Manager that uses API backend instead of JSON files"""
    
    def __init__(self, api_base_url: Optional[str] = None, api_token: Optional[str] = None):
        self.api_client = SyncAPIClient(api_base_url, api_token)
        self._cache = {}  # Simple in-memory cache
    
    def load_data(self, filename: str) -> Optional[Any]:
        """Load data from API (mimics DataManager interface)"""
        try:
            # Map filename to API endpoint
            if filename == "employees":
                return self.api_client.get_employees()
            elif filename == "tasks":
                return self.api_client.get_tasks()
            elif filename == "projects":
                return self.api_client.get_projects()
            elif filename == "performances":
                return self.api_client.get_performances()
            elif filename == "goals":
                return self.api_client.get_goals()
            elif filename == "feedback":
                return self.api_client.get_feedback()
            elif filename == "notifications":
                return self.api_client.get_notifications()
            else:
                # For other data types not yet in API, return empty list
                return []
        except Exception as e:
            print(f"Error loading {filename} from API: {e}")
            return []
    
    def save_data(self, filename: str, data: Any) -> bool:
        """Save data to API (mimics DataManager interface)"""
        try:
            if not isinstance(data, list):
                print(f"Warning: save_data for {filename} expects a list, got {type(data)}")
                return False
            
            # For now, we'll handle creates/updates individually
            # This is a simplified version - in production, you'd want to track changes
            if filename == "employees":
                # For employees, we'd need to check if each exists and update/create
                # This is a simplified implementation
                return True
            elif filename == "tasks":
                return True
            elif filename == "projects":
                return True
            elif filename == "performances":
                # Save each performance evaluation
                for perf in data:
                    if isinstance(perf, dict) and "employee_id" in perf:
                        try:
                            self.api_client.create_performance(perf)
                        except:
                            pass  # Skip if already exists
                return True
            elif filename == "goals":
                for goal in data:
                    if isinstance(goal, dict) and "title" in goal:
                        try:
                            self.api_client.create_goal(goal)
                        except:
                            pass
                return True
            elif filename == "feedback":
                for feedback in data:
                    if isinstance(feedback, dict) and "employee_id" in feedback:
                        try:
                            self.api_client.create_feedback(feedback)
                        except:
                            pass
                return True
            elif filename == "notifications":
                for notif in data:
                    if isinstance(notif, dict) and "user_id" in notif:
                        try:
                            self.api_client.create_notification(notif)
                        except:
                            pass
                return True
            else:
                return True
        except Exception as e:
            print(f"Error saving {filename} to API: {e}")
            return False
    
    def get_employee_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get employee by email"""
        employees = self.load_data("employees")
        if employees:
            for emp in employees:
                if isinstance(emp, dict) and emp.get("email") == email:
                    return emp
        return None
    
    def get_employee_by_id(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get employee by ID"""
        employees = self.load_data("employees")
        if employees:
            for emp in employees:
                if isinstance(emp, dict) and str(emp.get("id")) == str(employee_id):
                    return emp
        return None

