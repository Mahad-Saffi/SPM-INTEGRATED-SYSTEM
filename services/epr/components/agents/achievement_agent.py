"""
Achievement Agent - Employee achievement logging and tracking
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from components.managers.data_manager import DataManager
from components.agents.notification_agent import NotificationAgent


class AchievementAgent:
    """Achievement logging and tracking agent"""
    
    def __init__(self, data_manager: DataManager, notification_agent: Optional[NotificationAgent] = None):
        self.data_manager = data_manager
        self.notification_agent = notification_agent
    
    def log_achievement(self, employee_id: str, achievement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Log a new achievement"""
        if not achievement_data.get("title"):
            return {"success": False, "error": "Achievement title is required"}
        
        achievements = self.data_manager.load_data("achievements") or []
        
        achievement = {
            "id": f"ach_{len(achievements) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "employee_id": employee_id,
            "title": achievement_data["title"],
            "description": achievement_data.get("description", ""),
            "category": achievement_data.get("category", "general"),  # task_completion, project_milestone, skill_development, etc.
            "related_task_id": achievement_data.get("related_task_id"),
            "related_project_id": achievement_data.get("related_project_id"),
            "impact": achievement_data.get("impact", "medium"),  # low, medium, high
            "verified": achievement_data.get("verified", False),
            "verified_by": achievement_data.get("verified_by"),
            "verified_at": achievement_data.get("verified_at"),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        achievements.append(achievement)
        self.data_manager.save_data("achievements", achievements)
        
        # Notify manager if high impact
        if achievement.get("impact") == "high" and self.notification_agent:
            employees = self.data_manager.load_data("employees") or []
            employee = next((e for e in employees if e.get("id") == employee_id), None)
            if employee:
                # Find manager (simplified - in real system, use proper manager lookup)
                managers = [e for e in employees if e.get("role") in ["manager", "owner"]]
                for manager in managers:
                    self.notification_agent.send_notification(
                        recipient=manager.get("email"),
                        title=f"High Impact Achievement: {achievement.get('title')}",
                        message=f"{employee.get('name')} logged a high-impact achievement: {achievement.get('description', achievement.get('title'))}",
                        notification_type="achievement",
                        priority="normal"
                    )
        
        return {"success": True, "achievement": achievement}
    
    def log_task_completion(self, employee_id: str, task_id: str, completion_notes: Optional[str] = None) -> Dict[str, Any]:
        """Log task completion as an achievement"""
        tasks = self.data_manager.load_data("tasks") or []
        task = next((t for t in tasks if t.get("id") == task_id), None)
        
        if not task:
            return {"success": False, "error": "Task not found"}
        
        if task.get("assigned_to") != employee_id:
            return {"success": False, "error": "Task not assigned to this employee"}
        
        # Determine impact based on task priority
        impact_map = {"high": "high", "medium": "medium", "low": "low"}
        impact = impact_map.get(task.get("priority", "medium"), "medium")
        
        achievement_data = {
            "title": f"Completed Task: {task.get('title', 'Untitled')}",
            "description": completion_notes or f"Successfully completed task: {task.get('description', '')}",
            "category": "task_completion",
            "related_task_id": task_id,
            "related_project_id": task.get("project_id"),
            "impact": impact
        }
        
        return self.log_achievement(employee_id, achievement_data)
    
    def get_employee_achievements(self, employee_id: str, category: Optional[str] = None,
                                 verified_only: bool = False) -> List[Dict[str, Any]]:
        """Get achievements for an employee"""
        achievements = self.data_manager.load_data("achievements") or []
        
        employee_achievements = [a for a in achievements if a.get("employee_id") == employee_id]
        
        if category:
            employee_achievements = [a for a in employee_achievements if a.get("category") == category]
        
        if verified_only:
            employee_achievements = [a for a in employee_achievements if a.get("verified", False)]
        
        # Sort by created_at descending
        employee_achievements.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return employee_achievements
    
    def verify_achievement(self, achievement_id: str, verifier_id: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """Verify an achievement"""
        achievements = self.data_manager.load_data("achievements") or []
        
        for achievement in achievements:
            if achievement.get("id") == achievement_id:
                achievement["verified"] = True
                achievement["verified_by"] = verifier_id
                achievement["verified_at"] = datetime.now().isoformat()
                if notes:
                    achievement["verification_notes"] = notes
                achievement["updated_at"] = datetime.now().isoformat()
                
                self.data_manager.save_data("achievements", achievements)
                
                # Notify employee
                if self.notification_agent:
                    self.notification_agent.send_notification(
                        recipient=achievement.get("employee_id"),
                        title="Achievement Verified",
                        message=f"Your achievement '{achievement.get('title')}' has been verified by your manager.",
                        notification_type="achievement_verification",
                        priority="normal"
                    )
                
                return {"success": True, "achievement": achievement}
        
        return {"success": False, "error": "Achievement not found"}
    
    def get_achievement_statistics(self, employee_id: str) -> Dict[str, Any]:
        """Get achievement statistics for an employee"""
        achievements = self.get_employee_achievements(employee_id)
        
        total = len(achievements)
        verified = len([a for a in achievements if a.get("verified", False)])
        high_impact = len([a for a in achievements if a.get("impact") == "high"])
        medium_impact = len([a for a in achievements if a.get("impact") == "medium"])
        low_impact = len([a for a in achievements if a.get("impact") == "low"])
        
        # Group by category
        by_category = {}
        for achievement in achievements:
            category = achievement.get("category", "general")
            by_category[category] = by_category.get(category, 0) + 1
        
        # Recent achievements (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent = [a for a in achievements 
                 if datetime.fromisoformat(a.get("created_at", "")) >= thirty_days_ago]
        
        return {
            "total_achievements": total,
            "verified_achievements": verified,
            "verification_rate": (verified / total * 100) if total > 0 else 0,
            "high_impact": high_impact,
            "medium_impact": medium_impact,
            "low_impact": low_impact,
            "by_category": by_category,
            "recent_achievements": len(recent),
            "achievements": achievements[:10]  # Last 10
        }
    
    def update_achievement(self, achievement_id: str, employee_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an achievement (only by owner)"""
        achievements = self.data_manager.load_data("achievements") or []
        
        for achievement in achievements:
            if achievement.get("id") == achievement_id and achievement.get("employee_id") == employee_id:
                # Only allow updating certain fields
                allowed_fields = ["title", "description", "category", "impact"]
                for field in allowed_fields:
                    if field in updates:
                        achievement[field] = updates[field]
                achievement["updated_at"] = datetime.now().isoformat()
                
                self.data_manager.save_data("achievements", achievements)
                return {"success": True, "achievement": achievement}
        
        return {"success": False, "error": "Achievement not found or unauthorized"}
    
    def delete_achievement(self, achievement_id: str, employee_id: str) -> Dict[str, Any]:
        """Delete an achievement (only by owner)"""
        achievements = self.data_manager.load_data("achievements") or []
        original_count = len(achievements)
        
        achievements = [a for a in achievements 
                       if not (a.get("id") == achievement_id and a.get("employee_id") == employee_id)]
        
        if len(achievements) < original_count:
            self.data_manager.save_data("achievements", achievements)
            return {"success": True}
        
        return {"success": False, "error": "Achievement not found or unauthorized"}

