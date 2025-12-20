"""
History of Lab Records service client
"""
import httpx
from config import settings
from typing import Optional, Dict, Any, List


class LabsClient:
    """Client for History of Lab Records service"""
    
    def __init__(self):
        self.base_url = settings.labs_service_url.rstrip('/')
        self.service_name = "labs"
        self.service_token = settings.service_secret
    
    def _get_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """Get request headers"""
        headers = {
            "X-Service-Token": self.service_token,
            "X-Service-Name": "orchestrator",
            "Content-Type": "application/json"
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers
    
    async def health_check(self) -> str:
        """Check if the service is healthy"""
        url = f"{self.base_url}/health"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return "healthy"
                return "unhealthy"
        except Exception as e:
            return "unhealthy"
    
    async def get_labs(self, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all labs"""
        url = f"{self.base_url}/api/v1/labs/"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self._get_headers(token))
                response.raise_for_status()
                result = response.json()
                return result if isinstance(result, list) else []
        except Exception as e:
            return []
    
    async def get_lab(self, lab_id: int, token: Optional[str] = None) -> Dict[str, Any]:
        """Get a specific lab"""
        url = f"{self.base_url}/api/v1/labs/{lab_id}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self._get_headers(token))
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"error": str(e)}

    async def create_lab(self, lab_data: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        """Create a new lab"""
        url = f"{self.base_url}/api/v1/labs/"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=lab_data,
                    headers=self._get_headers(token)
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"error": str(e), "service": self.service_name, "attempted_url": url}
    
    async def get_researchers(self, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all researchers"""
        url = f"{self.base_url}/api/v1/researchers/"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self._get_headers(token))
                response.raise_for_status()
                result = response.json()
                return result if isinstance(result, list) else []
        except Exception as e:
            return []
    
    async def get_lab_researchers(self, lab_id: int, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get researchers for a lab"""
        url = f"{self.base_url}/api/v1/researchers/by-lab/{lab_id}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self._get_headers(token))
                response.raise_for_status()
                result = response.json()
                return result if isinstance(result, list) else []
        except Exception as e:
            return []
    
    async def create_researcher(self, researcher_data: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        """Create a new researcher"""
        url = f"{self.base_url}/api/v1/researchers/"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=researcher_data,
                    headers=self._get_headers(token)
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def get_collaborations(self, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get collaboration suggestions"""
        url = f"{self.base_url}/api/v1/collaboration/"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self._get_headers(token))
                response.raise_for_status()
                result = response.json()
                return result if isinstance(result, list) else []
        except Exception as e:
            return []
    
    async def generate_collaboration_email(self, lab_pair: str, token: Optional[str] = None) -> Dict[str, Any]:
        """Generate collaboration email"""
        url = f"{self.base_url}/api/v1/collaboration/generate-email"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json={"lab_pair": lab_pair},
                    headers=self._get_headers(token)
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"error": str(e)}


# Global instance
labs_client = LabsClient()
