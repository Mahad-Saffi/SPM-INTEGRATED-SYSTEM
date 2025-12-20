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
        return await self.get(f"/api/v1/activity/user/{user_id}", token, {"limit": days * 20})
    
    async def get_today_activity(self, user_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        """Get today's activity"""
        return await self.get(f"/api/v1/activity/user/{user_id}/today", token)
    
    async def get_activities(self, user_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get user activities"""
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        result = await self.get(f"/api/v1/activity/user/{user_id}", token, params)
        return result if isinstance(result, list) else []
    
    async def get_team_activities(self, org_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get team activities"""
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        result = await self.get(f"/api/v1/activity/team/{org_id}", token, params)
        return result if isinstance(result, list) else []
    
    async def log_activity(self, activity_data: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        """Log user activity"""
        return await self.post("/api/v1/activity/", activity_data, token)
    
    async def get_team_activity(self, org_id: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get team activity summary"""
        result = await self.get(f"/api/v1/activity/team/{org_id}", token)
        return result if isinstance(result, list) else []
    
    async def get_productivity_stats(self, user_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        """Get productivity statistics"""
        return await self.get(f"/api/v1/productivity/user/{user_id}/stats", token)


# Global instance
workpulse_client = WorkPulseClient()
