"""
Example usage of MCP automation tools
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.server import (
    handle_evaluate_all_employees,
    handle_detect_all_risks,
    handle_check_overdue_tasks,
    handle_automated_daily_check,
    handle_get_employee_stats
)


async def examples():
    """Run example automation tasks"""
    
    print("=" * 60)
    print("MCP Automation Examples")
    print("=" * 60)
    
    # Example 1: Evaluate all employees
    print("\n1. Evaluating all employees...")
    result = await handle_evaluate_all_employees({"save_results": True})
    print(result[0].text[:500] + "..." if len(result[0].text) > 500 else result[0].text)
    
    # Example 2: Detect risks
    print("\n2. Detecting all risks...")
    result = await handle_detect_all_risks({})
    print(result[0].text[:500] + "..." if len(result[0].text) > 500 else result[0].text)
    
    # Example 3: Check overdue tasks
    print("\n3. Checking overdue tasks...")
    result = await handle_check_overdue_tasks({"send_notifications": False})
    print(result[0].text[:500] + "..." if len(result[0].text) > 500 else result[0].text)
    
    # Example 4: Get employee stats (if employees exist)
    print("\n4. Getting employee statistics...")
    # This would need an actual employee_id
    # result = await handle_get_employee_stats({"employee_id": "1"})
    # print(result[0].text)
    print("(Skipped - requires employee_id)")
    
    # Example 5: Automated daily check
    print("\n5. Running automated daily check...")
    result = await handle_automated_daily_check({
        "evaluate_performance": True,
        "detect_risks": True,
        "check_overdue": True
    })
    print(result[0].text[:500] + "..." if len(result[0].text) > 500 else result[0].text)
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(examples())



