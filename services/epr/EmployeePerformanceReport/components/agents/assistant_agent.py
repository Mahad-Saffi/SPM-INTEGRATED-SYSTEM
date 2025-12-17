"""
Assistant Agent - Natural language query processing
"""
from typing import Dict, Any, Optional
from components.managers.data_manager import DataManager
from components.agents.performance_agent import EnhancedPerformanceAgent
from components.agents.reporting_agent import ReportingAgent


class AssistantAgent:
    """AI-powered natural language query processing agent"""
    
    def __init__(self, data_manager: DataManager, performance_agent: EnhancedPerformanceAgent,
                 reporting_agent: ReportingAgent):
        self.data_manager = data_manager
        self.performance_agent = performance_agent
        self.reporting_agent = reporting_agent
    
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process natural language query"""
        query_lower = query.lower()
        
        # Performance queries
        if any(keyword in query_lower for keyword in ["performance", "score", "evaluate", "rank"]):
            return self._handle_performance_query(query, context)
        
        # Task queries
        if any(keyword in query_lower for keyword in ["task", "todo", "assignment"]):
            return self._handle_task_query(query, context)
        
        # Project queries
        if any(keyword in query_lower for keyword in ["project", "status", "progress"]):
            return self._handle_project_query(query, context)
        
        # Team queries
        if any(keyword in query_lower for keyword in ["team", "employee", "staff", "worker"]):
            return self._handle_team_query(query, context)
        
        # Analytics queries
        if any(keyword in query_lower for keyword in ["analytics", "report", "overview", "dashboard"]):
            return self._handle_analytics_query(query, context)
        
        # Default response
        return {
            "response": "I can help you with performance, tasks, projects, team information, and analytics. Please rephrase your question.",
            "suggestions": [
                "What is the performance of employee X?",
                "Show me all pending tasks",
                "What is the status of project Y?",
                "Generate an overview report"
            ]
        }
    
    def _handle_performance_query(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle performance-related queries"""
        employees = self.data_manager.load_data("employees") or []
        
        # Try to extract employee name/ID from query
        employee_id = None
        if context and context.get("employee_id"):
            employee_id = context["employee_id"]
        else:
            # Simple name matching
            query_lower = query.lower()
            for emp in employees:
                if emp.get("name", "").lower() in query_lower:
                    employee_id = emp.get("id")
                    break
        
        if employee_id:
            # Don't save, just read existing performance data
            evaluation = self.performance_agent.evaluate_employee(employee_id, save=False)
            return {
                "response": f"Performance evaluation for employee {employee_id}: Score: {evaluation.get('performance_score')}, Rank: {evaluation.get('rank')}, Trend: {evaluation.get('trend')}",
                "data": evaluation
            }
        else:
            return {
                "response": "Please specify which employee's performance you'd like to check.",
                "employees": [{"id": e.get("id"), "name": e.get("name")} for e in employees]
            }
    
    def _handle_task_query(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle task-related queries"""
        tasks = self.data_manager.load_data("tasks") or []
        query_lower = query.lower()
        
        if "pending" in query_lower or "incomplete" in query_lower:
            pending = [t for t in tasks if t.get("status") == "pending"]
            return {
                "response": f"There are {len(pending)} pending tasks.",
                "data": pending[:10]  # Limit to 10
            }
        
        if "overdue" in query_lower:
            from datetime import datetime
            overdue = []
            for task in tasks:
                if task.get("status") != "completed" and task.get("due_date"):
                    try:
                        due_date = datetime.fromisoformat(task["due_date"])
                        if due_date < datetime.now():
                            overdue.append(task)
                    except:
                        pass
            return {
                "response": f"There are {len(overdue)} overdue tasks.",
                "data": overdue
            }
        
        return {
            "response": f"Total tasks: {len(tasks)}",
            "data": tasks[:10]
        }
    
    def _handle_project_query(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle project-related queries"""
        projects = self.data_manager.load_data("projects") or []
        query_lower = query.lower()
        
        if "active" in query_lower:
            active = [p for p in projects if p.get("status") == "active"]
            return {
                "response": f"There are {len(active)} active projects.",
                "data": active
            }
        
        if "overview" in query_lower or "report" in query_lower:
            overview = self.reporting_agent.generate_overview_report()
            return {
                "response": "Here is the system overview report.",
                "data": overview
            }
        
        return {
            "response": f"Total projects: {len(projects)}",
            "data": projects
        }
    
    def _handle_team_query(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle team-related queries"""
        employees = self.data_manager.load_data("employees") or []
        query_lower = query.lower()
        
        if "list" in query_lower or "all" in query_lower:
            return {
                "response": f"There are {len(employees)} employees in the system.",
                "data": employees
            }
        
        return {
            "response": f"Total employees: {len(employees)}",
            "data": employees
        }
    
    def _handle_analytics_query(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle analytics-related queries"""
        overview = self.reporting_agent.generate_overview_report()
        return {
            "response": "Here is the system analytics overview.",
            "data": overview
        }

