"""
Dashboard router - unified dashboard endpoint
"""
from fastapi import APIRouter, Depends, HTTPException

from auth.jwt_handler import get_current_user
from services.atlas_client import atlas_client
from services.workpulse_client import workpulse_client
from services.epr_client import epr_client
from services.labs_client import labs_client

router = APIRouter(prefix="/api/v1", tags=["Dashboard"])


@router.get("/dashboard")
async def get_dashboard(current_user = Depends(get_current_user)):
    """Get unified dashboard"""
    
    user_id = current_user.get("sub")
    org_id = current_user.get("organization_id")
    role = current_user.get("role")
    
    if not org_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")
    
    try:
        # Gather data from all services in parallel
        projects = await atlas_client.get_projects(org_id=org_id)
        tasks = await atlas_client.get_user_tasks(user_id=user_id)
        activities = await workpulse_client.get_activities(user_id=user_id)
        reviews = await epr_client.get_reviews(user_id=user_id)
        goals = await epr_client.get_goals(user_id=user_id)
        labs = await labs_client.get_labs(org_id=org_id)
        
        # Get team data if manager/admin
        team_stats = None
        if role in ["admin", "manager"]:
            team_stats = await workpulse_client.get_team_activities(org_id=org_id)
        
        return {
            "user": {
                "id": user_id,
                "name": current_user.get("name"),
                "email": current_user.get("email"),
                "role": role
            },
            "organization": {
                "id": org_id
            },
            "projects": projects,
            "tasks": tasks,
            "activities": activities,
            "performance": {
                "reviews": reviews,
                "goals": goals
            },
            "labs": labs,
            "team_stats": team_stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
