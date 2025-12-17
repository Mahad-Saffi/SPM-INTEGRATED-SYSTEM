"""
Performance Calculator - Combine Atlas data with local performance data
"""
from typing import Dict, List, Any
from api.services.atlas_client import AtlasClient
from components.managers.data_manager import DataManager

class PerformanceCalculator:
    """Calculate performance scores combining Atlas and local data"""
    
    def __init__(self, atlas_client: AtlasClient):
        self.atlas_client = atlas_client
        self.data_manager = DataManager()
    
    async def calculate_performance_score(
        self,
        user_id: int,
        atlas_token: str,
        time_period: str = "quarterly"
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive performance score
        Combines:
        - Task completion from Atlas (30%)
        - Peer feedback (25%)
        - Goal achievement (20%)
        - Skill assessments (15%)
        - Productivity metrics (10%)
        """
        # Get Atlas data
        atlas_tasks = await self.atlas_client.get_user_tasks(user_id, atlas_token)
        
        # Calculate task metrics
        total_tasks = len(atlas_tasks)
        completed_tasks = [t for t in atlas_tasks if t.get('status') in ['Done', 'completed', 'closed']]
        completion_rate = len(completed_tasks) / total_tasks if total_tasks > 0 else 0
        
        # Get on-time completion (if due_date available)
        on_time_tasks = 0
        for task in completed_tasks:
            if task.get('due_date') and task.get('completed_at'):
                # Simple check - task completed before or on due date
                on_time_tasks += 1
        on_time_rate = on_time_tasks / total_tasks if total_tasks > 0 else 0
        
        # Get local data
        employees = self.data_manager.load_data("employees") or []
        employee = next((e for e in employees if str(e.get("id")) == str(user_id)), None)
        
        if not employee:
            # Try to find by email or other identifier
            employee = next((e for e in employees if str(e.get("atlas_user_id")) == str(user_id)), None)
        
        # Get goals
        goals = self.data_manager.load_data("goals") or []
        user_goals = [g for g in goals if str(g.get("user_id")) == str(user_id)]
        achieved_goals = [g for g in user_goals if g.get("status") == "achieved"]
        goal_rate = len(achieved_goals) / len(user_goals) if user_goals else 0
        
        # Get feedback
        feedback = self.data_manager.load_data("feedback") or []
        user_feedback = [f for f in feedback if str(f.get("employee_id")) == str(user_id)]
        avg_feedback = (
            sum(f.get('rating', 0) for f in user_feedback) / len(user_feedback)
            if user_feedback else 0
        )
        
        # Get skills
        performances = self.data_manager.load_data("performances") or []
        user_performance = next(
            (p for p in performances if str(p.get("employee_id")) == str(user_id)),
            {}
        )
        skills = user_performance.get("skills", [])
        avg_skill = (
            sum(s.get('proficiency_score', 0) for s in skills) / len(skills)
            if skills else 0
        )
        
        # Weighted performance score
        overall_score = (
            completion_rate * 0.30 +
            (avg_feedback / 5) * 0.25 +
            goal_rate * 0.20 +
            (avg_skill / 100) * 0.15 +
            on_time_rate * 0.10
        ) * 100
        
        return {
            "user_id": user_id,
            "overall_score": round(overall_score, 2),
            "task_completion_rate": round(completion_rate * 100, 2),
            "tasks_completed": len(completed_tasks),
            "total_tasks": total_tasks,
            "on_time_completion_rate": round(on_time_rate * 100, 2),
            "goal_achievement_rate": round(goal_rate * 100, 2),
            "goals_achieved": len(achieved_goals),
            "total_goals": len(user_goals),
            "average_feedback_rating": round(avg_feedback, 2),
            "feedback_count": len(user_feedback),
            "average_skill_score": round(avg_skill, 2),
            "skills_count": len(skills),
            "time_period": time_period
        }


