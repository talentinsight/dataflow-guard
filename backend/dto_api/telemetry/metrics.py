"""Prometheus metrics configuration."""

from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge, Info
from fastapi import FastAPI


# Define metrics
api_requests_total = Counter(
    'dto_api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status_code']
)

api_request_duration_seconds = Histogram(
    'dto_api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint']
)

test_executions_total = Counter(
    'dto_test_executions_total',
    'Total test executions',
    ['test_type', 'status']
)

test_execution_duration_seconds = Histogram(
    'dto_test_execution_duration_seconds',
    'Test execution duration in seconds',
    ['test_type']
)

active_runs = Gauge(
    'dto_active_runs',
    'Number of currently active test runs'
)

catalog_imports_total = Counter(
    'dto_catalog_imports_total',
    'Total catalog imports',
    ['source_type', 'status']
)

ai_requests_total = Counter(
    'dto_ai_requests_total',
    'Total AI service requests',
    ['request_type', 'model', 'status']
)

ai_request_duration_seconds = Histogram(
    'dto_ai_request_duration_seconds',
    'AI request duration in seconds',
    ['request_type', 'model']
)

ai_tokens_total = Counter(
    'dto_ai_tokens_total',
    'Total AI tokens consumed',
    ['model', 'token_type']  # token_type: prompt, completion
)

database_connections = Gauge(
    'dto_database_connections',
    'Number of active database connections',
    ['connection_name', 'connection_type']
)

policy_violations_total = Counter(
    'dto_policy_violations_total',
    'Total policy violations',
    ['policy_type', 'severity']
)

artifact_storage_operations_total = Counter(
    'dto_artifact_storage_operations_total',
    'Total artifact storage operations',
    ['operation', 'status']
)

system_info = Info(
    'dto_system_info',
    'System information'
)


def setup_metrics(app: FastAPI) -> None:
    """Setup metrics collection for FastAPI app."""
    
    # Set system info
    system_info.info({
        'version': '0.1.0',
        'component': 'dto-api'
    })
    
    # Middleware for request metrics is handled by prometheus-fastapi-instrumentator
    # in main.py - this provides additional custom metrics


def record_api_request(method: str, endpoint: str, status_code: int, duration: float) -> None:
    """Record API request metrics."""
    api_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status_code=str(status_code)
    ).inc()
    
    api_request_duration_seconds.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)


def record_test_execution(test_type: str, status: str, duration: float) -> None:
    """Record test execution metrics."""
    test_executions_total.labels(
        test_type=test_type,
        status=status
    ).inc()
    
    test_execution_duration_seconds.labels(
        test_type=test_type
    ).observe(duration)


def record_catalog_import(source_type: str, status: str) -> None:
    """Record catalog import metrics."""
    catalog_imports_total.labels(
        source_type=source_type,
        status=status
    ).inc()


def record_ai_request(
    request_type: str, 
    model: str, 
    status: str, 
    duration: float,
    prompt_tokens: int = 0,
    completion_tokens: int = 0
) -> None:
    """Record AI service request metrics."""
    ai_requests_total.labels(
        request_type=request_type,
        model=model,
        status=status
    ).inc()
    
    ai_request_duration_seconds.labels(
        request_type=request_type,
        model=model
    ).observe(duration)
    
    if prompt_tokens > 0:
        ai_tokens_total.labels(
            model=model,
            token_type="prompt"
        ).inc(prompt_tokens)
    
    if completion_tokens > 0:
        ai_tokens_total.labels(
            model=model,
            token_type="completion"
        ).inc(completion_tokens)


def record_policy_violation(policy_type: str, severity: str) -> None:
    """Record policy violation metrics."""
    policy_violations_total.labels(
        policy_type=policy_type,
        severity=severity
    ).inc()


def record_artifact_operation(operation: str, status: str) -> None:
    """Record artifact storage operation metrics."""
    artifact_storage_operations_total.labels(
        operation=operation,
        status=status
    ).inc()


def update_active_runs(count: int) -> None:
    """Update active runs gauge."""
    active_runs.set(count)


def update_database_connections(connection_name: str, connection_type: str, count: int) -> None:
    """Update database connections gauge."""
    database_connections.labels(
        connection_name=connection_name,
        connection_type=connection_type
    ).set(count)


def get_metrics_summary() -> Dict[str, Any]:
    """Get current metrics summary for health checks."""
    from prometheus_client import REGISTRY
    
    # This would collect current metric values
    # For now, return a simple summary
    return {
        "metrics_enabled": True,
        "collectors_registered": len(REGISTRY._collector_to_names),
        "custom_metrics": [
            "dto_api_requests_total",
            "dto_test_executions_total", 
            "dto_active_runs",
            "dto_ai_requests_total",
            "dto_policy_violations_total"
        ]
    }
