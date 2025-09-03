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
    from dto_api.db.models import get_db_manager
    from dto_api.adapters.connectors.snowflake import SnowflakeConnector
    from dto_api.services.artifact_service import artifact_service
    import time
    
    checks = {}
    
    # Database connectivity check
    try:
        start_time = time.time()
        db_manager = get_db_manager()
        
        if db_manager.health_check():
            checks["database"] = {
                "status": "healthy", 
                "response_time_ms": int((time.time() - start_time) * 1000),
                "type": "postgresql"
            }
        else:
            checks["database"] = {
                "status": "unhealthy",
                "error": "Database connection failed"
            }
                
    except Exception as e:
        logger.error("Database health check failed", exc_info=e)
        checks["database"] = {"status": "unhealthy", "error": str(e)}
    
    # Snowflake connector check
    try:
        start_time = time.time()
        connector = SnowflakeConnector()
        
        # Test connection (this will use environment variables)
        await connector.connect()
        await connector.disconnect()
        
        checks["snowflake"] = {
            "status": "healthy", 
            "response_time_ms": int((time.time() - start_time) * 1000)
        }
    except Exception as e:
        logger.error("Snowflake health check failed", exc_info=e)
        checks["snowflake"] = {"status": "unhealthy", "error": str(e)}
    
    # MinIO/artifact storage check
    try:
        start_time = time.time()
        
        if artifact_service.health_check():
            checks["artifact_storage"] = {
                "status": "healthy", 
                "response_time_ms": int((time.time() - start_time) * 1000),
                "type": "minio"
            }
        else:
            checks["artifact_storage"] = {
                "status": "unhealthy",
                "error": "MinIO connection failed"
            }
    except Exception as e:
        logger.error("Artifact storage health check failed", exc_info=e)
        checks["artifact_storage"] = {"status": "unhealthy", "error": str(e)}
    
    # Determine overall status
    all_healthy = all(check.get("status") == "healthy" for check in checks.values())
    status = "ready" if all_healthy else "not_ready"
    
    # Return 503 if not ready
    if not all_healthy:
        raise HTTPException(
            status_code=503, 
            detail={
                "status": status,
                "checks": checks,
                "message": "Service not ready - one or more dependencies unhealthy"
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
