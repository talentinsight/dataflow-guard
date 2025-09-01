# DTO Development Makefile

.PHONY: help dev build test test-integration lint fmt clean docker-build docker-up docker-down openapi

# Default target
help:
	@echo "DTO Development Commands:"
	@echo ""
	@echo "Development:"
	@echo "  dev          - Start development environment (fast, with hot reload)"
	@echo "  dev-up       - Start dev containers"
	@echo "  dev-down     - Stop dev containers"
	@echo "  dev-logs     - Show dev logs"
	@echo "  dev-build    - Build dev images"
	@echo "  dev-api      - Start only API backend for development"
	@echo "  dev-frontend - Start only frontend for development"
	@echo ""
	@echo "Build & Test:"
	@echo "  build        - Build all components"
	@echo "  test         - Run unit tests (excluding integration tests)"
	@echo "  test-integration - Run all tests including Snowflake integration"
	@echo "  lint         - Run linters"
	@echo "  fmt          - Format code"
	@echo "  type-check   - Run type checking"
	@echo ""
	@echo "Docker Compose:"
	@echo "  compose.up   - Start services with docker-compose"
	@echo "  compose.down - Stop services"
	@echo "  compose.logs - View service logs"
	@echo "  compose.build- Build Docker images"
	@echo ""
	@echo "Local Development:"
	@echo "  api.dev      - Start API backend locally (uvicorn)"
	@echo "  front.dev    - Start frontend locally (next dev)"
	@echo ""
	@echo "Docker (legacy):"
	@echo "  docker-build - Build Docker images"
	@echo "  docker-up    - Start services with docker-compose"
	@echo "  docker-down  - Stop services"
	@echo "  docker-logs  - View service logs"
	@echo ""
	@echo "API:"
	@echo "  openapi      - Generate OpenAPI spec"
	@echo "  api-docs     - View API documentation"
	@echo ""
	@echo "Utilities:"
	@echo "  clean        - Clean build artifacts"
	@echo "  setup        - Initial project setup"

# Development
dev: dev-up
	@echo "✅ Development environment started"
	@echo "   API: http://localhost:8000"
	@echo "   Frontend: http://localhost:3000"
	@echo "   MinIO Console: http://localhost:9001"

dev-up:
	@echo "🚀 Starting development environment..."
	cd infra && docker-compose -f docker-compose.dev.yml up -d

dev-down:
	@echo "🛑 Stopping development environment..."
	cd infra && docker-compose -f docker-compose.dev.yml down

dev-logs:
	@echo "📋 Showing development logs..."
	cd infra && docker-compose -f docker-compose.dev.yml logs -f

dev-build:
	@echo "🔨 Building development images..."
	cd infra && docker-compose -f docker-compose.dev.yml build

dev-api:
	@echo "🚀 Starting API backend locally..."
	cd backend && source .venv/bin/activate && python -m uvicorn dto_api.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	@echo "🚀 Starting frontend locally..."
	cd frontend && npm run dev

dev-local:
	@echo "🚀 Starting local development (no Docker)..."
	@echo "Starting frontend in background..."
	cd frontend && npm run dev &
	@echo "Starting API..."
	cd backend && source .venv/bin/activate && python -m uvicorn dto_api.main:app --reload --host 0.0.0.0 --port 8000

dev-local-frontend:
	@echo "🚀 Starting frontend only (local)..."
	cd frontend && npm run dev

dev-local-api:
	@echo "🚀 Starting API only (local)..."
	cd backend && source .venv/bin/activate && python -m uvicorn dto_api.main:app --reload --host 0.0.0.0 --port 8000

# Build & Test
build:
	@echo "🔨 Building backend..."
	cd backend && pip install -e .
	@echo "🔨 Building frontend..."
	cd frontend && npm run build

test:
	@echo "🧪 Running backend unit tests..."
	cd backend && python -m pytest tests/ -v -m "not integration"
	@echo "🧪 Running frontend tests..."
	cd frontend && npm run test

test-integration:
	@echo "🧪 Running all backend tests (including Snowflake integration)..."
	cd backend && python -m pytest tests/ -v
	@echo "🧪 Running frontend tests..."
	cd frontend && npm run test

lint:
	@echo "🔍 Linting backend..."
	cd backend && ruff check dto_api/ dto_cli/ tests/
	cd backend && mypy dto_api/ dto_cli/
	@echo "🔍 Linting frontend..."
	cd frontend && npm run lint

fmt:
	@echo "✨ Formatting backend..."
	cd backend && black dto_api/ dto_cli/ tests/
	cd backend && ruff --fix dto_api/ dto_cli/ tests/
	@echo "✨ Formatting frontend..."
	cd frontend && npm run lint -- --fix

