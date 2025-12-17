from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .routers import labs, researchers, users, collaboration
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="History of Lab Records Service", version="1.0.0")

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
        "service": "labs",
        "timestamp": datetime.utcnow().isoformat()
    }

# Include routers with /api/v1 prefix
app.include_router(users.router, prefix="/api/v1")
app.include_router(labs.router, prefix="/api/v1")
app.include_router(researchers.router, prefix="/api/v1")
app.include_router(collaboration.router, prefix="/api/v1")

@app.get("/")
def root():
    return {
        "message": "History of Lab Records Service",
        "version": "1.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)
