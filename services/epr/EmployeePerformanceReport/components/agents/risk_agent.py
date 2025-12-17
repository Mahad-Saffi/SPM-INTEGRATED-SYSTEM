"""
Risk Detection Agent - Proactive risk identification
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from components.managers.data_manager import DataManager
from components.agents.performance_agent import EnhancedPerformanceAgent
from components.agents.reporting_agent import ReportingAgent


class RiskDetectionAgent:
    """Proactive risk detection agent"""
    
    def __init__(self, data_manager: DataManager, performance_agent: EnhancedPerformanceAgent,
                 reporting_agent: ReportingAgent):
        self.data_manager = data_manager
        self.performance_agent = performance_agent
        self.reporting_agent = reporting_agent
    
    def detect_all_risks(self) -> List[Dict[str, Any]]:
        """Detect all types of risks"""
        risks = []
        
        risks.extend(self.detect_employee_risks())
        risks.extend(self.detect_project_risks())
        risks.extend(self.detect_task_risks())
        risks.extend(self.detect_performance_risks())
        
        # Save risks
        risk_data = self.data_manager.load_data("risks") or []
        for risk in risks:
            if risk not in risk_data:
                risk_data.append(risk)
        self.data_manager.save_data("risks", risk_data)
        
        return risks
    
    def detect_employee_risks(self) -> List[Dict[str, Any]]:
        """Detect employee-related risks"""
        risks = []
        employees = self.data_manager.load_data("employees") or []
        tasks = self.data_manager.load_data("tasks") or []
        performance_data = self.data_manager.load_data("performances") or []
        
        for employee in employees:
            emp_id = employee.get("id")
            emp_tasks = [t for t in tasks if t.get("assigned_to") == emp_id]
            
            # Overwork risk
            if len(emp_tasks) > 10:
                risks.append({
                    "id": self._generate_risk_id(),
                    "type": "employee_overwork",
                    "category": "employee",
                    "severity": "high",
                    "entity_id": emp_id,
                    "entity_type": "employee",
                    "description": f"Employee {employee.get('name')} has {len(emp_tasks)} assigned tasks",
                    "detected_at": datetime.now().isoformat()
                })
            
            # Performance risk
            emp_perf = [p for p in performance_data if p.get("employee_id") == emp_id]
            if emp_perf:
                latest_perf = max(emp_perf, key=lambda x: x.get("evaluated_at", ""))
                if latest_perf.get("performance_score", 100) < 50:
                    risks.append({
                        "id": self._generate_risk_id(),
                        "type": "low_performance",
                        "category": "employee",
                        "severity": "medium",
                        "entity_id": emp_id,
                        "entity_type": "employee",
                        "description": f"Employee {employee.get('name')} has low performance score",
                        "detected_at": datetime.now().isoformat()
                    })
        
        return risks
    
    def detect_project_risks(self) -> List[Dict[str, Any]]:
        """Detect project-related risks"""
        risks = []
        projects = self.data_manager.load_data("projects") or []
        tasks = self.data_manager.load_data("tasks") or []
        
        for project in projects:
            project_id = project.get("id")
            project_tasks = [t for t in tasks if t.get("project_id") == project_id]
            
            # Deadline risk
            if project.get("deadline"):
                try:
                    deadline = datetime.fromisoformat(project["deadline"])
                    days_remaining = (deadline - datetime.now()).days
                    incomplete_tasks = [t for t in project_tasks if t.get("status") != "completed"]
                    
                    if days_remaining < 0:
                        risks.append({
                            "id": self._generate_risk_id(),
                            "type": "deadline_passed",
                            "category": "project",
                            "severity": "high",
                            "entity_id": project_id,
                            "entity_type": "project",
                            "description": f"Project {project.get('name')} deadline has passed",
                            "detected_at": datetime.now().isoformat()
                        })
                    elif days_remaining < 7 and incomplete_tasks:
                        risks.append({
                            "id": self._generate_risk_id(),
                            "type": "approaching_deadline",
                            "category": "project",
                            "severity": "medium",
                            "entity_id": project_id,
                            "entity_type": "project",
                            "description": f"Project {project.get('name')} deadline approaching with {len(incomplete_tasks)} incomplete tasks",
                            "detected_at": datetime.now().isoformat()
                        })
                except:
                    pass
            
            # Low completion risk
            if project_tasks:
                completion_rate = len([t for t in project_tasks if t.get("status") == "completed"]) / len(project_tasks) * 100
                if completion_rate < 30:
                    risks.append({
                        "id": self._generate_risk_id(),
                        "type": "low_completion",
                        "category": "project",
                        "severity": "medium",
                        "entity_id": project_id,
                        "entity_type": "project",
                        "description": f"Project {project.get('name')} has low completion rate: {completion_rate:.1f}%",
                        "detected_at": datetime.now().isoformat()
                    })
        
        return risks
    
    def detect_task_risks(self) -> List[Dict[str, Any]]:
        """Detect task-related risks"""
        risks = []
        tasks = self.data_manager.load_data("tasks") or []
        
        for task in tasks:
            # Overdue task
            if task.get("status") != "completed" and task.get("due_date"):
                try:
                    due_date = datetime.fromisoformat(task["due_date"])
                    if due_date < datetime.now():
                        risks.append({
                            "id": self._generate_risk_id(),
                            "type": "overdue_task",
                            "category": "task",
                            "severity": "high" if task.get("priority") == "high" else "medium",
                            "entity_id": task.get("id"),
                            "entity_type": "task",
                            "description": f"Task '{task.get('title')}' is overdue",
                            "detected_at": datetime.now().isoformat()
                        })
                except:
                    pass
            
            # High priority unassigned
            if task.get("priority") == "high" and not task.get("assigned_to"):
                risks.append({
                    "id": self._generate_risk_id(),
                    "type": "unassigned_high_priority",
                    "category": "task",
                    "severity": "medium",
                    "entity_id": task.get("id"),
                    "entity_type": "task",
                    "description": f"High priority task '{task.get('title')}' is unassigned",
                    "detected_at": datetime.now().isoformat()
                })
        
        return risks
    
    def detect_performance_risks(self) -> List[Dict[str, Any]]:
        """Detect performance-related risks"""
        risks = []
        employees = self.data_manager.load_data("employees") or []
        performance_data = self.data_manager.load_data("performances") or []
        
        # Department performance
        departments = {}
        for employee in employees:
            dept = employee.get("department", "unknown")
            if dept not in departments:
                departments[dept] = []
            departments[dept].append(employee.get("id"))
        
        for dept, emp_ids in departments.items():
            dept_scores = []
            for emp_id in emp_ids:
                emp_perf = [p for p in performance_data if p.get("employee_id") == emp_id]
                if emp_perf:
                    latest = max(emp_perf, key=lambda x: x.get("evaluated_at", ""))
                    dept_scores.append(latest.get("performance_score", 0))
            
            if dept_scores:
                avg_score = sum(dept_scores) / len(dept_scores)
                if avg_score < 60:
                    risks.append({
                        "id": self._generate_risk_id(),
                        "type": "department_low_performance",
                        "category": "performance",
                        "severity": "medium",
                        "entity_id": dept,
                        "entity_type": "department",
                        "description": f"Department {dept} has low average performance: {avg_score:.1f}",
                        "detected_at": datetime.now().isoformat()
                    })
        
        return risks
    
    def get_risks(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get risks with optional filters"""
        risks = self.data_manager.load_data("risks") or []
        
        if not filters:
            return risks
        
        filtered_risks = risks
        if filters.get("category"):
            filtered_risks = [r for r in filtered_risks if r.get("category") == filters["category"]]
        if filters.get("severity"):
            filtered_risks = [r for r in filtered_risks if r.get("severity") == filters["severity"]]
        if filters.get("entity_type"):
            filtered_risks = [r for r in filtered_risks if r.get("entity_type") == filters["entity_type"]]
        
        return filtered_risks
    
    def _generate_risk_id(self) -> str:
        """Generate unique risk ID"""
        risks = self.data_manager.load_data("risks") or []
        return str(len(risks) + 1)