type-check:
	@echo "🔍 Type checking backend..."
	cd backend && mypy dto_api/ dto_cli/
	@echo "🔍 Type checking frontend..."
	cd frontend && npm run type-check

# Docker Compose
compose.up:
	@echo "🐳 Starting services with docker-compose..."
	docker compose -f infra/docker-compose.yml up -d
	@echo "⏳ Waiting for services to be ready..."
	@sleep 15
	@echo "✅ Services started successfully!"
	@echo "   API: http://localhost:8000"
	@echo "   Frontend: http://localhost:3000"
	@echo "   MinIO Console: http://localhost:9001"

compose.down:
	@echo "🐳 Stopping services..."
	docker compose -f infra/docker-compose.yml down

compose.logs:
	@echo "📋 Showing service logs..."
	docker compose -f infra/docker-compose.yml logs -f

compose.build:
	@echo "🔨 Building Docker images..."
	docker compose -f infra/docker-compose.yml build --no-cache

# Development (local)
api.dev:
	@echo "🚀 Starting API backend locally..."
	cd backend && source ../.venv/bin/activate && uvicorn dto_api.main:app --reload --host 0.0.0.0 --port 8000

front.dev:
	@echo "🚀 Starting frontend locally..."
	cd frontend && npm run dev

# Docker (legacy targets)
docker-build:
	@echo "🐳 Building Docker images..."
	docker build -t dto/api:latest backend/
	docker build -t dto/frontend:latest frontend/

docker-up:
	@echo "🐳 Starting services..."
	cd infra && docker-compose up -d
	@echo "⏳ Waiting for services to be ready..."
	@sleep 10
	@echo "✅ Services started successfully!"

docker-down:
	@echo "🐳 Stopping services..."
	cd infra && docker-compose down

docker-rebuild:
	@echo "🐳 Rebuilding Docker images..."
	cd infra && docker-compose build --no-cache

docker-logs:
	cd infra && docker-compose logs -f

# API Documentation
openapi:
	@echo "📋 Generating OpenAPI spec..."
	cd backend && python -c "from dto_api.main import app; import json; print(json.dumps(app.openapi(), indent=2))" > ../docs/openapi.json
	@echo "✅ OpenAPI spec generated at docs/openapi.json"

api-docs:
	@echo "📖 Opening API documentation..."
	@echo "Visit: http://localhost:8000/docs"

# Utilities
clean:
	@echo "🧹 Cleaning build artifacts..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	cd frontend && rm -rf .next node_modules/.cache
	cd backend && rm -rf build/ dist/
	@echo "✅ Cleanup complete"

setup:
	@echo "🔧 Setting up development environment..."
	@echo "Installing backend dependencies..."
	cd backend && pip install -e ".[dev]"
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Setting up pre-commit hooks..."
	cd backend && pre-commit install
	@echo "✅ Setup complete!"

# Health checks
health:
	@echo "🏥 Checking service health..."
	@curl -f http://localhost:8000/api/v1/healthz || echo "❌ API not healthy"
	@curl -f http://localhost:3000 || echo "❌ Frontend not healthy"

# Database operations
db-migrate:
	@echo "🗃️  Running database migrations..."
	cd backend && alembic upgrade head

db-reset:
	@echo "🗃️  Resetting database..."
	cd infra && docker-compose exec postgres psql -U dto -d dto -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	$(MAKE) db-migrate

# CLI operations
cli-help:
	cd backend && python -m dto_cli --help

cli-health:
	cd backend && python -m dto_cli health

# Security checks
security-check:
	@echo "🔒 Running security checks..."
	cd backend && pip-audit
	cd frontend && npm audit

# Performance testing
perf-test:
	@echo "⚡ Running performance tests..."
	@echo "TODO: Implement performance tests"

# Deployment helpers
deploy-dev:
	@echo "🚀 Deploying to development..."
	kubectl apply -f infra/k8s/dev/

deploy-staging:
	@echo "🚀 Deploying to staging..."
	kubectl apply -f infra/k8s/staging/

# Monitoring
logs-api:
	cd infra && docker-compose logs -f api

logs-frontend:
	cd infra && docker-compose logs -f frontend

logs-db:
	cd infra && docker-compose logs -f postgres

# Backup
backup-db:
	@echo "💾 Creating database backup..."
	cd infra && docker-compose exec postgres pg_dump -U dto dto > backup_$(shell date +%Y%m%d_%H%M%S).sql

# Load testing
load-test:
	@echo "🔥 Running load tests..."
	@echo "TODO: Implement load tests with locust or similar"
