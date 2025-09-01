"""Test catalog endpoints."""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from dto_api.main import app

client = TestClient(app)


@pytest.fixture
def sample_catalog_package():
    """Sample catalog package for testing."""
    return {
        "version": "1.0",
        "generated_at": datetime.utcnow().isoformat(),
        "environment": "test",
        "datasets": [
            {
                "name": "RAW.ORDERS",
                "kind": "table",
                "row_count_estimate": 1000,
                "columns": [
                    {"name": "ORDER_ID", "type": "NUMBER", "nullable": False},
                    {"name": "ORDER_TS", "type": "TIMESTAMP_NTZ", "nullable": False},
                    {"name": "CUSTOMER_ID", "type": "NUMBER", "nullable": False}
                ],
                "primary_key": ["ORDER_ID"],
                "foreign_keys": [],
                "watermark_column": "ORDER_TS",
                "lineage": []
            }
        ],
        "signatures": {}
    }


def test_import_catalog_package(sample_catalog_package):
    """Test importing a catalog package."""
    response = client.post(
        "/api/v1/catalog/import",
        json={
            "source_type": "catalog_package",
            "data": sample_catalog_package,
            "environment": "test"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "catalog_id" in data
    assert data["datasets_imported"] == 1
    assert isinstance(data["warnings"], list)


def test_import_invalid_source_type():
    """Test importing with invalid source type."""
    response = client.post(
        "/api/v1/catalog/import",
        json={
            "source_type": "invalid_type",
            "data": {},
            "environment": "test"
        }
    )
    
    assert response.status_code == 500  # Should fail with unsupported source type


def test_get_catalog_not_found():
    """Test getting non-existent catalog."""
    response = client.get("/api/v1/catalog/nonexistent-id")
    
    assert response.status_code == 404


def test_list_catalogs():
    """Test listing catalogs."""
    response = client.get("/api/v1/catalog")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "catalogs" in data
    assert "total" in data
    assert isinstance(data["catalogs"], list)
