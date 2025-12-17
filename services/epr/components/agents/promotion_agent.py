"""
Promotion Agent - Suggests employees ready for promotion
"""
from typing import Dict, Any, Optional, List
from components.managers.data_manager import DataManager


class PromotionAgent:
    """Determines if employees are ready for promotion based on criteria"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
    
    def check_promotion_eligibility(self, employee_id: str) -> Dict[str, Any]:
        """Check if employee is eligible for promotion
        
        Criteria:
        - Performance > 80
        - Attendance > 90%
        - Goals completed > 70%
        """
        from components.agents.performance_agent import EnhancedPerformanceAgent
        from components.agents.attendance_agent import AttendanceAgent
        from components.agents.goal_agent import GoalAgent
        
        performance_agent = EnhancedPerformanceAgent(self.data_manager)
        attendance_agent = AttendanceAgent(self.data_manager)
        goal_agent = GoalAgent(self.data_manager, None)
        
        # Get performance score
        performance = performance_agent.evaluate_employee(employee_id, save=False)
        performance_score = performance.get("performance_score", 0)
        
        # Get attendance percentage
        attendance_percentage = attendance_agent.calculate_attendance_percentage(employee_id, days=30)
        
        # Get goal completion rate
        goals = goal_agent.get_employee_goals(employee_id)
        goal_completion_rate = 0
        if goals:
            completed_goals = len([g for g in goals 
                                  if g.get("current_value", 0) >= g.get("target_value", 0)])
            goal_completion_rate = (completed_goals / len(goals)) * 100
        
        # Check criteria
        meets_performance = performance_score > 80
        meets_attendance = attendance_percentage > 90
        meets_goals = goal_completion_rate > 70
        
        is_eligible = meets_performance and meets_attendance and meets_goals
        
        return {
            "employee_id": employee_id,
            "is_eligible": is_eligible,
            "performance_score": round(performance_score, 2),
            "attendance_percentage": round(attendance_percentage, 2),
            "goal_completion_rate": round(goal_completion_rate, 2),
            "meets_performance": meets_performance,
            "meets_attendance": meets_attendance,
            "meets_goals": meets_goals,
            "recommendation": "Ready for Promotion" if is_eligible else "Not Ready Yet"
        }
    
    def get_all_eligible_employees(self) -> List[Dict[str, Any]]:
        """Get all employees eligible for promotion"""
        employees = self.data_manager.load_data("employees") or []
        eligible = []
        
        for employee in employees:
            emp_id = employee.get("id")
            if emp_id:
                eligibility = self.check_promotion_eligibility(emp_id)
                if eligibility.get("is_eligible"):
                    eligibility["employee_name"] = employee.get("name", "Unknown")
                    eligibility["employee_email"] = employee.get("email", "")
                    eligible.append(eligibility)
        
        return eligible

