"""
MCP Server for Employee Performance Report System
Provides automation tools for performance evaluation, notifications, reports, and more.
"""
import asyncio
import json
import sys
import httpx
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path

# Add parent directory to path to import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    # Fallback for alternative MCP implementations
    try:
        from mcp import Server, stdio_server, Tool, TextContent
    except ImportError:
        print("Warning: MCP library not found. Install with: pip install mcp")
        # Create minimal stubs for development
        class Server:
            def __init__(self, name):
                self.name = name
            def list_tools(self):
                pass
            def call_tool(self):
                pass
            def run(self, *args, **kwargs):
                pass
            def create_initialization_options(self):
                return {}
        
        class Tool:
            def __init__(self, **kwargs):
                pass
        
        class TextContent:
            def __init__(self, **kwargs):
                pass
        
        def stdio_server():
            return None, None
from components.managers.data_manager import DataManager
from components.agents.performance_agent import EnhancedPerformanceAgent
from components.agents.notification_agent import NotificationAgent
from components.agents.reporting_agent import ReportingAgent
from components.agents.risk_agent import RiskDetectionAgent
from components.agents.task_agent import TaskAgent
from components.agents.goal_agent import GoalAgent
from components.agents.export_agent import ExportAgent
from components.agents.workload_agent import WorkloadAgent
from components.agents.attendance_agent import AttendanceAgent

# Initialize server
server = Server("employee-performance-automation")

