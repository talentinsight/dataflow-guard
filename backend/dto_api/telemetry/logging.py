"""Structured logging configuration."""

import logging
import sys
from typing import Any, Dict

import structlog


def setup_logging(log_level: str = "INFO") -> None:
    """Setup structured logging with JSON output."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        logger_factory=structlog.WriteLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_request_logger(request_id: str) -> structlog.BoundLogger:
    """Get logger bound with request ID."""
    return structlog.get_logger().bind(request_id=request_id)


def log_api_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    request_id: str,
    user_id: str = None,
    **kwargs
) -> None:
    """Log API request with standard fields."""
    logger = structlog.get_logger()
    
    log_data = {
        "event": "api_request",
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": duration_ms,
        "request_id": request_id,
        **kwargs
    }
    
    if user_id:
        log_data["user_id"] = user_id
    
    if status_code >= 500:
        logger.error("API request failed", **log_data)
    elif status_code >= 400:
        logger.warning("API request error", **log_data)
    else:
        logger.info("API request", **log_data)


def log_test_execution(
    run_id: str,
    test_name: str,
    status: str,
    duration_ms: int,
    **kwargs
) -> None:
    """Log test execution with standard fields."""
    logger = structlog.get_logger()
    
    log_data = {
        "event": "test_execution",
        "run_id": run_id,
        "test_name": test_name,
        "status": status,
        "duration_ms": duration_ms,
        **kwargs
    }
    
    if status == "fail":
        logger.warning("Test failed", **log_data)
    elif status == "error":
        logger.error("Test error", **log_data)
    else:
        logger.info("Test executed", **log_data)


def log_ai_interaction(
    request_type: str,
    model: str,
    prompt_tokens: int = None,
    completion_tokens: int = None,
    duration_ms: float = None,
    success: bool = True,
    **kwargs
) -> None:
    """Log AI service interaction."""
    logger = structlog.get_logger()
    
    log_data = {
        "event": "ai_interaction",
        "request_type": request_type,
        "model": model,
        "success": success,
        **kwargs
    }
    
    if prompt_tokens:
        log_data["prompt_tokens"] = prompt_tokens
    if completion_tokens:
        log_data["completion_tokens"] = completion_tokens
    if duration_ms:
        log_data["duration_ms"] = duration_ms
    
    if success:
        logger.info("AI interaction", **log_data)
    else:
        logger.error("AI interaction failed", **log_data)


def log_security_event(
    event_type: str,
    user_id: str = None,
    details: Dict[str, Any] = None,
    severity: str = "info"
) -> None:
    """Log security-related events."""
    logger = structlog.get_logger()
    
    log_data = {
        "event": "security_event",
        "event_type": event_type,
        "severity": severity
    }
    
    if user_id:
        log_data["user_id"] = user_id
    if details:
        log_data.update(details)
    
    if severity == "critical":
        logger.critical("Security event", **log_data)
    elif severity == "error":
        logger.error("Security event", **log_data)
    elif severity == "warning":
        logger.warning("Security event", **log_data)
    else:
        logger.info("Security event", **log_data)
