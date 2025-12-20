from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from .database import Base, engine
from .routers import activity, productivity, users
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = FastAPI(title="WorkPulse Activity Monitoring Service", version="1.0.0")

# Service authentication
SERVICE_SECRET = os.getenv("SERVICE_SECRET", "shared-secret-token")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Service token validation middleware - DISABLED for development
# Enable in production by uncommenting below
# @app.middleware("http")
# async def validate_service_token(request: Request, call_next):
#     # Skip validation for health endpoint
#     if request.url.path == "/health":
#         return await call_next(request)
#     
#     # Validate service token
#     token = request.headers.get("X-Service-Token")
#     if token != SERVICE_SECRET:
#         raise HTTPException(status_code=403, detail="Invalid service token")
#     
#     return await call_next(request)

# Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "workpulse",
        "timestamp": datetime.utcnow().isoformat()
    }

# Include routers with /api/v1 prefix
app.include_router(activity.router, prefix="/api/v1")
app.include_router(productivity.router, prefix="/api/v1")
app.include_router(users.router)

@app.get("/")
def root():
    return {
        "message": "WorkPulse Activity Monitoring Service",
        "version": "1.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
