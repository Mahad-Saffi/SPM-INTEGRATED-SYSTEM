"""
History of Lab Records service client
"""
from .base_client import BaseServiceClient
from config import settings
from typing import Optional, Dict, Any, List


class LabsClient(BaseServiceClient):
    """Client for History of Lab Records service"""
    
    def __init__(self):
        super().__init__(settings.labs_service_url, "labs")
    
    async def get_labs(self, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all labs"""
        result = await self.get("/labs", token)
        return result if isinstance(result, list) else []
    
    async def get_lab(self, lab_id: int, token: Optional[str] = None) -> Dict[str, Any]:
        """Get a specific lab"""
        return await self.get(f"/labs/{lab_id}", token)
    
    async def create_lab(self, lab_data: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        """Create a new lab"""
        return await self.post("/labs", lab_data, token)
    
    async def get_researchers(self, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all researchers"""
        result = await self.get("/researchers", token)
        return result if isinstance(result, list) else []
    
    async def get_lab_researchers(self, lab_id: int, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get researchers for a lab"""
        result = await self.get(f"/researchers/by-lab/{lab_id}", token)
        return result if isinstance(result, list) else []
    
    async def create_researcher(self, researcher_data: Dict[str, Any], token: Optional[str] = None) -> Dict[str, Any]:
        """Create a new researcher"""
        return await self.post("/researchers", researcher_data, token)
    
    async def get_collaborations(self, token: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get collaboration suggestions"""
        result = await self.get("/collaboration", token)
        return result if isinstance(result, list) else []
    
    async def generate_collaboration_email(self, lab_pair: str, token: Optional[str] = None) -> Dict[str, Any]:
        """Generate collaboration email"""
        return await self.post("/collaboration/generate-email", {"lab_pair": lab_pair}, token)


# Global instance
labs_client = LabsClient()
