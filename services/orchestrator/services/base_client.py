"""
Base HTTP client for service communication
"""
import httpx
from typing import Optional, Dict, Any
from config import settings


class BaseServiceClient:
    """Base class for service clients"""
    
    def __init__(self, base_url: str, service_name: str):
        self.base_url = base_url.rstrip('/')  # Remove trailing slash
        self.service_name = service_name
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
        """Check service health"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_url}/health",
                    headers=self._get_headers()
                )
                if response.status_code == 200:
                    return "healthy"
                return "unhealthy"
        except Exception as e:
            print(f"Health check failed for {self.service_name}: {str(e)}")
            return "unreachable"
    
    async def get(self, endpoint: str, token: Optional[str] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request to service"""
        url = f"{self.base_url}{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers=self._get_headers(token),
                    params=params
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"error": str(e), "service": self.service_name, "endpoint": endpoint}

    async def post(self, endpoint: str, data: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        """Make POST request to service"""
        url = f"{self.base_url}{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=data,
                    headers=self._get_headers(token)
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {
                "error": str(e), 
                "service": self.service_name, 
                "endpoint": endpoint,
                "attempted_url": url
            }
    
    async def put(self, endpoint: str, data: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        """Make PUT request to service"""
        url = f"{self.base_url}{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(
                    url,
                    json=data,
                    headers=self._get_headers(token)
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"error": str(e), "service": self.service_name, "endpoint": endpoint}
    
    async def delete(self, endpoint: str, token: Optional[str] = None) -> Dict[str, Any]:
        """Make DELETE request to service"""
        url = f"{self.base_url}{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    url,
                    headers=self._get_headers(token)
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"error": str(e), "service": self.service_name, "endpoint": endpoint}
