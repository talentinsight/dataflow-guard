"""Health check endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import structlog
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter()
logger = structlog.get_logger()


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str
    version: str
    timestamp: str


class ReadinessResponse(BaseModel):
    """Readiness check response."""
    
    status: str
    checks: Dict[str, Any]


class VersionResponse(BaseModel):
    """Version information response."""
    
    version: str
    build_date: str
    commit_sha: str


@router.get("/healthz", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic health check endpoint."""
    from datetime import datetime
    
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        timestamp=datetime.utcnow().isoformat()
    )


@router.get("/readyz", response_model=ReadinessResponse)
async def readiness_check() -> ReadinessResponse:
    """Readiness check with dependency validation."""
    from dto_api.db import get_engine
    import time
    
    checks = {}
    
    # Database connectivity and migration check
    try:
        start_time = time.time()
        engine = get_engine()
        
        # Test basic connectivity
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            
            # Check if Alembic migrations have been run
            try:
                result = conn.execute(text("SELECT version_num FROM alembic_version"))
                version = result.scalar()
                if version:
                    checks["database"] = {
                        "status": "healthy", 
                        "response_time_ms": int((time.time() - start_time) * 1000),
                        "migration_version": version
                    }
                else:
                    checks["database"] = {
                        "status": "unhealthy", 
                        "error": "No migration version found",
                        "hint": "Run 'make db-migrate' to initialize database"
                    }
            except SQLAlchemyError:
                # alembic_version table doesn't exist
                checks["database"] = {
                    "status": "unhealthy",
                    "error": "Database not migrated",
                    "hint": "Run 'make db-migrate' to initialize database"
                }
                
    except Exception as e:
        logger.error("Database health check failed", exc_info=e)
        checks["database"] = {"status": "unhealthy", "error": str(e)}
    
    # AI service check (stub)
    try:
        # TODO: Implement actual AI service connectivity check
        checks["ai_service"] = {"status": "healthy", "response_time_ms": 10}
    except Exception as e:
        logger.error("AI service health check failed", exc_info=e)
        checks["ai_service"] = {"status": "unhealthy", "error": str(e)}
    
    # Artifact storage check (stub)
    try:
        # TODO: Implement actual storage connectivity check
        checks["artifact_storage"] = {"status": "healthy", "response_time_ms": 3}
    except Exception as e:
        logger.error("Artifact storage health check failed", exc_info=e)
        checks["artifact_storage"] = {"status": "unhealthy", "error": str(e)}
    
    # Determine overall status
    all_healthy = all(check.get("status") == "healthy" for check in checks.values())
    status = "ready" if all_healthy else "not_ready"
    
    # Return 503 if not ready (especially for database migration issues)
    if not all_healthy and checks.get("database", {}).get("status") == "unhealthy":
        raise HTTPException(
            status_code=503, 
            detail={
                "status": status,
                "checks": checks,
                "message": "Service not ready - database migration required"
            }
        )
    
    return ReadinessResponse(
        status=status,
        checks=checks
    )


@router.get("/version", response_model=VersionResponse)
async def version_info() -> VersionResponse:
    """Version and build information."""
    return VersionResponse(
        version="0.1.0",
        build_date="2025-01-01T00:00:00Z",  # TODO: Inject at build time
        commit_sha="dev"  # TODO: Inject at build time
    )
