"""
User Synchronization Service
Ensures users created in orchestrator are synced to all microservices
"""
import httpx
from typing import Dict, Any
from config import settings
import logging

logger = logging.getLogger(__name__)


class UserSyncService:
    """Synchronize user creation across all microservices"""
    
    def __init__(self):
        self.timeout = 10.0
        self.service_token = settings.service_secret
        
    async def sync_user_to_all_services(self, user_data: Dict[str, Any]) -> Dict[str, bool]:
        """
        Sync user to all microservices
        Returns dict with service names and success status
        """
        results = {}
        
        # Sync to each service
        results['atlas'] = await self._sync_to_atlas(user_data)
        results['workpulse'] = await self._sync_to_workpulse(user_data)
        results['epr'] = await self._sync_to_epr(user_data)
        results['labs'] = await self._sync_to_labs(user_data)
        
        return results
    
    async def _sync_to_atlas(self, user_data: Dict[str, Any]) -> bool:
        """Sync user to Atlas service"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{settings.atlas_service_url}/api/v1/internal/users/sync",
                    json={
                        "orchestrator_user_id": user_data["id"],
                        "email": user_data["email"],
                        "name": user_data["name"],
                        "organization_id": user_data.get("organization_id")
                    },
                    headers={"X-Service-Token": self.service_token}
                )
                return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Failed to sync user to Atlas: {e}")
            return False
    
    async def _sync_to_workpulse(self, user_data: Dict[str, Any]) -> bool:
        """Sync user to WorkPulse service"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{settings.workpulse_service_url}/api/v1/users/sync",
                    json={
                        "orchestrator_user_id": user_data["id"],
                        "email": user_data["email"],
                        "name": user_data["name"]
                    },
                    headers={"X-Service-Token": self.service_token}
                )
                return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Failed to sync user to WorkPulse: {e}")
            return False
    
    async def _sync_to_epr(self, user_data: Dict[str, Any]) -> bool:
        """Sync user to EPR service"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{settings.epr_service_url}/api/v1/employees",
                    json={
                        "employee_id": user_data["id"],
                        "email": user_data["email"],
                        "name": user_data["name"],
                        "role": user_data.get("role", "member")
                    },
                    headers={"X-Service-Token": self.service_token}
                )
                return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Failed to sync user to EPR: {e}")
            return False
    
    async def _sync_to_labs(self, user_data: Dict[str, Any]) -> bool:
        """Sync user to Labs service"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{settings.labs_service_url}/users/sync",
                    json={
                        "orchestrator_user_id": user_data["id"],
                        "email": user_data["email"],
                        "name": user_data["name"]
                    },
                    headers={"X-Service-Token": self.service_token}
                )
                return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Failed to sync user to Labs: {e}")
            return False


# Global instance
user_sync_service = UserSyncService()
