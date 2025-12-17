"""
Goal Agent - Goal setting, tracking, and progress management
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from components.managers.data_manager import DataManager
from components.agents.notification_agent import NotificationAgent


class GoalAgent:
    """Goal management agent"""
    
    def __init__(self, data_manager: DataManager, notification_agent: Optional[NotificationAgent] = None):
        self.data_manager = data_manager
        self.notification_agent = notification_agent
    
    def create_goal(self, goal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new goal"""
        if not goal_data.get("employee_id") or not goal_data.get("title"):
            return {"success": False, "error": "Employee ID and title are required"}
        
        # Prepare goal data for API (API uses user_id, not employee_id)
        api_goal_data = {
            "user_id": goal_data["employee_id"],
            "title": goal_data["title"],
            "description": goal_data.get("description", ""),
            "goal_type": goal_data.get("goal_type", "quantitative"),
            "target_value": goal_data.get("target_value", 100),
            "start_date": goal_data.get("start_date", datetime.now().isoformat()),
            "target_date": goal_data.get("deadline") or goal_data.get("target_date", (datetime.now() + timedelta(days=30)).isoformat())
        }
        
        # Use HybridDataManager's create_goal method (uses API if available)
        if hasattr(self.data_manager, 'create_goal'):
            goal = self.data_manager.create_goal(api_goal_data)
            # Add employee_id for compatibility
            if "employee_id" not in goal:
                goal["employee_id"] = goal.get("user_id", goal_data["employee_id"])
        else:
            # Fallback to old method
            goals = self.data_manager.load_data("goals") or []
            goal = {
                "id": str(len(goals) + 1),
                "employee_id": goal_data["employee_id"],
                "title": goal_data["title"],
                "description": goal_data.get("description", ""),
                "target_value": goal_data.get("target_value", 100),
                "current_value": goal_data.get("current_value", 0),
                "unit": goal_data.get("unit", "percentage"),
                "deadline": goal_data.get("deadline"),
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            goals.append(goal)
            self.data_manager.save_data("goals", goals)
        
        # Notify employee
        if self.notification_agent:
            self.notification_agent.send_notification(
                recipient=goal_data["employee_id"],
                title="New Goal Assigned",
                message=f"A new goal has been assigned to you: {goal_data['title']}",
                notification_type="goal_assignment"
            )
        
        return {"success": True, "goal": goal}
    
    def update_goal_progress(self, goal_id: str, current_value: float, notes: Optional[str] = None) -> Dict[str, Any]:
        """Update goal progress"""
        # Prepare update data for API
        update_data = {
            "current_value": current_value,
            "status": None  # Will be calculated
        }
        
        # Use HybridDataManager's update_goal method (uses API if available)
        if hasattr(self.data_manager, 'update_goal'):
            # First get the goal to calculate status
            goals = self.data_manager.load_data("goals") or []
            goal = next((g for g in goals if str(g.get("id")) == str(goal_id)), None)
            if goal:
                goal["current_value"] = current_value
                goal["status"] = self._calculate_goal_status(goal)
                update_data["status"] = goal["status"]
                
                goal = self.data_manager.update_goal(goal_id, update_data)
                if goal:
                    # Add notes if provided
                    if notes:
                        if "notes" not in goal:
                            goal["notes"] = []
                        goal["notes"].append({
                            "note": notes,
                            "timestamp": datetime.now().isoformat()
                        })
                    goal["progress_percentage"] = self.calculate_goal_progress(goal)
                    return {"success": True, "goal": goal}
        else:
            # Fallback to old method
            goals = self.data_manager.load_data("goals") or []
            for goal in goals:
                if str(goal.get("id")) == str(goal_id):
                    goal["current_value"] = current_value
                    goal["updated_at"] = datetime.now().isoformat()
                    
                    if notes:
                        if "notes" not in goal:
                            goal["notes"] = []
                        goal["notes"].append({
                            "note": notes,
                            "timestamp": datetime.now().isoformat()
                        })
                    
                    # Update status
                    goal["status"] = self._calculate_goal_status(goal)
                    goal["progress_percentage"] = self.calculate_goal_progress(goal)
                    
                    self.data_manager.save_data("goals", goals)
                    return {"success": True, "goal": goal}
        
        return {"success": False, "error": "Goal not found"}
    
    def calculate_goal_progress(self, goal: Dict[str, Any]) -> float:
        """Calculate goal progress percentage"""
        target = goal.get("target_value", 100)
        current = goal.get("current_value", 0)
        
        if target == 0:
            return 0.0
        
        progress = (current / target) * 100
        return min(100.0, max(0.0, progress))
    
    def _calculate_goal_status(self, goal: Dict[str, Any]) -> str:
        """Calculate goal status"""
        progress = self.calculate_goal_progress(goal)
        
        if progress >= 100:
            return "completed"
        
        # Check if overdue
        if goal.get("deadline"):
            try:
                deadline = datetime.fromisoformat(goal["deadline"])
                if deadline < datetime.now() and progress < 100:
                    return "overdue"
            except:
                pass
        
        return "active"
    
    def get_employee_goals(self, employee_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get goals for an employee"""
        goals = self.data_manager.load_data("goals") or []
        emp_goals = [g for g in goals if g.get("employee_id") == employee_id]
        
        if status:
            emp_goals = [g for g in emp_goals if g.get("status") == status]
        
        # Calculate progress for each goal
        for goal in emp_goals:
            goal["progress_percentage"] = self.calculate_goal_progress(goal)
        
        return emp_goals
    
    def get_goal(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific goal"""
        goals = self.data_manager.load_data("goals") or []
        for goal in goals:
            if goal.get("id") == goal_id:
                goal["progress_percentage"] = self.calculate_goal_progress(goal)
                return goal
        return None
    
    def delete_goal(self, goal_id: str) -> bool:
        """Delete a goal"""
        goals = self.data_manager.load_data("goals") or []
        goals = [g for g in goals if g.get("id") != goal_id]
        return self.data_manager.save_data("goals", goals)
    
    def get_all_goals(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all goals with optional filters"""
        goals = self.data_manager.load_data("goals") or []
        
        if not filters:
            for goal in goals:
                goal["progress_percentage"] = self.calculate_goal_progress(goal)
            return goals
        
        filtered_goals = goals
        if filters.get("status"):
            filtered_goals = [g for g in filtered_goals if g.get("status") == filters["status"]]
        if filters.get("employee_id"):
            filtered_goals = [g for g in filtered_goals if g.get("employee_id") == filters["employee_id"]]
        
        for goal in filtered_goals:
            goal["progress_percentage"] = self.calculate_goal_progress(goal)
        
        return filtered_goals

