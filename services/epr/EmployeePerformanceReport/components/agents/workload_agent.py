"""
Workload Agent - Monitors employee workload and stress indicators
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from components.managers.data_manager import DataManager


class WorkloadAgent:
    """Monitors employee workload and determines stress levels"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
    
    def assess_workload(self, employee_id: str) -> Dict[str, Any]:
        """Assess employee workload and return status
        
        Returns:
            {
                "status": "low" | "normal" | "overloaded",
                "task_count": int,
                "overdue_tasks": int,
                "tasks_due_soon": int,
                "average_deadline_pressure": float,
                "recommendations": List[str]
            }
        """
        tasks = self.data_manager.load_data("tasks") or []
        employee_tasks = [t for t in tasks if t.get("assigned_to") == employee_id]
        
        # Filter active tasks (not completed)
        active_tasks = [t for t in employee_tasks if t.get("status") != "completed"]
        task_count = len(active_tasks)
        
        # Count overdue tasks
        now = datetime.now()
        overdue_tasks = 0
        tasks_due_soon = 0  # Due within 3 days
        total_pressure = 0
        
        for task in active_tasks:
            if task.get("due_date"):
                try:
                    due_date = datetime.fromisoformat(task["due_date"])
                    days_until_due = (due_date - now).days
                    
                    if days_until_due < 0:
                        overdue_tasks += 1
                    elif days_until_due <= 3:
                        tasks_due_soon += 1
                    
                    # Calculate pressure (inverse of days until due, normalized)
                    if days_until_due > 0:
                        pressure = 1 / (days_until_due + 1)  # Higher pressure for closer deadlines
                    else:
                        pressure = 1.0  # Maximum pressure for overdue
                    
                    total_pressure += pressure
                except:
                    pass
        
        average_pressure = total_pressure / len(active_tasks) if active_tasks else 0
        
        # Determine workload status
        status = "normal"
        recommendations = []
        
        if task_count > 15 or overdue_tasks > 3 or average_pressure > 0.5:
            status = "overloaded"
            recommendations.append("Consider redistributing some tasks")
            recommendations.append("Prioritize overdue tasks")
            recommendations.append("Request deadline extensions if needed")
        elif task_count < 3:
            status = "low"
            recommendations.append("You have capacity for additional tasks")
        else:
            status = "normal"
            if overdue_tasks > 0:
                recommendations.append(f"Focus on completing {overdue_tasks} overdue task(s)")
            if tasks_due_soon > 0:
                recommendations.append(f"{tasks_due_soon} task(s) due soon - plan accordingly")
        
        return {
            "status": status,
            "task_count": task_count,
            "overdue_tasks": overdue_tasks,
            "tasks_due_soon": tasks_due_soon,
            "average_deadline_pressure": round(average_pressure, 2),
            "recommendations": recommendations
        }
    
    def get_workload_status_emoji(self, status: str) -> str:
        """Get emoji for workload status"""
        emoji_map = {
            "low": "🟢",
            "normal": "🟡",
            "overloaded": "🔴"
        }
        return emoji_map.get(status, "⚪")
    
    def get_all_employee_workloads(self) -> List[Dict[str, Any]]:
        """Get workload assessment for all employees"""
        employees = self.data_manager.load_data("employees") or []
        workloads = []
        
        for employee in employees:
            emp_id = employee.get("id")
            if emp_id:
                workload = self.assess_workload(emp_id)
                workload["employee_id"] = emp_id
                workload["employee_name"] = employee.get("name", "Unknown")
                workloads.append(workload)
        
        return workloads

