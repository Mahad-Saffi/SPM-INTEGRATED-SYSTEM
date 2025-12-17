"""
WorkPulse service client
"""
from .base_client import BaseServiceClient
from config import settings
from typing import Optional, Dict, Any, List


class WorkPulseClient(BaseServiceClient):
    """Client for WorkPulse monitoring service"""
    
    def __init__(self):
        super().__init__(settings.workpulse_service_url, "workpulse")
    
    async def get_user_activity(self, user_id: str, days: int = 7, token: Optional[str] = None) -> Dict[str, Any]:
        """Get user activity data"""
        return await self.get(f"/api/v1/activity/{user_id}", token, {"days": days})
    
    async def get_today_activity(self, user_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        """Get today's activity"""
        return await self.get(f"/api/v1/activity/{user_id}/today", token)
    
    async def log_activity(self, activity_data: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        """Log user activity"""
        return await self.post("/api/v1/activity/log", activity_data, token)
    
    async def get_team_activity(self, org_id: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get team activity summary"""
        result = await self.get(f"/api/v1/activity/team/{org_id}", token)
        return result if isinstance(result, list) else []
    
    async def get_productivity_stats(self, user_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        """Get productivity statistics"""
        return await self.get(f"/api/v1/stats/{user_id}/productivity", token)


# Global instance
workpulse_client = WorkPulseClient()
