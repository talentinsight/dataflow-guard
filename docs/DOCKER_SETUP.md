# Docker Compose Setup

This document describes how to run DataFlowGuard using Docker Compose for local development and testing.

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Make (optional, for convenience)

### Start All Services

```bash
# Using Make (recommended)
make compose.up

# Or directly with docker compose
docker compose -f infra/docker-compose.yml up -d
```

This will start:
- **API Backend** on http://localhost:8000
- **Frontend** on http://localhost:3000  
- **PostgreSQL** database on localhost:5432
- **MinIO** object storage on http://localhost:9000 (console: http://localhost:9001)

### Stop All Services

```bash
# Using Make
make compose.down

# Or directly
docker compose -f infra/docker-compose.yml down
```

## Services Overview

| Service | Port | Description | Health Check |
|---------|------|-------------|--------------|
| `api` | 8000 | FastAPI backend | `GET /api/v1/healthz` |
| `frontend` | 3000 | Next.js frontend | `GET /` |
| `postgres` | 5432 | PostgreSQL database | `pg_isready` |
| `minio` | 9000/9001 | Object storage | `GET /minio/health/live` |

## Environment Configuration

### Backend (.env)
The API service reads from `backend/.env`:
```bash
# Database
DATABASE_URL=postgresql+psycopg://dfg_user:dfg_password@postgres:5432/dfg_db

# Snowflake (optional)
SNOWFLAKE_ACCOUNT=your-account
SNOWFLAKE_USER=your-user
SNOWFLAKE_PASSWORD=your-password
```

### Frontend (.env)
The frontend service reads from `frontend/.env`:
```bash
# API endpoint
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Environment
NODE_ENV=development
```

## Development Workflow

### 1. Start Services
```bash
make compose.up
```

### 2. Check Health
```bash
# API health
curl http://localhost:8000/api/v1/healthz

# Frontend
curl http://localhost:3000

# Or use the health check target
make health
```

### 3. View Logs
```bash
# All services
make compose.logs

# Specific service
docker compose -f infra/docker-compose.yml logs -f api
```

### 4. Rebuild Images
```bash
# Rebuild all images
make compose.build

# Or rebuild specific service
docker compose -f infra/docker-compose.yml build api
```

## Local Development (No Docker)

For faster development with hot reload:

```bash
# Terminal 1: Start API locally
make api.dev

# Terminal 2: Start frontend locally  
make front.dev
```

This runs:
- API: `uvicorn dto_api.main:app --reload` on port 8000
- Frontend: `npm run dev` on port 3000

## Database Operations

### Run Migrations
```bash
# Connect to running postgres container
docker compose -f infra/docker-compose.yml exec postgres psql -U dfg_user -d dfg_db

# Or run migrations from backend
cd backend && alembic upgrade head
```

### Reset Database
```bash
make db-reset
```

## Troubleshooting

### Port Conflicts
If ports are already in use, modify `infra/docker-compose.yml`:
```yaml
services:
  api:
    ports:
      - "8001:8000"  # Change host port
```

### Build Issues
```bash
# Clean rebuild
make compose.build

# Check service logs
make compose.logs
```

### Health Check Failures
```bash
# Check individual service health
docker compose -f infra/docker-compose.yml ps

# View specific service logs
docker compose -f infra/docker-compose.yml logs api
```

## Production Considerations

This setup is for **development only**. For production:

1. Use proper secrets management
2. Configure SSL/TLS
3. Use production database settings
4. Set up proper logging and monitoring
5. Configure resource limits
6. Use multi-stage builds for smaller images