# Initialize data manager and agents
data_manager = DataManager()
performance_agent = EnhancedPerformanceAgent(data_manager)
notification_agent = NotificationAgent(data_manager)
reporting_agent = ReportingAgent(data_manager)
risk_agent = RiskDetectionAgent(data_manager, performance_agent, reporting_agent)
task_agent = TaskAgent(data_manager, notification_agent)
goal_agent = GoalAgent(data_manager, notification_agent)
export_agent = ExportAgent(data_manager)
workload_agent = WorkloadAgent(data_manager)
attendance_agent = AttendanceAgent(data_manager)


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List all available automation tools"""
    return [
        Tool(
            name="evaluate_all_employees",
            description="Automatically evaluate performance for all employees",
            inputSchema={
                "type": "object",
                "properties": {
                    "save_results": {
                        "type": "boolean",
                        "description": "Whether to save evaluation results (default: True)",
                        "default": True
                    }
                }
            }
        ),
        Tool(
            name="detect_all_risks",
            description="Automatically detect all risks in the system (employees, projects, tasks, performance)",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="send_notification",
            description="Send a notification to an employee",
            inputSchema={
                "type": "object",
                "properties": {
                    "employee_id": {
                        "type": "string",
                        "description": "Employee ID to send notification to"
                    },
                    "title": {
                        "type": "string",
                        "description": "Notification title"
                    },
                    "message": {
                        "type": "string",
                        "description": "Notification message"
                    },
                    "notification_type": {
                        "type": "string",
                        "description": "Type of notification (info, warning, success, error)",
                        "enum": ["info", "warning", "success", "error"]
                    }
                },
                "required": ["employee_id", "title", "message"]
            }
        ),
        Tool(
            name="generate_performance_report",
            description="Generate a performance report for an employee",
            inputSchema={
                "type": "object",
                "properties": {
                    "employee_id": {
                        "type": "string",
                        "description": "Employee ID to generate report for"
                    },
                    "format": {
                        "type": "string",
                        "description": "Report format (json, pdf, csv)",
                        "enum": ["json", "pdf", "csv"],
                        "default": "json"
                    }
                },
                "required": ["employee_id"]
            }
        ),
        Tool(
            name="check_overdue_tasks",
            description="Check for overdue tasks and send notifications",
            inputSchema={
                "type": "object",
                "properties": {
                    "send_notifications": {
                        "type": "boolean",
                        "description": "Whether to send notifications for overdue tasks (default: True)",
                        "default": True
                    }
                }
            }
        ),
        Tool(
            name="check_overdue_goals",
            description="Check for overdue goals and send notifications",
            inputSchema={
                "type": "object",
                "properties": {
                    "send_notifications": {
                        "type": "boolean",
                        "description": "Whether to send notifications for overdue goals (default: True)",
                        "default": True
                    }
                }
            }
        ),
        Tool(
            name="assess_workload",
            description="Assess workload for all employees and identify overloaded employees",
            inputSchema={
                "type": "object",
                "properties": {
                    "threshold": {
                        "type": "integer",
                        "description": "Maximum number of active tasks before considered overloaded (default: 10)",
                        "default": 10
                    }
                }
            }
        ),
        Tool(
            name="generate_project_report",
            description="Generate a comprehensive report for a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project ID to generate report for"
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="export_data",
            description="Export data to CSV or PDF format",
            inputSchema={
                "type": "object",
                "properties": {
                    "data_type": {
                        "type": "string",
                        "description": "Type of data to export",
                        "enum": ["projects", "tasks", "employees", "performances", "goals", "feedback"]
                    },
                    "format": {
                        "type": "string",
                        "description": "Export format (csv, pdf)",
                        "enum": ["csv", "pdf"],
                        "default": "csv"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional output file path"
                    }
                },
                "required": ["data_type"]
            }
        ),
        Tool(
            name="record_attendance",
            description="Record employee attendance (check-in or check-out)",
            inputSchema={
                "type": "object",
                "properties": {
                    "employee_id": {
                        "type": "string",
                        "description": "Employee ID"
                    },
                    "action": {
                        "type": "string",
                        "description": "Attendance action (checkin, checkout)",
                        "enum": ["checkin", "checkout"]
                    },
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format (default: today)"
                    }
                },
                "required": ["employee_id", "action"]
            }
        ),
        Tool(
            name="get_employee_stats",
            description="Get comprehensive statistics for an employee",
            inputSchema={
                "type": "object",
                "properties": {
                    "employee_id": {
                        "type": "string",
                        "description": "Employee ID"
                    }
                },
                "required": ["employee_id"]
            }
        ),
        Tool(
            name="automated_daily_check",
            description="Run automated daily checks: evaluate performance, detect risks, check overdue items",
            inputSchema={
                "type": "object",
                "properties": {
                    "evaluate_performance": {
                        "type": "boolean",
                        "description": "Whether to evaluate all employees (default: True)",
                        "default": True
                    },
                    "detect_risks": {
                        "type": "boolean",
                        "description": "Whether to detect risks (default: True)",
                        "default": True
                    },
                    "check_overdue": {
                        "type": "boolean",
                        "description": "Whether to check for overdue tasks/goals (default: True)",
                        "default": True
                    }
                }
            }
        ),
        # New Atlas Integration Tools
        Tool(
            name="get_user_performance",
            description="Get comprehensive performance data for a user (combines Atlas task data with local performance data)",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User ID from Atlas"
                    },
                    "time_period": {
                        "type": "string",
                        "description": "Time period for analysis (monthly, quarterly, yearly)",
                        "enum": ["monthly", "quarterly", "yearly"],
                        "default": "quarterly"
                    },
                    "atlas_token": {
                        "type": "string",
                        "description": "Atlas JWT token for API access"
                    }
                },
                "required": ["user_id", "atlas_token"]
            }
        ),
        Tool(
            name="create_performance_review",
            description="Create a new performance review for an employee",
            inputSchema={
                "type": "object",
                "properties": {
                    "employee_id": {
                        "type": "string",
                        "description": "Employee ID from Atlas"
                    },
                    "review_period_start": {
                        "type": "string",
                        "description": "Review period start date (YYYY-MM-DD)"
                    },
                    "review_period_end": {
                        "type": "string",
                        "description": "Review period end date (YYYY-MM-DD)"
                    },
                    "overall_rating": {
                        "type": "number",
                        "description": "Overall performance rating (0-100)"
                    },
                    "strengths": {
                        "type": "string",
                        "description": "Employee strengths"
                    },
                    "areas_for_improvement": {
                        "type": "string",
                        "description": "Areas for improvement"
                    },
                    "atlas_token": {
                        "type": "string",
                        "description": "Atlas JWT token"
                    }
                },
                "required": ["employee_id", "review_period_start", "review_period_end", "atlas_token"]
            }
        ),
        Tool(
            name="set_performance_goal",
            description="Set a performance goal for a user",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User ID from Atlas"
                    },
                    "title": {
                        "type": "string",
                        "description": "Goal title"
                    },
                    "description": {
                        "type": "string",
                        "description": "Goal description"
                    },
                    "goal_type": {
                        "type": "string",
                        "description": "Goal type",
                        "enum": ["quantitative", "qualitative", "skill_based"]
                    },
                    "target_value": {
                        "type": "number",
                        "description": "Target value for quantitative goals"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Goal start date (YYYY-MM-DD)"
                    },
                    "target_date": {
                        "type": "string",
                        "description": "Goal target date (YYYY-MM-DD)"
                    },
                    "atlas_token": {
                        "type": "string",
                        "description": "Atlas JWT token"
                    }
                },
                "required": ["user_id", "title", "goal_type", "start_date", "target_date", "atlas_token"]
            }
        ),
        Tool(
            name="get_team_performance",
            description="Get team performance analytics for an organization",
            inputSchema={
                "type": "object",
                "properties": {
                    "organization_id": {
                        "type": "string",
                        "description": "Organization ID from Atlas"
                    },
                    "atlas_token": {
                        "type": "string",
                        "description": "Atlas JWT token"
                    }
                },
                "required": ["organization_id", "atlas_token"]
            }
        ),
        Tool(
            name="submit_peer_feedback",
            description="Submit peer feedback for an employee",
            inputSchema={
                "type": "object",
                "properties": {
                    "employee_id": {
                        "type": "string",
                        "description": "Employee ID receiving feedback"
                    },
                    "project_id": {
                        "type": "string",
                        "description": "Project ID from Atlas (optional)"
                    },
                    "feedback_type": {
                        "type": "string",
                        "description": "Type of feedback",
                        "enum": ["positive", "constructive", "general"]
                    },
                    "rating": {
                        "type": "number",
                        "description": "Rating (1-5 scale)"
                    },
                    "feedback_text": {
                        "type": "string",
                        "description": "Feedback text"
                    },
                    "is_anonymous": {
                        "type": "boolean",
                        "description": "Whether feedback is anonymous",
                        "default": False
                    },
                    "atlas_token": {
                        "type": "string",
                        "description": "Atlas JWT token"
                    }
                },
                "required": ["employee_id", "feedback_type", "rating", "feedback_text", "atlas_token"]
            }
        ),
        Tool(
            name="assess_skills",
            description="Assess skills for a user",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User ID from Atlas"
                    },
                    "skill_name": {
                        "type": "string",
                        "description": "Name of the skill"
                    },
                    "skill_category": {
                        "type": "string",
                        "description": "Skill category",
                        "enum": ["technical", "soft", "domain"]
                    },
                    "proficiency_level": {
                        "type": "string",
                        "description": "Proficiency level",
                        "enum": ["beginner", "intermediate", "advanced", "expert"]
                    },
                    "proficiency_score": {
                        "type": "number",
                        "description": "Proficiency score (0-100)"
                    },
                    "assessment_method": {
                        "type": "string",
                        "description": "Assessment method",
                        "enum": ["self", "peer", "manager", "test"]
                    },
                    "atlas_token": {
                        "type": "string",
                        "description": "Atlas JWT token"
                    }
                },
                "required": ["user_id", "skill_name", "proficiency_level", "proficiency_score", "atlas_token"]
            }
        ),
        Tool(
            name="identify_skill_gaps",
            description="Identify skill gaps for a user",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User ID from Atlas"
                    },
                    "project_id": {
                        "type": "string",
                        "description": "Project ID from Atlas (optional)"
                    },
                    "atlas_token": {
                        "type": "string",
                        "description": "Atlas JWT token"
                    }
                },
                "required": ["user_id", "atlas_token"]
            }
        ),
        Tool(
            name="track_goal_progress",
            description="Update goal progress",
            inputSchema={
                "type": "object",
                "properties": {
                    "goal_id": {
                        "type": "integer",
                        "description": "Goal ID"
                    },
                    "current_value": {
                        "type": "number",
                        "description": "Current progress value"
                    },
                    "status": {
                        "type": "string",
                        "description": "Goal status",
                        "enum": ["in_progress", "achieved", "missed"]
                    },
                    "atlas_token": {
                        "type": "string",
                        "description": "Atlas JWT token"
                    }
                },
                "required": ["goal_id", "atlas_token"]
            }
        ),
        Tool(
            name="generate_performance_report_api",
            description="Generate performance report via API (quarterly, monthly, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User ID from Atlas"
                    },
                    "report_type": {
                        "type": "string",
                        "description": "Report type",
                        "enum": ["quarterly", "monthly", "yearly"],
                        "default": "quarterly"
                    },
                    "quarter": {
                        "type": "integer",
                        "description": "Quarter number (1-4) for quarterly reports"
                    },
                    "year": {
                        "type": "integer",
                        "description": "Year for the report"
                    },
                    "atlas_token": {
                        "type": "string",
                        "description": "Atlas JWT token"
                    }
                },
                "required": ["user_id", "atlas_token"]
            }
        ),
        Tool(
            name="predict_performance_trend",
            description="Predict performance trend for a user",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User ID from Atlas"
                    },
                    "prediction_months": {
                        "type": "integer",
                        "description": "Number of months to predict ahead",
                        "default": 3
                    },
                    "atlas_token": {
                        "type": "string",
                        "description": "Atlas JWT token"
                    }
                },
                "required": ["user_id", "atlas_token"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    try:
        if name == "evaluate_all_employees":
            return await handle_evaluate_all_employees(arguments)
        elif name == "detect_all_risks":
            return await handle_detect_all_risks(arguments)
        elif name == "send_notification":
            return await handle_send_notification(arguments)
        elif name == "generate_performance_report":
            return await handle_generate_performance_report(arguments)
        elif name == "check_overdue_tasks":
            return await handle_check_overdue_tasks(arguments)
        elif name == "check_overdue_goals":
            return await handle_check_overdue_goals(arguments)
        elif name == "assess_workload":
            return await handle_assess_workload(arguments)
        elif name == "generate_project_report":
            return await handle_generate_project_report(arguments)
        elif name == "export_data":
            return await handle_export_data(arguments)
        elif name == "record_attendance":
            return await handle_record_attendance(arguments)
        elif name == "get_employee_stats":
            return await handle_get_employee_stats(arguments)
        elif name == "automated_daily_check":
            return await handle_automated_daily_check(arguments)
        # New Atlas Integration Tools
        elif name == "get_user_performance":
            return await handle_get_user_performance(arguments)
        elif name == "create_performance_review":
            return await handle_create_performance_review(arguments)
        elif name == "set_performance_goal":
            return await handle_set_performance_goal(arguments)
        elif name == "get_team_performance":
            return await handle_get_team_performance(arguments)
        elif name == "submit_peer_feedback":
            return await handle_submit_peer_feedback(arguments)
        elif name == "assess_skills":
            return await handle_assess_skills(arguments)
        elif name == "identify_skill_gaps":
            return await handle_identify_skill_gaps(arguments)
        elif name == "track_goal_progress":
            return await handle_track_goal_progress(arguments)
        elif name == "generate_performance_report_api":
            return await handle_generate_performance_report_api(arguments)
        elif name == "predict_performance_trend":
            return await handle_predict_performance_trend(arguments)
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error executing tool {name}: {str(e)}"
        )]


# Tool handlers
async def handle_evaluate_all_employees(arguments: Dict[str, Any]) -> List[TextContent]:
    """Evaluate performance for all employees"""
    save_results = arguments.get("save_results", True)
    employees = data_manager.load_data("employees") or []
    
    results = []
    for employee in employees:
        employee_id = employee.get("id")
        if employee_id:
            evaluation = performance_agent.evaluate_employee(employee_id, save=save_results)
            results.append({
                "employee_id": employee_id,
                "employee_name": employee.get("name"),
                "performance_score": evaluation.get("performance_score", 0),
                "completion_rate": evaluation.get("completion_rate", 0),
                "on_time_rate": evaluation.get("on_time_rate", 0),
                "rank": evaluation.get("rank", "N/A")
            })
    
    return [TextContent(
        type="text",
        text=json.dumps({
            "status": "success",
            "message": f"Evaluated {len(results)} employees",
            "results": results
        }, indent=2)
    )]


async def handle_detect_all_risks(arguments: Dict[str, Any]) -> List[TextContent]:
    """Detect all risks in the system"""
    risks = risk_agent.detect_all_risks()
    
    return [TextContent(
        type="text",
        text=json.dumps({
            "status": "success",
            "total_risks": len(risks),
            "risks": risks
        }, indent=2, default=str)
    )]


async def handle_send_notification(arguments: Dict[str, Any]) -> List[TextContent]:
    """Send a notification to an employee"""
    employee_id = arguments["employee_id"]
    title = arguments["title"]
    message = arguments["message"]
    notification_type = arguments.get("notification_type", "info")
    
    notification_agent.send_notification(
        recipient=employee_id,
        title=title,
        message=message,
        notification_type=notification_type
    )
    
    return [TextContent(
        type="text",
        text=json.dumps({
            "status": "success",
            "message": f"Notification sent to employee {employee_id}"
        }, indent=2)
    )]


async def handle_generate_performance_report(arguments: Dict[str, Any]) -> List[TextContent]:
    """Generate a performance report"""
    employee_id = arguments["employee_id"]
    format_type = arguments.get("format", "json")
    
    evaluation = performance_agent.evaluate_employee(employee_id, save=False)
    
    if format_type == "json":
        return [TextContent(
            type="text",
            text=json.dumps(evaluation, indent=2, default=str)
        )]
    else:
        # For PDF/CSV, use export agent
        result = export_agent.export_performance_report(employee_id, format_type)
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "success",
                "message": f"Report generated in {format_type} format",
                "file_path": result.get("file_path", "N/A")
            }, indent=2)
        )]


async def handle_check_overdue_tasks(arguments: Dict[str, Any]) -> List[TextContent]:
    """Check for overdue tasks"""
    send_notifications = arguments.get("send_notifications", True)
    tasks = data_manager.load_data("tasks") or []
    today = datetime.now()
    
    overdue_tasks = []
    for task in tasks:
        if task.get("status") not in ["completed", "cancelled"] and task.get("due_date"):
            try:
                due_date = datetime.fromisoformat(task["due_date"])
                if due_date < today:
                    overdue_tasks.append(task)
                    if send_notifications and task.get("assigned_to"):
                        notification_agent.send_notification(
                            recipient=task["assigned_to"],
                            title="Overdue Task",
                            message=f"Task '{task.get('title')}' is overdue. Due date: {due_date.strftime('%Y-%m-%d')}",
                            notification_type="warning"
                        )
            except:
                pass
    
    return [TextContent(
        type="text",
        text=json.dumps({
            "status": "success",
            "overdue_count": len(overdue_tasks),
            "overdue_tasks": overdue_tasks
        }, indent=2, default=str)
    )]


async def handle_check_overdue_goals(arguments: Dict[str, Any]) -> List[TextContent]:
    """Check for overdue goals"""
    send_notifications = arguments.get("send_notifications", True)
    goals = data_manager.load_data("goals") or []
    today = datetime.now()
    
    overdue_goals = []
    for goal in goals:
        if goal.get("status") not in ["completed", "cancelled"] and goal.get("deadline"):
            try:
                deadline = datetime.fromisoformat(goal["deadline"])
                if deadline < today:
                    overdue_goals.append(goal)
                    if send_notifications and goal.get("employee_id"):
                        notification_agent.send_notification(
                            recipient=goal["employee_id"],
                            title="Overdue Goal",
                            message=f"Goal '{goal.get('title')}' is overdue. Deadline: {deadline.strftime('%Y-%m-%d')}",
                            notification_type="warning"
                        )
            except:
                pass
    
    return [TextContent(
        type="text",
        text=json.dumps({
            "status": "success",
            "overdue_count": len(overdue_goals),
            "overdue_goals": overdue_goals
        }, indent=2, default=str)
    )]


async def handle_assess_workload(arguments: Dict[str, Any]) -> List[TextContent]:
    """Assess workload for all employees"""
    threshold = arguments.get("threshold", 10)
    employees = data_manager.load_data("employees") or []
    
    workload_results = []
    for employee in employees:
        employee_id = employee.get("id")
        if employee_id:
            workload = workload_agent.assess_workload(employee_id)
            workload_results.append({
                "employee_id": employee_id,
                "employee_name": employee.get("name"),
                "workload": workload,
                "overloaded": workload.get("active_tasks", 0) > threshold
            })
    
    return [TextContent(
        type="text",
        text=json.dumps({
            "status": "success",
            "threshold": threshold,
            "results": workload_results
        }, indent=2, default=str)
    )]


async def handle_generate_project_report(arguments: Dict[str, Any]) -> List[TextContent]:
    """Generate a project report"""
    project_id = arguments["project_id"]
    report = reporting_agent.generate_project_report(project_id)
    
    return [TextContent(
        type="text",
        text=json.dumps(report, indent=2, default=str)
    )]


async def handle_export_data(arguments: Dict[str, Any]) -> List[TextContent]:
    """Export data to CSV or PDF"""
    data_type = arguments["data_type"]
    format_type = arguments.get("format", "csv")
    output_path = arguments.get("output_path")
    
    data = data_manager.load_data(data_type) or []
    
    if format_type == "csv":
        result = export_agent.export_to_csv(data, output_path=output_path)
    else:
        result = export_agent.export_to_pdf(data, output_path=output_path)
    
    return [TextContent(
        type="text",
        text=json.dumps({
            "status": "success",
            "message": f"Data exported to {format_type}",
            "file_path": result.get("file_path", "N/A")
        }, indent=2)
    )]


async def handle_record_attendance(arguments: Dict[str, Any]) -> List[TextContent]:
    """Record employee attendance"""
    employee_id = arguments["employee_id"]
    action = arguments["action"]
    date_str = arguments.get("date", datetime.now().strftime("%Y-%m-%d"))
    
    if action == "checkin":
        result = attendance_agent.record_checkin(employee_id, date_str)
    else:
        result = attendance_agent.record_checkout(employee_id, date_str)
    
    return [TextContent(
        type="text",
        text=json.dumps({
            "status": "success",
            "message": f"Attendance {action} recorded",
            "result": result
        }, indent=2, default=str)
    )]


async def handle_get_employee_stats(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get comprehensive employee statistics"""
    employee_id = arguments["employee_id"]
    
    # Get performance evaluation
    performance = performance_agent.evaluate_employee(employee_id, save=False)
    
    # Get workload
    workload = workload_agent.assess_workload(employee_id)
    
    # Get tasks
    tasks = data_manager.load_data("tasks") or []
    employee_tasks = [t for t in tasks if t.get("assigned_to") == employee_id]
    
    # Get goals
    goals = data_manager.load_data("goals") or []
    employee_goals = [g for g in goals if g.get("employee_id") == employee_id]
    
    stats = {
        "employee_id": employee_id,
        "performance": performance,
        "workload": workload,
        "tasks": {
            "total": len(employee_tasks),
            "completed": len([t for t in employee_tasks if t.get("status") == "completed"]),
            "pending": len([t for t in employee_tasks if t.get("status") == "pending"]),
            "in_progress": len([t for t in employee_tasks if t.get("status") == "in_progress"])
        },
        "goals": {
            "total": len(employee_goals),
            "completed": len([g for g in employee_goals if g.get("status") == "completed"]),
            "active": len([g for g in employee_goals if g.get("status") == "active"])
        }
    }
    
    return [TextContent(
        type="text",
        text=json.dumps(stats, indent=2, default=str)
    )]


