from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.config.database import SessionLocal, engine
from app.api.v1 import ai as ai_router
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Atlas AI Scrum Master Service", version="1.0.0")

# Service authentication
SERVICE_SECRET = os.getenv("SERVICE_SECRET", "shared-secret-token")

# Service token validation middleware
@app.middleware("http")
async def validate_service_token(request: Request, call_next):
    # Skip validation for health and root endpoints
    if request.url.path in ["/health", "/"]:
        return await call_next(request)
    
    # Validate service token for internal API calls
    token = request.headers.get("X-Service-Token")
    if token and token == SERVICE_SECRET:
        # Valid service token - bypass other auth
        request.state.is_service_call = True
    
    return await call_next(request)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.models import Base
from app.config.database import engine
from app.core.startup import startup_checks
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@app.on_event("startup")
async def startup():
    """Run startup checks and initialize database"""
    try:
        # Run comprehensive startup checks
        await startup_checks()
    except Exception as e:
        logging.error(f"❌ Startup failed: {e}")
        raise

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    from sqlalchemy import text
    
    health_status = {
        "status": "healthy",
        "service": "atlas-backend",
        "database": "unknown",
        "checks": {}
    }
    
    # Check database connection
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
            health_status["database"] = "connected"
            health_status["checks"]["database"] = "✅ OK"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"] = "disconnected"
        health_status["checks"]["database"] = f"❌ Error: {str(e)}"
    
    # Check if tables exist
    try:
        from sqlalchemy import inspect
        async with engine.begin() as conn:
            def get_tables(connection):
                inspector = inspect(connection)
                return inspector.get_table_names()
            
            tables = await conn.run_sync(get_tables)
            health_status["checks"]["tables"] = f"✅ {len(tables)} tables"
            health_status["tables_count"] = len(tables)
    except Exception as e:
        health_status["checks"]["tables"] = f"❌ Error: {str(e)}"
    
    return health_status

from app.api.v1 import projects as projects_router
from app.api.v1 import notifications as notifications_router
from app.api.v1 import chat as chat_router
from app.api.v1 import auth as auth_router
from app.api.v1 import issues as issues_router
from app.api.v1 import organizations as organizations_router
from app.api.v1 import ai_automation as ai_automation_router
from app.api.v1 import internal as internal_router

app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(ai_router.router, prefix="/api/v1/ai", tags=["ai"])
app.include_router(projects_router.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(notifications_router.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(chat_router.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(issues_router.router, prefix="/api/v1/issues", tags=["issues"])
app.include_router(organizations_router.router, prefix="/api/v1/organizations", tags=["organizations"])
app.include_router(ai_automation_router.router, prefix="/api/v1/ai-automation", tags=["ai-automation"])
app.include_router(internal_router.router, prefix="/api/v1/internal", tags=["internal"])

@app.get("/")
async def read_root():
    return {
        "message": "Atlas AI Scrum Master Service",
        "version": "1.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

from app.core.security import get_current_user

@app.get("/users/me")
async def get_user(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user"""
    return current_user
