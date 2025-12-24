# SPM-INTEGRATED-SYSTEM

Comprehensive Integrated Project Management System with microservices architecture. Manage projects, track performance, monitor activities, and collaborate on research across multiple organizations.

## Quick Start with Docker

### Prerequisites
- Docker & Docker Compose installed
- Ports available: 5432 (PostgreSQL), 9000 (Orchestrator), 8000-8004 (Services)

### Start the Project

```bash
docker-compose up -d
```

### What Happens

1. **PostgreSQL 15** initializes with 5 databases (project_management, atlas, workpulse, epr, labs)
2. **Orchestrator** (Port 9000) - Central API gateway & authentication
3. **Atlas** (Port 8000) - Project & task management
4. **WorkPulse** (Port 8001) - Activity & productivity monitoring
5. **EPR** (Port 8003) - Employee performance reports
6. **Labs** (Port 8004) - Research lab management

Database credentials: `admin:admin123`

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

---

## Core Features

### 1. Authentication & Authorization

**Endpoints:**
- `POST /auth/register` - User registration with auto-organization creation
- `POST /auth/login` - JWT token generation
- `GET /auth/me` - Current user info
- `POST /auth/organizations` - Create new organization
- `GET /auth/organizations` - List user organizations
- `POST /auth/invitations` - Send organization invitation
- `GET /auth/invitations` - Get pending invitations
- `POST /auth/invitations/{id}/accept` - Accept invitation
- `POST /auth/invitations/{id}/reject` - Reject invitation

**Features:**
- JWT-based authentication with 7-day expiration
- Role-based access control (admin, manager, member)
- Organization-based multi-tenancy
- User invitations with email-based acceptance
- Automatic organization creation on registration

---

### 2. Project Management (Atlas Service)

**Endpoints:**
- `GET /projects` - List organization projects
- `POST /projects` - Create project
- `GET /projects/{id}` - Get project details
- `PUT /projects/{id}` - Update project
- `GET /projects/{id}/tasks` - List project tasks
- `POST /projects/{id}/tasks` - Create task
- `GET /projects/{id}/tasks/{task_id}` - Get task details
- `PUT /projects/{id}/tasks/{task_id}` - Update task

**Features:**
- Project creation and management
- Task assignment and tracking
- Project status management (active, completed, archived)
- Task progress tracking with percentage
- Hierarchical project structure

---

### 3. Activity & Productivity Monitoring (WorkPulse Service)

**Endpoints:**
- `GET /monitoring/activity/{user_id}` - User activity history
- `GET /monitoring/activity/{user_id}/today` - Today's activity
- `GET /monitoring/team/{org_id}` - Team activity summary
- `GET /monitoring/stats/{user_id}/productivity` - Productivity statistics
- `POST /activities` - Log activity
- `GET /activities` - List user activities

**Features:**
- Real-time activity logging
- Productivity metrics and statistics
- Team activity aggregation
- Daily activity tracking
- Performance insights

---

### 4. Employee Performance Reports (EPR Service)

**Endpoints:**
- `GET /performance/users/{user_id}/reviews` - Performance reviews
- `POST /performance/users/{user_id}/reviews` - Create review
- `GET /performance/users/{user_id}/goals` - User goals
- `POST /performance/users/{user_id}/goals` - Create goal
- `GET /performance/users/{user_id}/feedback` - Peer feedback
- `POST /performance/users/{user_id}/feedback` - Give feedback
- `GET /performance/users/{user_id}/skills` - User skills

**Features:**
- Performance review management
- Goal setting and tracking
- Peer feedback system
- Skill assessment
- Team performance metrics

---

### 5. Research Lab Management (Labs Service)

**Endpoints:**
- `GET /research/labs` - List labs
- `POST /research/labs` - Create lab
- `GET /research/labs/{id}` - Lab details
- `GET /research/researchers` - List researchers
- `POST /research/researchers` - Add researcher
- `GET /research/labs/{id}/researchers` - Lab researchers
- `GET /research/collaborations` - Collaboration suggestions
- `POST /research/collaborations/accept/{lab1}/{lab2}` - Accept collaboration
- `POST /research/collaborations/generate-email` - Generate collaboration email
- `GET /research/collaborations/active` - Active collaborations

