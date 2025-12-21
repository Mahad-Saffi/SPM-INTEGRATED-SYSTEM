# SPM-INTEGRATED-SYSTEM

Integrated Project Management System with microservices architecture.

## Quick Start with Docker

### Prerequisites
- Docker & Docker Compose installed
- Port 5432 (PostgreSQL), 9000 (Orchestrator), 8000-8004 (Services) available

### Start the Project

```bash
docker-compose up -d
```

### What Happens

1. **PostgreSQL 15** starts and initializes 5 databases (project_management, atlas, workpulse, epr, labs)
2. **Orchestrator** (Port 9000) - API gateway that coordinates all services
3. **Atlas** (Port 8000) - Project & task management
4. **WorkPulse** (Port 8001) - Activity & productivity monitoring
5. **EPR** (Port 8003) - Employee performance reports
6. **Labs** (Port 8004) - Research lab management

All services auto-start and initialize their schemas. Database credentials: `admin:admin123`

### Access

- **API Docs:** http://localhost:9000/docs
- **Health Check:** http://localhost:9000/health
- **API Base:** http://localhost:9000/api/v1

### Test Endpoints

```bash
python test_endpoints_simple.py
```

### Stop Services

```bash
docker-compose down
```

## Architecture

- **Centralized Auth:** JWT-based authentication via Orchestrator
- **Multi-tenancy:** Organization-based data isolation
- **Microservices:** 5 independent services with PostgreSQL databases
- **Hot Reload:** Development mode with auto-reload enabled
