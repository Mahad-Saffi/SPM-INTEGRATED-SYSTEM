"""
Dashboard aggregator - combines data from all services
"""
import asyncio
from typing import Dict, Any

from services.atlas_client import atlas_client
from services.workpulse_client import workpulse_client
from services.epr_client import epr_client
from services.labs_client import labs_client


class DashboardAggregator:
    """Aggregate dashboard data from all services"""
    
    async def get_unified_dashboard(self, user_id: str, token: str) -> Dict[str, Any]:
        """
        Get unified dashboard combining data from all services
        
        Returns:
        - Projects and tasks from Atlas
        - Activity metrics from WorkPulse
        - Performance scores from EPR
        - Labs and collaborations from Labs
        """
        
        # Fetch from all services in parallel
        projects_task = atlas_client.get_user_projects(user_id, token)
        tasks_task = atlas_client.get_user_tasks(user_id, token)
        activity_task = workpulse_client.get_today_activity(user_id, token)
        performance_task = epr_client.get_performance_score(user_id, token)
        goals_task = epr_client.get_user_goals(user_id, token)
        labs_task = labs_client.get_labs(token)
        
        # Run all in parallel
        (projects, tasks, activity, performance, goals, labs) = await asyncio.gather(
            projects_task,
            tasks_task,
            activity_task,
            performance_task,
            goals_task,
            labs_task,
            return_exceptions=True
        )
        
        # Count tasks by status
        completed_tasks = len([t for t in (tasks if isinstance(tasks, list) else []) if t.get('status') == 'Done'])
        pending_tasks = len([t for t in (tasks if isinstance(tasks, list) else []) if t.get('status') != 'Done'])
        
        # Build dashboard
        dashboard = {
            "user_id": user_id,
            "projects": {
                "total": len(projects) if isinstance(projects, list) else 0,
                "active": len([p for p in (projects if isinstance(projects, list) else []) if p.get('status') == 'active']),
                "data": projects[:5] if isinstance(projects, list) else []
            },
            "tasks": {
                "total": len(tasks) if isinstance(tasks, list) else 0,
                "completed": completed_tasks,
                "pending": pending_tasks,
                "data": tasks[:5] if isinstance(tasks, list) else []
            },
            "activity": {
                "productive_hours_today": activity.get('productive_hours', 0) if isinstance(activity, dict) else 0,
                "idle_hours_today": activity.get('idle_hours', 0) if isinstance(activity, dict) else 0,
                "productivity_score": activity.get('productivity_score', 0) if isinstance(activity, dict) else 0,
                "is_online": activity.get('is_online', False) if isinstance(activity, dict) else False
            },
            "performance": {
                "overall_score": performance.get('overall_score', 0) if isinstance(performance, dict) else 0,
                "task_completion_rate": performance.get('task_completion_rate', 0) if isinstance(performance, dict) else 0,
                "goal_achievement_rate": performance.get('goal_achievement_rate', 0) if isinstance(performance, dict) else 0,
                "trend": performance.get('trend', 'stable') if isinstance(performance, dict) else 'stable'
            },
            "goals": {
                "total": len(goals) if isinstance(goals, list) else 0,
                "in_progress": len([g for g in (goals if isinstance(goals, list) else []) if g.get('status') == 'in_progress']),
                "achieved": len([g for g in (goals if isinstance(goals, list) else []) if g.get('status') == 'achieved']),
                "data": goals[:3] if isinstance(goals, list) else []
            },
            "labs": {
                "total": len(labs) if isinstance(labs, list) else 0,
                "data": labs[:5] if isinstance(labs, list) else []
            }
        }
        
        return dashboard


# Global instance
dashboard_aggregator = DashboardAggregator()