async def handle_automated_daily_check(arguments: Dict[str, Any]) -> List[TextContent]:
    """Run automated daily checks"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    if arguments.get("evaluate_performance", True):
        eval_result = await handle_evaluate_all_employees({"save_results": True})
        results["checks"]["performance_evaluation"] = json.loads(eval_result[0].text)
    
    if arguments.get("detect_risks", True):
        risk_result = await handle_detect_all_risks({})
        results["checks"]["risk_detection"] = json.loads(risk_result[0].text)
    
    if arguments.get("check_overdue", True):
        task_result = await handle_check_overdue_tasks({"send_notifications": True})
        results["checks"]["overdue_tasks"] = json.loads(task_result[0].text)
        
        goal_result = await handle_check_overdue_goals({"send_notifications": True})
        results["checks"]["overdue_goals"] = json.loads(goal_result[0].text)
    
    return [TextContent(
        type="text",
        text=json.dumps(results, indent=2, default=str)
    )]


# Atlas Integration Tool Handlers
async def handle_get_user_performance(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get user performance via API"""
    user_id = arguments.get("user_id")
    time_period = arguments.get("time_period", "quarterly")
    token = arguments.get("atlas_token")
    
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "Atlas token required"}))]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://localhost:8003/api/v1/analytics/user/{user_id}/performance",
                params={"time_period": time_period},
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return [TextContent(type="text", text=json.dumps(response.json(), indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def handle_create_performance_review(arguments: Dict[str, Any]) -> List[TextContent]:
    """Create performance review via API"""
    token = arguments.get("atlas_token")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "Atlas token required"}))]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8003/api/v1/reviews",
                json={
                    "employee_id": arguments.get("employee_id"),
                    "review_period_start": arguments.get("review_period_start"),
                    "review_period_end": arguments.get("review_period_end"),
                    "overall_rating": arguments.get("overall_rating"),
                    "strengths": arguments.get("strengths"),
                    "areas_for_improvement": arguments.get("areas_for_improvement")
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return [TextContent(type="text", text=json.dumps(response.json(), indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def handle_set_performance_goal(arguments: Dict[str, Any]) -> List[TextContent]:
    """Set performance goal via API"""
    token = arguments.get("atlas_token")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "Atlas token required"}))]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8003/api/v1/goals",
                json={
                    "title": arguments.get("title"),
                    "description": arguments.get("description"),
                    "goal_type": arguments.get("goal_type"),
                    "target_value": arguments.get("target_value"),
                    "start_date": arguments.get("start_date"),
                    "target_date": arguments.get("target_date")
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return [TextContent(type="text", text=json.dumps(response.json(), indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def handle_get_team_performance(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get team performance via API"""
    org_id = arguments.get("organization_id")
    token = arguments.get("atlas_token")
    
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "Atlas token required"}))]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://localhost:8003/api/v1/analytics/team/{org_id}/performance",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return [TextContent(type="text", text=json.dumps(response.json(), indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def handle_submit_peer_feedback(arguments: Dict[str, Any]) -> List[TextContent]:
    """Submit peer feedback via API"""
    token = arguments.get("atlas_token")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "Atlas token required"}))]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8003/api/v1/feedback",
                json={
                    "employee_id": arguments.get("employee_id"),
                    "project_id": arguments.get("project_id"),
                    "feedback_type": arguments.get("feedback_type"),
                    "rating": arguments.get("rating"),
                    "feedback_text": arguments.get("feedback_text"),
                    "is_anonymous": arguments.get("is_anonymous", False)
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return [TextContent(type="text", text=json.dumps(response.json(), indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def handle_assess_skills(arguments: Dict[str, Any]) -> List[TextContent]:
    """Assess skills via API"""
    token = arguments.get("atlas_token")
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "Atlas token required"}))]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8003/api/v1/skills/assess",
                json={
                    "skill_name": arguments.get("skill_name"),
                    "skill_category": arguments.get("skill_category"),
                    "proficiency_level": arguments.get("proficiency_level"),
                    "proficiency_score": arguments.get("proficiency_score"),
                    "assessment_method": arguments.get("assessment_method")
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return [TextContent(type="text", text=json.dumps(response.json(), indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def handle_identify_skill_gaps(arguments: Dict[str, Any]) -> List[TextContent]:
    """Identify skill gaps via API"""
    user_id = arguments.get("user_id")
    project_id = arguments.get("project_id")
    token = arguments.get("atlas_token")
    
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "Atlas token required"}))]
    
    try:
        async with httpx.AsyncClient() as client:
            url = f"http://localhost:8003/api/v1/skills/gaps/{user_id}"
            params = {"project_id": project_id} if project_id else {}
            response = await client.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return [TextContent(type="text", text=json.dumps(response.json(), indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def handle_track_goal_progress(arguments: Dict[str, Any]) -> List[TextContent]:
    """Track goal progress via API"""
    goal_id = arguments.get("goal_id")
    token = arguments.get("atlas_token")
    
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "Atlas token required"}))]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"http://localhost:8003/api/v1/goals/{goal_id}/progress",
                json={
                    "current_value": arguments.get("current_value"),
                    "status": arguments.get("status")
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return [TextContent(type="text", text=json.dumps(response.json(), indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def handle_generate_performance_report_api(arguments: Dict[str, Any]) -> List[TextContent]:
    """Generate performance report via API"""
    user_id = arguments.get("user_id")
    report_type = arguments.get("report_type", "quarterly")
    token = arguments.get("atlas_token")
    
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "Atlas token required"}))]
    
    try:
        async with httpx.AsyncClient() as client:
            if report_type == "quarterly":
                params = {}
                if arguments.get("quarter"):
                    params["quarter"] = arguments.get("quarter")
                if arguments.get("year"):
                    params["year"] = arguments.get("year")
                
                response = await client.get(
                    f"http://localhost:8003/api/v1/reports/user/{user_id}/quarterly",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"}
                )
            else:
                # For monthly/yearly, use analytics endpoint
                response = await client.get(
                    f"http://localhost:8003/api/v1/analytics/user/{user_id}/performance",
                    params={"time_period": report_type},
                    headers={"Authorization": f"Bearer {token}"}
                )
            
            response.raise_for_status()
            return [TextContent(type="text", text=json.dumps(response.json(), indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def handle_predict_performance_trend(arguments: Dict[str, Any]) -> List[TextContent]:
    """Predict performance trend via API"""
    user_id = arguments.get("user_id")
    prediction_months = arguments.get("prediction_months", 3)
    token = arguments.get("atlas_token")
    
    if not token:
        return [TextContent(type="text", text=json.dumps({"error": "Atlas token required"}))]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8003/api/v1/analytics/predict",
                json={
                    "user_id": user_id,
                    "prediction_months": prediction_months
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return [TextContent(type="text", text=json.dumps(response.json(), indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

async def main():
    """Main entry point for the MCP server"""
    # Create stdio transport
    transport = stdio_server()
    # Run the server with the transport
    await server.run(transport, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())

