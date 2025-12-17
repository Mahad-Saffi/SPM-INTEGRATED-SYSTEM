"""
Badge Agent - Awards badges and rewards to employees
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from components.managers.data_manager import DataManager


class BadgeAgent:
    """Manages employee badges and rewards"""
    
    BADGE_TYPES = {
        "top_performer": {"name": "⭐ Top Performer", "emoji": "⭐", "description": "Consistently high performance"},
        "goal_achiever": {"name": "🎯 Goal Achiever", "emoji": "🎯", "description": "Completed all assigned goals"},
        "team_player": {"name": "🏆 Best Team Player", "emoji": "🏆", "description": "Excellent collaboration"},
        "on_time_master": {"name": "⏰ On-Time Master", "emoji": "⏰", "description": "100% on-time task completion"},
        "feedback_champion": {"name": "💬 Feedback Champion", "emoji": "💬", "description": "Active in feedback discussions"},
        "skill_expert": {"name": "🎓 Skill Expert", "emoji": "🎓", "description": "Mastered multiple skills"},
        "attendance_star": {"name": "📅 Attendance Star", "emoji": "📅", "description": "Perfect attendance record"}
    }
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
    
    def award_badge(self, employee_id: str, badge_type: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """Award a badge to an employee"""
        if badge_type not in self.BADGE_TYPES:
            return {"success": False, "error": f"Invalid badge type: {badge_type}"}
        
        badges_data = self.data_manager.load_data("badges") or []
        
        badge_record = {
            "id": str(len(badges_data) + 1),
            "employee_id": employee_id,
            "badge_type": badge_type,
            "badge_name": self.BADGE_TYPES[badge_type]["name"],
            "badge_emoji": self.BADGE_TYPES[badge_type]["emoji"],
            "reason": reason or self.BADGE_TYPES[badge_type]["description"],
            "awarded_at": datetime.now().isoformat()
        }
        
        badges_data.append(badge_record)
        self.data_manager.save_data("badges", badges_data)
        
        return {"success": True, "badge": badge_record}
    
    def get_employee_badges(self, employee_id: str) -> List[Dict[str, Any]]:
        """Get all badges for an employee"""
        badges_data = self.data_manager.load_data("badges") or []
        return [b for b in badges_data if b.get("employee_id") == employee_id]
    
    def check_and_award_badges(self, employee_id: str) -> List[Dict[str, Any]]:
        """Automatically check and award badges based on performance"""
        from components.agents.performance_agent import EnhancedPerformanceAgent
        from components.agents.goal_agent import GoalAgent
        from components.agents.attendance_agent import AttendanceAgent
        from components.agents.skill_agent import SkillAgent
        
        performance_agent = EnhancedPerformanceAgent(self.data_manager)
        goal_agent = GoalAgent(self.data_manager, None)
        attendance_agent = AttendanceAgent(self.data_manager)
        skill_agent = SkillAgent(self.data_manager)
        
        awarded = []
        existing_badges = [b.get("badge_type") for b in self.get_employee_badges(employee_id)]
        
        # Check Top Performer
        if "top_performer" not in existing_badges:
            performance = performance_agent.evaluate_employee(employee_id, save=False)
            if performance.get("performance_score", 0) >= 85:
                result = self.award_badge(employee_id, "top_performer", 
                                        f"Performance score: {performance.get('performance_score', 0):.1f}")
                if result.get("success"):
                    awarded.append(result["badge"])
        
        # Check Goal Achiever
        if "goal_achiever" not in existing_badges:
            goals = goal_agent.get_employee_goals(employee_id)
            if goals:
                completed = len([g for g in goals 
                                if g.get("current_value", 0) >= g.get("target_value", 0)])
                if completed == len(goals) and len(goals) >= 3:
                    result = self.award_badge(employee_id, "goal_achiever", 
                                            f"Completed all {len(goals)} goals")
                    if result.get("success"):
                        awarded.append(result["badge"])
        
        # Check On-Time Master
        if "on_time_master" not in existing_badges:
            performance = performance_agent.evaluate_employee(employee_id, save=False)
            if performance.get("on_time_rate", 0) >= 100:
                result = self.award_badge(employee_id, "on_time_master", 
                                        "100% on-time task completion")
                if result.get("success"):
                    awarded.append(result["badge"])
        
        # Check Attendance Star
        if "attendance_star" not in existing_badges:
            attendance_percentage = attendance_agent.calculate_attendance_percentage(employee_id, days=30)
            if attendance_percentage >= 100:
                result = self.award_badge(employee_id, "attendance_star", 
                                        "Perfect attendance for 30 days")
                if result.get("success"):
                    awarded.append(result["badge"])
        
        # Check Skill Expert
        if "skill_expert" not in existing_badges:
            skills = skill_agent.get_employee_skills(employee_id)
            high_level_skills = [s for s, level in skills.items() if level >= 4]
            if len(high_level_skills) >= 5:
                result = self.award_badge(employee_id, "skill_expert", 
                                        f"Mastered {len(high_level_skills)} skills")
                if result.get("success"):
                    awarded.append(result["badge"])
        
        return awarded

