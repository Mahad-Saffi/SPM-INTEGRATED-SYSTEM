"""
Health check router - monitor status of all services
"""
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime

from database import get_db, ServiceHealth
from services.atlas_client import atlas_client
from services.workpulse_client import workpulse_client
from services.epr_client import epr_client
from services.labs_client import labs_client

router = APIRouter(prefix="/api/v1", tags=["Health"])

# Service mapping
SERVICES = {
    "atlas": atlas_client,
    "workpulse": workpulse_client,
    "epr": epr_client,
    "labs": labs_client
}


@router.get("/health")
async def health_check():
    """Check health of orchestrator and all services"""
    
    health_status = {
        "orchestrator": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    for service_name, client in SERVICES.items():
        status = await client.health_check()
        health_status["services"][service_name] = {
            "status": status,
            "url": client.base_url
        }
    
    return health_status


@router.get("/services")
async def list_services():
    """List all registered services"""
    
    services = []
    for service_name, client in SERVICES.items():
        services.append({
            "name": service_name,
            "url": client.base_url,
            "status": await client.health_check()
        })
    
    return {
        "services": services,
        "orchestrator": "http://localhost:9000"
    }
