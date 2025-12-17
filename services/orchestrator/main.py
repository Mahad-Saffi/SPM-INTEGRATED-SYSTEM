"""
Main FastAPI application - Project Management Orchestrator
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio

from database import init_db, get_db
from config import settings
from auth.jwt_handler import get_current_user
from routers import auth, health, projects, monitoring, performance, research
from aggregators.dashboard import dashboard_aggregator

# Create FastAPI app
app = FastAPI(
    title="Project Management Orchestrator",
    description="Unified API gateway for all microservices",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("🚀 Starting Orchestrator...")
    print(f"📊 Database: {settings.database_url}")
    print(f"🔐 JWT Algorithm: {settings.jwt_algorithm}")
    print(f"🌐 Atlas Service: {settings.atlas_service_url}")
    print(f"📊 WorkPulse Service: {settings.workpulse_service_url}")
    print(f"📈 EPR Service: {settings.epr_service_url}")
    print(f"🧪 Labs Service: {settings.labs_service_url}")
    
    try:
        await init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Shutting down Orchestrator...")

# Include routers
app.include_router(auth.router)
app.include_router(health.router)
app.include_router(projects.router)
app.include_router(monitoring.router)
app.include_router(performance.router)
app.include_router(research.router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Project Management Orchestrator",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.environment,
        "endpoints": {
            "docs": "/docs",
            "health": "/api/v1/health",
            "services": "/api/v1/services",
            "auth": "/api/v1/auth",
            "projects": "/api/v1/projects",
            "monitoring": "/api/v1/monitoring",
            "performance": "/api/v1/performance",
            "research": "/api/v1/research",
            "dashboard": "/api/v1/dashboard"
        },
        "services": {
            "atlas": settings.atlas_service_url,
            "workpulse": settings.workpulse_service_url,
            "epr": settings.epr_service_url,
            "labs": settings.labs_service_url
        }
    }

# Dashboard endpoint
@app.get("/api/v1/dashboard")
async def get_dashboard(current_user = Depends(get_current_user)):
    """Get unified dashboard combining data from all services"""
    try:
        user_id = current_user["sub"]
        token = None  # In production, pass the user's token
        dashboard = await dashboard_aggregator.get_unified_dashboard(user_id, token)
        return dashboard
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed"
        }

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "path": str(request.url),
            "method": request.method
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9000,
        reload=settings.debug,
        log_level="info"
    )
