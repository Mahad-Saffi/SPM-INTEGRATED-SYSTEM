"""
Employee Performance Report service client
"""
from .base_client import BaseServiceClient
from config import settings
from typing import Optional, Dict, Any, List


class EPRClient(BaseServiceClient):
    """Client for Employee Performance Report service"""
    
    def __init__(self):
        super().__init__(settings.epr_service_url, "epr")
    
    async def get_performance_score(self, user_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        """Get user's performance score"""
        return await self.get(f"/api/v1/analytics/user/{user_id}/performance", token)
    
    async def get_user_goals(self, user_id: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get user's goals"""
        result = await self.get(f"/api/v1/goals/user/{user_id}", token)
        return result if isinstance(result, list) else []
    
    async def create_goal(self, goal_data: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        """Create a new goal"""
        return await self.post("/api/v1/goals", goal_data, token)
    
    async def get_reviews(self, user_id: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get performance reviews"""
        result = await self.get(f"/api/v1/reviews/user/{user_id}", token)
        return result if isinstance(result, list) else []
    
    async def get_feedback(self, user_id: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get peer feedback"""
        result = await self.get(f"/api/v1/feedback/user/{user_id}", token)
        return result if isinstance(result, list) else []
    
    async def get_skills(self, user_id: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get user skills"""
        result = await self.get(f"/api/v1/skills/user/{user_id}", token)
        return result if isinstance(result, list) else []
    
    async def get_team_performance(self, org_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        """Get team performance metrics"""
        return await self.get(f"/api/v1/analytics/team/{org_id}/performance", token)


# Global instance
epr_client = EPRClient()
