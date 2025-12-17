"""
Predictive Analytics Agent - Capacity and risk forecasting
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from components.managers.data_manager import DataManager
from components.agents.performance_agent import EnhancedPerformanceAgent
from components.agents.reporting_agent import ReportingAgent


class PredictiveAnalyticsAgent:
    """Predictive analytics for capacity and risk forecasting"""
    
    def __init__(self, data_manager: DataManager, performance_agent: EnhancedPerformanceAgent,
                 reporting_agent: ReportingAgent):
        self.data_manager = data_manager
        self.performance_agent = performance_agent
        self.reporting_agent = reporting_agent
    
    def forecast_capacity(self, employee_id: Optional[str] = None, weeks: int = 4) -> Dict[str, Any]:
        """Forecast employee or team capacity"""
        tasks = self.data_manager.load_data("tasks") or []
        employees = self.data_manager.load_data("employees") or []
        performance_data = self.data_manager.load_data("performances") or []
        
        if employee_id:
            # Forecast for specific employee
            employee_tasks = [t for t in tasks if t.get("assigned_to") == employee_id]
            emp_perf = [p for p in performance_data if p.get("employee_id") == employee_id]
            
            # Calculate average tasks per week
            completed_tasks = [t for t in employee_tasks if t.get("status") == "completed"]
            if completed_tasks:
                # Estimate based on historical completion rate
                avg_completion_time = self._calculate_avg_completion_time(completed_tasks)
                tasks_per_week = 5 / avg_completion_time if avg_completion_time > 0 else 2
            else:
                tasks_per_week = 2  # Default
            
            # Get current workload
            active_tasks = [t for t in employee_tasks if t.get("status") in ["pending", "in_progress"]]
            current_workload = len(active_tasks)
            
            # Forecast
            forecasted_capacity = tasks_per_week * weeks
            available_capacity = max(0, forecasted_capacity - current_workload)
            
            return {
                "employee_id": employee_id,
                "forecast_period_weeks": weeks,
                "current_workload": current_workload,
                "tasks_per_week": round(tasks_per_week, 2),
                "forecasted_capacity": round(forecasted_capacity, 2),
                "available_capacity": round(available_capacity, 2),
                "utilization_rate": round((current_workload / forecasted_capacity * 100) if forecasted_capacity > 0 else 0, 2),
                "recommendation": self._get_capacity_recommendation(current_workload, forecasted_capacity)
            }
        else:
            # Forecast for entire team
            team_capacity = []
            for employee in employees:
                if employee.get("status") == "active":
                    emp_forecast = self.forecast_capacity(employee.get("id"), weeks)
                    team_capacity.append(emp_forecast)
            
            total_capacity = sum(c.get("forecasted_capacity", 0) for c in team_capacity)
            total_workload = sum(c.get("current_workload", 0) for c in team_capacity)
            total_available = sum(c.get("available_capacity", 0) for c in team_capacity)
            
            return {
                "team_forecast": True,
                "forecast_period_weeks": weeks,
                "total_employees": len(team_capacity),
                "total_capacity": round(total_capacity, 2),
                "total_workload": total_workload,
                "total_available_capacity": round(total_available, 2),
                "team_utilization_rate": round((total_workload / total_capacity * 100) if total_capacity > 0 else 0, 2),
                "employee_forecasts": team_capacity
            }
    
    def forecast_project_risk(self, project_id: str) -> Dict[str, Any]:
        """Forecast project completion risk"""
        projects = self.data_manager.load_data("projects") or []
        tasks = self.data_manager.load_data("tasks") or []
        
        project = next((p for p in projects if p.get("id") == project_id), None)
        if not project:
            return {"success": False, "error": "Project not found"}
        
        project_tasks = [t for t in tasks if t.get("project_id") == project_id]
        
        # Calculate completion rate
        total_tasks = len(project_tasks)
        completed_tasks = len([t for t in project_tasks if t.get("status") == "completed"])
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Check deadline risk
        deadline_risk = "low"
        if project.get("deadline"):
            try:
                deadline = datetime.fromisoformat(project["deadline"])
                days_remaining = (deadline - datetime.now()).days
                remaining_tasks = total_tasks - completed_tasks
                
                if days_remaining > 0 and remaining_tasks > 0:
                    tasks_per_day_needed = remaining_tasks / days_remaining
                    # Estimate based on historical rate
                    if completed_tasks > 0:
                        days_elapsed = (datetime.now() - datetime.fromisoformat(project.get("created_at", datetime.now().isoformat()))).days
                        tasks_per_day_actual = completed_tasks / max(days_elapsed, 1)
                        
                        if tasks_per_day_needed > tasks_per_day_actual * 1.5:
                            deadline_risk = "high"
                        elif tasks_per_day_needed > tasks_per_day_actual * 1.2:
                            deadline_risk = "medium"
                    else:
                        deadline_risk = "medium"
                elif days_remaining < 0:
                    deadline_risk = "high"
            except:
                pass
        
        # Resource risk
        resource_risk = "low"
        if project_tasks:
            overdue_tasks = len([t for t in project_tasks 
                               if t.get("status") != "completed" and t.get("due_date") 
                               and datetime.fromisoformat(t.get("due_date")) < datetime.now()])
            if overdue_tasks > total_tasks * 0.3:
                resource_risk = "high"
            elif overdue_tasks > total_tasks * 0.15:
                resource_risk = "medium"
        
        # Overall risk score
        risk_score = self._calculate_risk_score(completion_rate, deadline_risk, resource_risk)
        
        return {
            "project_id": project_id,
            "completion_rate": round(completion_rate, 2),
            "deadline_risk": deadline_risk,
            "resource_risk": resource_risk,
            "overall_risk_score": risk_score,
            "risk_level": "high" if risk_score > 70 else "medium" if risk_score > 40 else "low",
            "recommendations": self._get_risk_recommendations(deadline_risk, resource_risk, completion_rate)
        }
    
    def _calculate_avg_completion_time(self, completed_tasks: List[Dict[str, Any]]) -> float:
        """Calculate average task completion time in days"""
        if not completed_tasks:
            return 5.0  # Default 5 days
        
        total_days = 0
        count = 0
        
        for task in completed_tasks:
            if task.get("created_at") and task.get("completed_at"):
                try:
                    created = datetime.fromisoformat(task["created_at"])
                    completed = datetime.fromisoformat(task["completed_at"])
                    days = (completed - created).days
                    if days > 0:
                        total_days += days
                        count += 1
                except:
                    pass
        
        return total_days / count if count > 0 else 5.0
    
    def _calculate_risk_score(self, completion_rate: float, deadline_risk: str, resource_risk: str) -> float:
        """Calculate overall risk score (0-100)"""
        risk_map = {"low": 20, "medium": 50, "high": 80}
        
        deadline_score = risk_map.get(deadline_risk, 50)
        resource_score = risk_map.get(resource_risk, 50)
        completion_score = max(0, 100 - completion_rate)  # Lower completion = higher risk
        
        # Weighted average
        return (deadline_score * 0.4 + resource_score * 0.3 + completion_score * 0.3)
    
    def _get_capacity_recommendation(self, current_workload: float, forecasted_capacity: float) -> str:
        """Get capacity recommendation"""
        utilization = (current_workload / forecasted_capacity * 100) if forecasted_capacity > 0 else 0
        
        if utilization > 90:
            return "Overloaded - Consider redistributing tasks or adding resources"
        elif utilization > 75:
            return "High utilization - Monitor closely"
        elif utilization > 50:
            return "Optimal capacity - Good balance"
        else:
            return "Underutilized - Can take on more work"
    
    def _get_risk_recommendations(self, deadline_risk: str, resource_risk: str, completion_rate: float) -> List[str]:
        """Get risk mitigation recommendations"""
        recommendations = []
        
        if deadline_risk == "high":
            recommendations.append("Urgent: Project deadline at risk - consider extending deadline or adding resources")
        elif deadline_risk == "medium":
            recommendations.append("Monitor deadline closely - may need intervention")
        
        if resource_risk == "high":
            recommendations.append("High number of overdue tasks - review resource allocation")
        elif resource_risk == "medium":
            recommendations.append("Some tasks overdue - review task priorities")
        
        if completion_rate < 50:
            recommendations.append("Low completion rate - review project scope and timeline")
        elif completion_rate < 70:
            recommendations.append("Moderate completion rate - ensure progress is on track")
        
        if not recommendations:
            recommendations.append("Project is on track - continue monitoring")
        
        return recommendations

