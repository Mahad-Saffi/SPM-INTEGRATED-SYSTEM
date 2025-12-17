"""
Engagement Agent - Calculates employee engagement scores
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from components.managers.data_manager import DataManager


class EngagementAgent:
    """Calculates employee engagement scores based on various factors"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
    
    def calculate_engagement_score(self, employee_id: str) -> Dict[str, Any]:
        """Calculate overall engagement score (0-100)
        
        Factors:
        - Goal completion rate (30%)
        - Feedback response rate (20%)
        - Task on-time completion (30%)
        - Active participation (20%) - based on recent activity
        """
        goals = self.data_manager.load_data("goals") or []
        feedback = self.data_manager.load_data("feedback") or []
        tasks = self.data_manager.load_data("tasks") or []
        
        # Get employee-specific data
        employee_goals = [g for g in goals if g.get("employee_id") == employee_id]
        employee_feedback = [f for f in feedback if f.get("employee_id") == employee_id]
        employee_tasks = [t for t in tasks if t.get("assigned_to") == employee_id]
        
        # 1. Goal completion rate (30%)
        goal_score = 0
        if employee_goals:
            completed_goals = len([g for g in employee_goals 
                                if g.get("current_value", 0) >= g.get("target_value", 0)])
            goal_completion_rate = (completed_goals / len(employee_goals)) * 100
            goal_score = goal_completion_rate * 0.3
        else:
            goal_score = 50 * 0.3  # Default 50% if no goals
        
        # 2. Feedback response rate (20%)
        feedback_score = 0
        if employee_feedback:
            responded_feedback = len([f for f in employee_feedback 
                                     if f.get("employee_response") or f.get("questions")])
            feedback_response_rate = (responded_feedback / len(employee_feedback)) * 100
            feedback_score = feedback_response_rate * 0.2
        else:
            feedback_score = 50 * 0.2  # Default 50% if no feedback
        
        # 3. Task on-time completion (30%)
        task_score = 0
        if employee_tasks:
            completed_tasks = [t for t in employee_tasks if t.get("status") == "completed"]
            if completed_tasks:
                on_time_count = 0
                for task in completed_tasks:
                    if task.get("due_date") and task.get("completed_at"):
                        try:
                            due_date = datetime.fromisoformat(task["due_date"])
                            completed_at = datetime.fromisoformat(task["completed_at"])
                            if completed_at <= due_date:
                                on_time_count += 1
                        except:
                            pass
                
                on_time_rate = (on_time_count / len(completed_tasks)) * 100
                task_score = on_time_rate * 0.3
            else:
                task_score = 50 * 0.3  # Default if no completed tasks
        else:
            task_score = 50 * 0.3  # Default if no tasks
        
        # 4. Active participation (20%) - based on recent activity (last 30 days)
        participation_score = 0
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        recent_goals = [g for g in employee_goals 
                       if datetime.fromisoformat(g.get("created_at", datetime.now().isoformat())) >= thirty_days_ago]
        recent_feedback = [f for f in employee_feedback 
                          if datetime.fromisoformat(f.get("created_at", datetime.now().isoformat())) >= thirty_days_ago]
        recent_tasks = [t for t in employee_tasks 
                       if datetime.fromisoformat(t.get("created_at", datetime.now().isoformat())) >= thirty_days_ago]
        
        # Activity score based on number of recent activities
        activity_count = len(recent_goals) + len(recent_feedback) + len(recent_tasks)
        # Normalize: 10+ activities = 100%, 0 activities = 0%
        activity_rate = min((activity_count / 10) * 100, 100)
        participation_score = activity_rate * 0.2
        
        # Calculate total engagement score
        total_score = goal_score + feedback_score + task_score + participation_score
        
        return {
            "employee_id": employee_id,
            "engagement_score": round(total_score, 2),
            "goal_score": round(goal_score, 2),
            "feedback_score": round(feedback_score, 2),
            "task_score": round(task_score, 2),
            "participation_score": round(participation_score, 2),
            "calculated_at": datetime.now().isoformat()
        }
    
    def get_engagement_level(self, score: float) -> str:
        """Get engagement level based on score"""
        if score >= 80:
            return "High"
        elif score >= 60:
            return "Medium"
        elif score >= 40:
            return "Low"
        else:
            return "Very Low"

