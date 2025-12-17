"""
Task Agent - Autonomous task creation, validation, assignment, and notification
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from components.managers.data_manager import DataManager

if TYPE_CHECKING:
    from components.agents.notification_agent import NotificationAgent


class TaskAgent:
    """Autonomous task management agent"""
    
    def __init__(self, data_manager: DataManager, notification_agent: Optional['NotificationAgent'] = None):
        self.data_manager = data_manager
        self.notification_agent = notification_agent
    
    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create and assign a task"""
        # Validate inputs
        validation_result = self.validate_task_inputs(task_data)
        if not validation_result["valid"]:
            return {"success": False, "error": validation_result["error"]}
        
        # Prepare task data for API
        api_task_data = {
            "title": task_data["title"],
            "description": task_data.get("description", ""),
            "project_id": int(task_data.get("project_id")) if task_data.get("project_id") else None,
            "assigned_to": task_data.get("assigned_to"),
            "priority": task_data.get("priority", "medium"),
            "status": task_data.get("status", "pending"),
            "due_date": task_data.get("due_date"),
            "created_by": task_data.get("created_by", "system")
        }
        
        # Use HybridDataManager's create_task method (uses API if available)
        if hasattr(self.data_manager, 'create_task'):
            task = self.data_manager.create_task(api_task_data)
        else:
            # Fallback to old method
            tasks = self.data_manager.load_data("tasks") or []
            task = {
                "id": str(len(tasks) + 1),
                **api_task_data,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            tasks.append(task)
            self.data_manager.save_data("tasks", tasks)
        
        # Notify assignee if notification agent is available
        if self.notification_agent and task.get("assigned_to"):
            self._notify_assignee(task)
        
        return {"success": True, "task": task}
    
    def validate_task_inputs(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate task input data"""
        if not task_data.get("title"):
            return {"valid": False, "error": "Task title is required"}
        
        if task_data.get("due_date"):
            try:
                due_date = datetime.fromisoformat(task_data["due_date"])
                if due_date < datetime.now():
                    return {"valid": False, "error": "Due date cannot be in the past"}
            except:
                return {"valid": False, "error": "Invalid due date format"}
        
        return {"valid": True}
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing task"""
        # Prepare update data
        update_data = updates.copy()
        if "due_date" in update_data and isinstance(update_data["due_date"], str):
            # Keep as is if already string
            pass
        elif "project_id" in update_data and update_data["project_id"]:
            update_data["project_id"] = int(update_data["project_id"])
        
        # Use HybridDataManager's update_task method (uses API if available)
        if hasattr(self.data_manager, 'update_task'):
            task = self.data_manager.update_task(task_id, update_data)
            if task:
                return {"success": True, "task": task}
        else:
            # Fallback to old method
            tasks = self.data_manager.load_data("tasks") or []
            for task in tasks:
                if str(task.get("id")) == str(task_id):
                    task.update(updates)
                    task["updated_at"] = datetime.now().isoformat()
                    self.data_manager.save_data("tasks", tasks)
                    return {"success": True, "task": task}
        
        return {"success": False, "error": "Task not found"}
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific task"""
        # Use API if available
        if hasattr(self.data_manager, 'api_client') and self.data_manager.api_client:
            try:
                return self.data_manager.api_client.get_task(task_id)
            except:
                pass
        
        # Fallback to load_data
        tasks = self.data_manager.load_data("tasks") or []
        for task in tasks:
            if str(task.get("id")) == str(task_id):
                return task
        return None
    
    def get_tasks(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get tasks with optional filters"""
        tasks = self.data_manager.load_data("tasks") or []
        
        if not filters:
            return tasks
        
        filtered_tasks = tasks
        if filters.get("project_id"):
            filtered_tasks = [t for t in filtered_tasks if t.get("project_id") == filters["project_id"]]
        if filters.get("assigned_to"):
            filtered_tasks = [t for t in filtered_tasks if t.get("assigned_to") == filters["assigned_to"]]
        if filters.get("status"):
            filtered_tasks = [t for t in filtered_tasks if t.get("status") == filters["status"]]
        if filters.get("priority"):
            filtered_tasks = [t for t in filtered_tasks if t.get("priority") == filters["priority"]]
        
        return filtered_tasks
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        # Use HybridDataManager's delete_task method (uses API if available)
        if hasattr(self.data_manager, 'delete_task'):
            return self.data_manager.delete_task(task_id)
        else:
            # Fallback to old method
            tasks = self.data_manager.load_data("tasks") or []
            tasks = [t for t in tasks if str(t.get("id")) != str(task_id)]
            return self.data_manager.save_data("tasks", tasks)
    
    def _notify_assignee(self, task: Dict[str, Any]):
        """Notify task assignee"""
        if self.notification_agent:
            self.notification_agent.send_notification(
                recipient=task["assigned_to"],
                title="New Task Assigned",
                message=f"You have been assigned a new task: {task['title']}",
                notification_type="task_assignment"
            )

