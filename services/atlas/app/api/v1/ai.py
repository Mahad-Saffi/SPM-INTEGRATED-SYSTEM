from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import get_current_user
from app.services.ai_service import ai_service

router = APIRouter()

class DiscoverMessage(BaseModel):
    message: str

@router.post("/discover")
async def discover(message: DiscoverMessage, current_user: dict = Depends(get_current_user)):
    response_text = await ai_service.get_discover_response(message.message, current_user)
    return {"sender": "ai", "text": response_text}
