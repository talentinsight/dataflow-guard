"""Test health endpoints."""

import pytest
from fastapi.testclient import TestClient

from dto_api.main import app

client = TestClient(app)


def test_health_check():
    """Test basic health check endpoint."""
    response = client.get("/api/v1/healthz")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data


def test_readiness_check():
    """Test readiness check endpoint."""
    response = client.get("/api/v1/readyz")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert "checks" in data
    assert isinstance(data["checks"], dict)


def test_version_info():
    """Test version endpoint."""
    response = client.get("/api/v1/version")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "version" in data
    assert "build_date" in data
    assert "commit_sha" in data


def test_metrics_endpoint():
    """Test Prometheus metrics endpoint."""
    response = client.get("/metrics")
    
    assert response.status_code == 200
    assert "dto_" in response.text  # Should contain our custom metrics
