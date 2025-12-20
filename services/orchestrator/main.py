"""
Main FastAPI application - Project Management Orchestrator
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import httpx
import subprocess
import sys
import os
import time
import signal
from contextlib import asynccontextmanager

from database import init_db, get_db
from config import settings
from auth.jwt_handler import get_current_user
from routers import auth, health, projects, monitoring, performance, research
from aggregators.dashboard import dashboard_aggregator

# List of service URLs to check
SERVICE_URLS = [
    settings.atlas_service_url,
    settings.workpulse_service_url,
    settings.epr_service_url,
    settings.labs_service_url
]

# Service configurations for subprocess management
SERVICES = {
    "atlas": {
        "path": os.path.abspath(os.path.join(os.path.dirname(__file__), "../atlas/main.py")),
        "port": 8000,
        "process": None,
        "module": "main",
        "cwd": None  # Use the directory containing the path
    },
    "workpulse": {
        "path": os.path.abspath(os.path.join(os.path.dirname(__file__), "../workpulse/app/main.py")),
        "port": 8001,
        "process": None,
        "module": "app.main",
        "cwd": os.path.abspath(os.path.join(os.path.dirname(__file__), "../workpulse"))
    },
    "epr": {
        "path": os.path.abspath(os.path.join(os.path.dirname(__file__), "../epr/api/main.py")),
        "port": 8003,
        "process": None,
        "module": "api.main",
        "cwd": os.path.abspath(os.path.join(os.path.dirname(__file__), "../epr"))
    },
    "labs": {
        "path": os.path.abspath(os.path.join(os.path.dirname(__file__), "../labs/app/main.py")),
        "port": 8004,
        "process": None,
        "module": "app.main",
        "cwd": os.path.abspath(os.path.join(os.path.dirname(__file__), "../labs"))
    }
}

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    # Startup
    print("🚀 Starting Orchestrator...")
    print(f"📊 Database: {settings.database_url}")
    print(f"🔐 JWT Algorithm: {settings.jwt_algorithm}")
    print(f"🌐 Atlas Service: {settings.atlas_service_url}")
    print(f"📊 WorkPulse Service: {settings.workpulse_service_url}")
    print(f"📈 EPR Service: {settings.epr_service_url}")
    print(f"🧪 Labs Service: {settings.labs_service_url}")
    
    try:
        # Start all microservices first
        start_all_services()
        
        # Wait longer for services to start and initialize
        print("⏳ Waiting for services to initialize...")
        await asyncio.sleep(15)
        
        # Try to wait for them to be ready, but don't fail if they're not
        try:
            await wait_for_services_and_db()
            print("✅ All services and database are ready")
        except Exception as e:
            print(f"⚠️ Service health check warning: {e}")
            print("⏳ Services may still be initializing, continuing anyway...")
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        raise e
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Orchestrator...")
    stop_all_services()

# Create FastAPI app
app = FastAPI(
    title="Project Management Orchestrator",
    description="Unified API gateway for all microservices",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service management functions
def start_service(name: str, service_config: dict) -> bool:
    """Start a microservice subprocess"""
    try:
        path = service_config["path"]
        port = service_config["port"]
        module = service_config.get("module", "main")
        cwd = service_config.get("cwd") or os.path.dirname(path)
        
        if not os.path.exists(path):
            print(f"❌ Service file not found: {path}")
            return False
        
        print(f"🚀 Starting {name} service on port {port}...")
        
        # Create a log file for the service
        log_file = open(f"{name}_service.log", "w")
        
        # Start the service with uvicorn from the specified directory
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", f"{module}:app", "--host", "127.0.0.1", "--port", str(port)],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=cwd
        )
        
        service_config["process"] = process
        service_config["log_file"] = log_file
        print(f"✅ {name} service started (PID: {process.pid})")
        return True
    except Exception as e:
        print(f"❌ Failed to start {name} service: {e}")
        return False

def stop_all_services():
    """Stop all running microservices"""
    print("🛑 Stopping all services...")
    for name, config in SERVICES.items():
        if config["process"] and config["process"].poll() is None:
            try:
                config["process"].terminate()
                config["process"].wait(timeout=5)
                print(f"✅ {name} service stopped")
            except subprocess.TimeoutExpired:
                config["process"].kill()
                print(f"⚠️ {name} service force killed")
            except Exception as e:
                print(f"❌ Error stopping {name}: {e}")
        
        # Close log file if it exists
        if "log_file" in config and config["log_file"]:
            try:
                config["log_file"].close()
            except:
                pass

def start_all_services():
    """Start all microservices"""
    print("🚀 Starting all microservices...")
    for name, config in SERVICES.items():
        start_service(name, config)
        time.sleep(2)  # Small delay between service startups

# Helper functions for startup checks
async def check_service(url: str, timeout: int = 10):
    """Ping a service to check if it is up"""
    try:
        async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
            r = await client.get(url, follow_redirects=True)
            if r.status_code == 200:
                print(f"✅ Service up: {url}")
                return True
            else:
                print(f"⚠️ Service returned {r.status_code}: {url}")
                return False
    except asyncio.TimeoutError:
        print(f"⏱️ Service timeout: {url}")
        return False
    except Exception as e:
        print(f"❌ Service down: {url} - {type(e).__name__}: {str(e)[:100]}")
        return False

async def wait_for_services_and_db(retries: int = 15, delay: int = 4):
    """Wait until all services and the database are ready"""
    # 1. Check database
    db_ready = False
    for attempt in range(1, retries + 1):
        try:
            await init_db()
            db_ready = True
            print("✅ Database connection successful")
            break
        except Exception as e:
            print(f"⚠️ Attempt {attempt}: Database not ready - {e}")
            await asyncio.sleep(delay)
    if not db_ready:
        raise Exception("❌ Database connection failed after retries")

    # 2. Check microservices
    for url in SERVICE_URLS:
        service_ready = False
        for attempt in range(1, retries + 1):
            if await check_service(url):
                service_ready = True
                break
            print(f"⏳ Waiting for service {url} (Attempt {attempt}/{retries})...")
            await asyncio.sleep(delay)
        if not service_ready:
            raise Exception(f"❌ Service {url} not available after retries")

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
        reload=False,
        log_level="info"
    )
