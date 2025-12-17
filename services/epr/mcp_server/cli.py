"""
CLI tool for running MCP automation tasks directly
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.server import (
    handle_evaluate_all_employees,
    handle_detect_all_risks,
    handle_check_overdue_tasks,
    handle_check_overdue_goals,
    handle_assess_workload,
    handle_automated_daily_check,
    handle_send_notification,
    handle_get_employee_stats,
    handle_generate_performance_report,
    handle_generate_project_report,
    handle_export_data,
    handle_record_attendance
)


async def run_tool(tool_name: str, args: dict):
    """Run a specific tool"""
    handlers = {
        "evaluate_all_employees": handle_evaluate_all_employees,
        "detect_all_risks": handle_detect_all_risks,
        "check_overdue_tasks": handle_check_overdue_tasks,
        "check_overdue_goals": handle_check_overdue_goals,
        "assess_workload": handle_assess_workload,
        "automated_daily_check": handle_automated_daily_check,
        "send_notification": handle_send_notification,
        "get_employee_stats": handle_get_employee_stats,
        "generate_performance_report": handle_generate_performance_report,
        "generate_project_report": handle_generate_project_report,
        "export_data": handle_export_data,
        "record_attendance": handle_record_attendance
    }
    
    if tool_name not in handlers:
        print(f"Unknown tool: {tool_name}")
        print(f"Available tools: {', '.join(handlers.keys())}")
        return
    
    try:
        result = await handlers[tool_name](args)
        if result:
            print(result[0].text)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="MCP Automation CLI for Employee Performance System")
    parser.add_argument("tool", help="Tool name to execute")
    parser.add_argument("--args", help="JSON arguments for the tool", default="{}")
    
    args = parser.parse_args()
    
    try:
        tool_args = json.loads(args.args)
    except json.JSONDecodeError:
        print("Error: Invalid JSON in --args", file=sys.stderr)
        sys.exit(1)
    
    asyncio.run(run_tool(args.tool, tool_args))


if __name__ == "__main__":
    main()



