#!/usr/bin/env python3
"""
Standalone automation script for Employee Performance System
Can be used without MCP server for simple automation tasks
"""
import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from components.managers.data_manager import DataManager
from components.agents.performance_agent import EnhancedPerformanceAgent
from components.agents.notification_agent import NotificationAgent
from components.agents.risk_agent import RiskDetectionAgent
from components.agents.reporting_agent import ReportingAgent
from components.agents.task_agent import TaskAgent
from components.agents.goal_agent import GoalAgent
from components.agents.workload_agent import WorkloadAgent


def evaluate_all_employees(save=True):
    """Evaluate all employees"""
    data_manager = DataManager()
    performance_agent = EnhancedPerformanceAgent(data_manager)
    employees = data_manager.load_data("employees") or []
    
    print(f"Evaluating {len(employees)} employees...")
    results = []
    
    for employee in employees:
        employee_id = employee.get("id")
        if employee_id:
            try:
                evaluation = performance_agent.evaluate_employee(employee_id, save=save)
                results.append({
                    "employee_id": employee_id,
                    "employee_name": employee.get("name"),
                    "performance_score": evaluation.get("performance_score", 0),
                    "completion_rate": evaluation.get("completion_rate", 0),
                    "on_time_rate": evaluation.get("on_time_rate", 0),
                    "rank": evaluation.get("rank", "N/A")
                })
                print(f"✓ Evaluated {employee.get('name')} - Score: {evaluation.get('performance_score', 0):.1f}")
            except Exception as e:
                print(f"✗ Error evaluating {employee.get('name')}: {str(e)}")
    
    print(f"\nCompleted: {len(results)}/{len(employees)} employees evaluated")
    return results


def detect_risks():
    """Detect all risks"""
    data_manager = DataManager()
    performance_agent = EnhancedPerformanceAgent(data_manager)
    reporting_agent = ReportingAgent(data_manager)
    risk_agent = RiskDetectionAgent(data_manager, performance_agent, reporting_agent)
    
    print("Detecting risks...")
    risks = risk_agent.detect_all_risks()
    
    print(f"Found {len(risks)} risks:")
    for risk in risks:
        print(f"  - [{risk.get('severity', 'unknown').upper()}] {risk.get('type', 'Unknown')}: {risk.get('description', 'N/A')}")
    
    return risks


def check_overdue_tasks(send_notifications=True):
    """Check for overdue tasks"""
    data_manager = DataManager()
    notification_agent = NotificationAgent(data_manager)
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
    
    print(f"Found {len(overdue_tasks)} overdue tasks")
    for task in overdue_tasks:
        print(f"  - {task.get('title')} (Due: {task.get('due_date', 'N/A')})")
    
    return overdue_tasks


def check_overdue_goals(send_notifications=True):
    """Check for overdue goals"""
    data_manager = DataManager()
    notification_agent = NotificationAgent(data_manager)
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
    
    print(f"Found {len(overdue_goals)} overdue goals")
    for goal in overdue_goals:
        print(f"  - {goal.get('title')} (Deadline: {goal.get('deadline', 'N/A')})")
    
    return overdue_goals


def daily_check():
    """Run all daily checks"""
    print("=" * 60)
    print(f"Daily Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    print("\n1. Evaluating all employees...")
    evaluate_all_employees(save=True)
    
    print("\n2. Detecting risks...")
    detect_risks()
    
    print("\n3. Checking overdue tasks...")
    check_overdue_tasks(send_notifications=True)
    
    print("\n4. Checking overdue goals...")
    check_overdue_goals(send_notifications=True)
    
    print("\n" + "=" * 60)
    print("Daily check completed!")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Employee Performance System Automation")
    parser.add_argument("action", choices=[
        "evaluate", "risks", "overdue-tasks", "overdue-goals", "daily"
    ], help="Action to perform")
    parser.add_argument("--no-save", action="store_true", help="Don't save evaluation results")
    parser.add_argument("--no-notify", action="store_true", help="Don't send notifications")
    
    args = parser.parse_args()
    
    if args.action == "evaluate":
        evaluate_all_employees(save=not args.no_save)
    elif args.action == "risks":
        detect_risks()
    elif args.action == "overdue-tasks":
        check_overdue_tasks(send_notifications=not args.no_notify)
    elif args.action == "overdue-goals":
        check_overdue_goals(send_notifications=not args.no_notify)
    elif args.action == "daily":
        daily_check()


if __name__ == "__main__":
    main()



