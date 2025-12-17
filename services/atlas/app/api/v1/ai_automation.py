from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException
from app.services.ai_automation_service import automation_service
from app.core.security import get_current_user
import jwt
from starlette.config import Config
import logging

router = APIRouter()
config = Config(".env")
logger = logging.getLogger(__name__)

@router.websocket("/ws/automation")
async def automation_websocket(websocket: WebSocket, token: str = Query(...)):
    """WebSocket endpoint for AI automation"""
    try:
        # Verify JWT token
        try:
            payload = jwt.decode(token, config('JWT_SECRET_KEY'), algorithms=["HS256"])
            user_id = payload['id']
            logger.info(f"User {user_id} connected to AI automation")
        except jwt.ExpiredSignatureError:
            await websocket.close(code=1008, reason="Token expired")
            return
        except jwt.InvalidTokenError:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        await websocket.accept()
        
        try:
            # Wait for task from client
            data = await websocket.receive_json()
            task = data.get('task')
            
            if not task:
                await websocket.send_json({
                    "type": "error",
                    "message": "No task provided"
                })
                return
            
            logger.info(f"Starting automation for user {user_id}: {task}")
            
            # Start automation
            await automation_service.start_automation(task, websocket)
            
        except WebSocketDisconnect:
            logger.info(f"User {user_id} disconnected from AI automation")
            automation_service.stop()
        except Exception as e:
            logger.error(f"Automation error for user {user_id}: {e}")
            try:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
            except:
                pass
            automation_service.stop()
            
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass

@router.post("/stop")
async def stop_automation(current_user: dict = Depends(get_current_user)):
    """Stop current automation"""
    try:
        automation_service.stop()
        return {"message": "Automation stopped successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_status(current_user: dict = Depends(get_current_user)):
    """Get current automation status"""
    return {
        "is_running": automation_service.is_running,
        "current_task": automation_service.current_task
    }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-automation",
        "selenium_available": True
    }
