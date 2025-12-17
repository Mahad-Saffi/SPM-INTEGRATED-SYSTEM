"""
Reporting Agent - Comprehensive project reports and analytics
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from components.managers.data_manager import DataManager


class ReportingAgent:
    """Comprehensive reporting and analytics agent"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
    
    def generate_project_report(self, project_id: str) -> Dict[str, Any]:
        """Generate detailed project report"""
        projects = self.data_manager.load_data("projects") or []
        tasks = self.data_manager.load_data("tasks") or []
        employees = self.data_manager.load_data("employees") or []
        
        project = next((p for p in projects if p.get("id") == project_id), None)
        if not project:
            return {"error": "Project not found"}
        
        project_tasks = [t for t in tasks if t.get("project_id") == project_id]
        
        # Calculate metrics
        total_tasks = len(project_tasks)
        completed_tasks = len([t for t in project_tasks if t.get("status") == "completed"])
        pending_tasks = len([t for t in project_tasks if t.get("status") == "pending"])
        in_progress_tasks = len([t for t in project_tasks if t.get("status") == "in_progress"])
        
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Calculate project health
        health_score = self._calculate_project_health(project, project_tasks)
        
        # Identify risks
        risks = self._identify_project_risks(project, project_tasks)
        
        # Resource allocation
        resource_allocation = self._analyze_resource_allocation(project_tasks, employees)
        
        # Estimate completion date
        estimated_completion = self._estimate_completion_date(project, project_tasks)
        
        report = {
            "project_id": project_id,
            "project_name": project.get("name"),
            "status": project.get("status"),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "in_progress_tasks": in_progress_tasks,
            "completion_rate": round(completion_rate, 2),
            "health_score": health_score,
            "risks": risks,
            "resource_allocation": resource_allocation,
            "estimated_completion_date": estimated_completion,
            "generated_at": datetime.now().isoformat()
        }
        
        return report
    
    def generate_overview_report(self) -> Dict[str, Any]:
        """Generate system overview report"""
        projects = self.data_manager.load_data("projects") or []
        tasks = self.data_manager.load_data("tasks") or []
        employees = self.data_manager.load_data("employees") or []
        performance_data = self.data_manager.load_data("performances") or []
        
        # Project statistics
        total_projects = len(projects)
        active_projects = len([p for p in projects if p.get("status") == "active"])
        completed_projects = len([p for p in projects if p.get("status") == "completed"])
        
        # Task statistics
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.get("status") == "completed"])
        overdue_tasks = self._count_overdue_tasks(tasks)
        
        # Employee statistics
        total_employees = len(employees)
        active_employees = total_employees  # All employees are active
        
        # Performance statistics
        avg_performance = self._calculate_avg_performance(performance_data)
        
        # Resource allocation
        resource_utilization = self._calculate_resource_utilization(tasks, employees)
        
        overview = {
            "projects": {
                "total": total_projects,
                "active": active_projects,
                "completed": completed_projects
            },
            "tasks": {
                "total": total_tasks,
                "completed": completed_tasks,
                "overdue": overdue_tasks,
                "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            },
            "employees": {
                "total": total_employees,
                "active": active_employees
            },
            "performance": {
                "average_score": round(avg_performance, 2)
            },
            "resource_utilization": resource_utilization,
            "generated_at": datetime.now().isoformat()
        }
        
        return overview
    
    def _calculate_project_health(self, project: Dict[str, Any], tasks: List[Dict[str, Any]]) -> float:
        """Calculate project health score (0-100)"""
        if not tasks:
            return 100.0
        
        # Factors affecting health
        completion_rate = len([t for t in tasks if t.get("status") == "completed"]) / len(tasks) * 100
        
        # Check for overdue tasks
        overdue_count = self._count_overdue_tasks(tasks)
        overdue_penalty = (overdue_count / len(tasks)) * 30  # Max 30 point penalty
        
        # Check deadline proximity
        deadline_penalty = 0
        if project.get("deadline"):
            try:
                deadline = datetime.fromisoformat(project["deadline"])
                days_remaining = (deadline - datetime.now()).days
                if days_remaining < 0:
                    deadline_penalty = 20
                elif days_remaining < 7:
                    deadline_penalty = 10
            except:
                pass
        
        health_score = completion_rate - overdue_penalty - deadline_penalty
        return max(0, min(100, health_score))
    
    def _identify_project_risks(self, project: Dict[str, Any], tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify project risks"""
        risks = []
        
        # Overdue tasks risk
        overdue_tasks = self._get_overdue_tasks(tasks)
        if overdue_tasks:
            risks.append({
                "type": "overdue_tasks",
                "severity": "high" if len(overdue_tasks) > 3 else "medium",
                "description": f"{len(overdue_tasks)} tasks are overdue",
                "count": len(overdue_tasks)
            })
        
        # Deadline risk
        if project.get("deadline"):
            try:
                deadline = datetime.fromisoformat(project["deadline"])
                days_remaining = (deadline - datetime.now()).days
                incomplete_tasks = len([t for t in tasks if t.get("status") != "completed"])
                
                if days_remaining < 0:
                    risks.append({
                        "type": "deadline_passed",
                        "severity": "high",
                        "description": "Project deadline has passed",
                        "days_overdue": abs(days_remaining)
                    })
                elif days_remaining < 7 and incomplete_tasks > 0:
                    risks.append({
                        "type": "approaching_deadline",
                        "severity": "medium",
                        "description": f"Deadline approaching with {incomplete_tasks} incomplete tasks",
                        "days_remaining": days_remaining
                    })
            except:
                pass
        
        # Low completion rate risk
        if tasks:
            completion_rate = len([t for t in tasks if t.get("status") == "completed"]) / len(tasks) * 100
            if completion_rate < 50:
                risks.append({
                    "type": "low_completion",
                    "severity": "medium",
                    "description": f"Low completion rate: {completion_rate:.1f}%",
                    "completion_rate": completion_rate
                })
        
        return risks
    
    def _analyze_resource_allocation(self, tasks: List[Dict[str, Any]], employees: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze resource allocation"""
        allocation = {}
        for employee in employees:
            emp_id = employee.get("id")
            emp_tasks = [t for t in tasks if t.get("assigned_to") == emp_id]
            allocation[emp_id] = {
                "name": employee.get("name"),
                "task_count": len(emp_tasks),
                "completed": len([t for t in emp_tasks if t.get("status") == "completed"]),
                "pending": len([t for t in emp_tasks if t.get("status") == "pending"])
            }
        return allocation
    
    def _estimate_completion_date(self, project: Dict[str, Any], tasks: List[Dict[str, Any]]) -> Optional[str]:
        """Estimate project completion date"""
        incomplete_tasks = [t for t in tasks if t.get("status") != "completed"]
        if not incomplete_tasks:
            return datetime.now().isoformat()
        
        # Get average completion time
        completed_tasks = [t for t in tasks if t.get("status") == "completed"]
        if completed_tasks:
            completion_times = []
            for task in completed_tasks:
                if task.get("created_at") and task.get("completed_at"):
                    try:
                        created = datetime.fromisoformat(task["created_at"])
                        completed = datetime.fromisoformat(task["completed_at"])
                        completion_times.append((completed - created).days)
                    except:
                        pass
            
            if completion_times:
                avg_days = sum(completion_times) / len(completion_times)
                estimated = datetime.now() + timedelta(days=int(avg_days * len(incomplete_tasks)))
                return estimated.isoformat()
        
        return None
    
    def _count_overdue_tasks(self, tasks: List[Dict[str, Any]]) -> int:
        """Count overdue tasks"""
        return len(self._get_overdue_tasks(tasks))
    
    def _get_overdue_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get overdue tasks"""
        overdue = []
        for task in tasks:
            if task.get("status") != "completed" and task.get("due_date"):
                try:
                    due_date = datetime.fromisoformat(task["due_date"])
                    if due_date < datetime.now():
                        overdue.append(task)
                except:
                    pass
        return overdue
    
    def _calculate_avg_performance(self, performance_data: List[Dict[str, Any]]) -> float:
        """Calculate average performance score"""
        if not performance_data:
            return 0.0
        
        # Get latest evaluation for each employee
        latest_scores = {}
        for perf in performance_data:
            emp_id = perf.get("employee_id")
            score = perf.get("performance_score", 0)
            if emp_id not in latest_scores or perf.get("evaluated_at", "") > latest_scores[emp_id].get("evaluated_at", ""):
                latest_scores[emp_id] = perf
        
        scores = [p.get("performance_score", 0) for p in latest_scores.values()]
        return sum(scores) / len(scores) if scores else 0.0
    
    def _calculate_resource_utilization(self, tasks: List[Dict[str, Any]], employees: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate resource utilization"""
        total_employees = len(employees)
        employees_with_tasks = len(set([t.get("assigned_to") for t in tasks if t.get("assigned_to")]))
        
        utilization_rate = (employees_with_tasks / total_employees * 100) if total_employees > 0 else 0
        
        return {
            "total_employees": total_employees,
            "employees_with_tasks": employees_with_tasks,
            "utilization_rate": round(utilization_rate, 2)
        }

