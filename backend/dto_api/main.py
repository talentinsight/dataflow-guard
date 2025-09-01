"""FastAPI main application entry point."""

import logging
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from dto_api.routers import catalog, datasets, health, runs, settings, tests, sep
from dto_api.telemetry.logging import setup_logging
from dto_api.telemetry.metrics import setup_metrics


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Setup logging and metrics
    setup_logging()
    setup_metrics(app)
    
    logger = structlog.get_logger()
    logger.info("DTO API starting up", version="0.1.0")
    
    yield
    
    logger.info("DTO API shutting down")


# Create FastAPI app
app = FastAPI(
    title="Data Testing Orchestrator API",
    description="Zero-SQL, AI-assisted, push-down data testing framework",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

# CORS middleware - restrictive by default
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend dev server
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests for tracing."""
    request_id = str(uuid.uuid4())
    
    # Add to request state
    request.state.request_id = request_id
    
    # Add to structlog context
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    
    response = await call_next(request)
    
    # Add to response headers
    response.headers["X-Request-ID"] = request_id
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler following RFC-7807."""
    logger = structlog.get_logger()
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        request_id=request_id,
        path=request.url.path,
        method=request.method,
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "type": "about:blank",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred",
            "instance": request.url.path,
            "request_id": request_id,
        },
    )


# Include routers with /api/v1 prefix
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(catalog.router, prefix="/api/v1", tags=["catalog"])
app.include_router(datasets.router, prefix="/api/v1", tags=["datasets"])
app.include_router(tests.router, prefix="/api/v1", tags=["tests"])
app.include_router(runs.router, prefix="/api/v1", tags=["runs"])
app.include_router(settings.router, prefix="/api/v1", tags=["settings"])
app.include_router(sep.router, prefix="/api/v1", tags=["sep"])

# Setup Prometheus metrics
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app, endpoint="/metrics")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "dto_api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None,  # Use our custom logging
    )
