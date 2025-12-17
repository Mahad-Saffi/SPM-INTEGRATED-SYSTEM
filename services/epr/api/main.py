"""
ScoreSquad Performance API - Main FastAPI Application
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from api.database import init_db
from api.routes import reviews, goals, feedback, skills, analytics, reports, employees, tasks, projects, performances, notifications
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Employee Performance Report Service",
    description="Performance tracking and assessment API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Service authentication
SERVICE_SECRET = os.getenv("SERVICE_SECRET", "shared-secret-token")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service token validation middleware
@app.middleware("http")
async def validate_service_token(request: Request, call_next):
    # Skip validation for health endpoint
    if request.url.path == "/health":
        return await call_next(request)
    
    # Validate service token
    token = request.headers.get("X-Service-Token")
    if token != SERVICE_SECRET:
        raise HTTPException(status_code=403, detail="Invalid service token")
    
    return await call_next(request)

# Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "epr",
        "timestamp": datetime.utcnow().isoformat()
    }

# Initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()

# Include routers with /api/v1 prefix
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(goals.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")
app.include_router(skills.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(employees.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(performances.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Employee Performance Report Service",
        "version": "1.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)


