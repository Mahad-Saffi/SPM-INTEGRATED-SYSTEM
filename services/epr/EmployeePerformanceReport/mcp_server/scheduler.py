"""
Scheduler for automated daily tasks
Can be run as a cron job or scheduled task
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.server import handle_automated_daily_check


async def run_daily_checks():
    """Run automated daily checks"""
    print(f"[{datetime.now()}] Starting automated daily checks...")
    
    try:
        result = await handle_automated_daily_check({
            "evaluate_performance": True,
            "detect_risks": True,
            "check_overdue": True
        })
        
        if result:
            print(result[0].text)
            print(f"[{datetime.now()}] Daily checks completed successfully")
        else:
            print(f"[{datetime.now()}] Daily checks completed with no results")
            
    except Exception as e:
        print(f"[{datetime.now()}] Error during daily checks: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_daily_checks())