**Features:**
- Lab creation and management
- Researcher management
- Research focus tracking
- Lab-to-lab collaboration suggestions
- Collaboration scoring algorithm (0-100 based on research focus & expertise)
- Automated collaboration email generation

**Collaboration Scoring:**
- Research domain match: 40 points
- Partial domain match: 20 points
- Researcher expertise overlap: 15 points each
- Base score: 30 points
- Minimum threshold for suggestion: 60 points

---

### 6. Unified Dashboard

**Endpoint:**
- `GET /dashboard` - Unified dashboard combining all services

**Features:**
- Aggregated project data
- User tasks and activities
- Performance reviews and goals
- Lab information
- Team statistics (for managers/admins)
- Single view of all organizational data

---

## Architecture

### Microservices

| Service | Port | Database | Purpose |
|---------|------|----------|---------|
| Orchestrator | 9000 | project_management | API gateway, auth, coordination |
| Atlas | 8000 | atlas | Projects, tasks, issues |
| WorkPulse | 8001 | workpulse | Activity, productivity monitoring |
| EPR | 8003 | epr | Performance, reviews, goals |
| Labs | 8004 | labs | Research labs, collaboration |

### Key Technologies

- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL 15
- **Authentication:** JWT tokens
- **API Gateway:** Orchestrator service
- **Containerization:** Docker & Docker Compose
- **ORM:** SQLAlchemy with async support

### Design Patterns

- **Multi-tenancy:** Organization-based data isolation
- **Service-to-Service Communication:** HTTP clients with service tokens
- **Centralized Auth:** JWT validation at API gateway
- **Hot Reload:** Development mode with auto-reload
- **Health Checks:** Docker health checks for all services

---

## API Usage

### Authentication Flow

```bash
# 1. Register
curl -X POST http://localhost:9000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "name": "User Name",
    "password": "SecurePassword123!",
    "role": "member"
  }'

# Response includes JWT token and user organization

# 2. Use token for subsequent requests
curl -X GET http://localhost:9000/api/v1/auth/me \
  -H "Authorization: Bearer <token>"
```

### Create Project

```bash
curl -X POST http://localhost:9000/api/v1/projects \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mobile App",
    "description": "New mobile application",
    "status": "active"
  }'
```

### Log Activity

```bash
curl -X POST http://localhost:9000/api/v1/activities \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Completed login feature",
    "duration_seconds": 3600,
    "task_id": "task-uuid"
  }'
```

---

## Testing

### Run All Endpoint Tests

```bash
python test_endpoints_simple.py
```

### Run Auth Tests

```bash
python test_auth_flow.py
python test_auth_comprehensive.py
```

### Test Results

- **14/14 endpoints passing (100%)**
- All auth flows working
- Multi-organization support verified
- Collaboration features tested

---

## Environment Configuration

### .env File

```
DB_TYPE=postgresql
DB_HOST=postgres
DB_PORT=5432
DB_USER=admin
DB_PASSWORD=admin123
DATABASE_URL=postgresql+asyncpg://admin:admin123@postgres:5432/project_management
ORCHESTRATOR_PORT=9000
ENVIRONMENT=development
```

---

## Development

### Hot Reload

Services run with `--reload` flag in development mode. Changes to code are automatically reflected.

### Database Migrations

```bash
# Initialize databases
python init_all_databases.py

# Clean all databases
python cleanup_all_databases.py
```

### Service Logs

```bash
docker-compose logs -f orchestrator
docker-compose logs -f atlas
docker-compose logs -f workpulse
docker-compose logs -f epr
docker-compose logs -f labs
```

---

## Project Structure

```
.
├── services/
│   ├── orchestrator/          # API gateway & auth
│   ├── atlas/                 # Project management
│   ├── workpulse/             # Activity monitoring
│   ├── epr/                   # Performance reports
│   └── labs/                  # Research labs
├── docker-compose.yml         # Service orchestration
├── init-databases.sql         # Database initialization
├── config_loader.py           # Centralized config
└── test_*.py                  # Test scripts
```

---

## Status

✅ All 14 core endpoints tested and working
✅ Multi-organization support
✅ JWT authentication
✅ Lab collaboration features
✅ Performance tracking
✅ Activity monitoring
✅ Docker deployment ready
