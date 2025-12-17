"""
Research router - proxy requests to Labs service
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any

from auth.jwt_handler import get_current_user
from services.labs_client import labs_client

router = APIRouter(prefix="/api/v1/research", tags=["Research"])


@router.get("/labs")
async def get_labs(current_user = Depends(get_current_user)):
    """Get all labs"""
    return await labs_client.get_labs()


@router.get("/labs/{lab_id}")
async def get_lab(lab_id: int, current_user = Depends(get_current_user)):
    """Get a specific lab"""
    return await labs_client.get_lab(lab_id)


@router.post("/labs")
async def create_lab(lab_data: Dict[str, Any], current_user = Depends(get_current_user)):
    """Create a new lab"""
    return await labs_client.create_lab(lab_data)


@router.get("/researchers")
async def get_researchers(current_user = Depends(get_current_user)):
    """Get all researchers"""
    return await labs_client.get_researchers()


@router.get("/labs/{lab_id}/researchers")
async def get_lab_researchers(lab_id: int, current_user = Depends(get_current_user)):
    """Get researchers for a lab"""
    return await labs_client.get_lab_researchers(lab_id)


@router.post("/researchers")
async def create_researcher(researcher_data: Dict[str, Any], current_user = Depends(get_current_user)):
    """Create a new researcher"""
    return await labs_client.create_researcher(researcher_data)


@router.get("/collaborations")
async def get_collaborations(current_user = Depends(get_current_user)):
    """Get collaboration suggestions"""
    return await labs_client.get_collaborations()


@router.post("/collaborations/email")
async def generate_collaboration_email(lab_pair: str, current_user = Depends(get_current_user)):
    """Generate collaboration email"""
    return await labs_client.generate_collaboration_email(lab_pair)
