"""Unit tests for readiness endpoint dependency checks."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from dto_api.main import app


class TestReadinessEndpoint:
    """Test cases for /readyz endpoint dependency checks."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
    
    @patch('dto_api.db.models.get_db_manager')
    @patch('dto_api.adapters.connectors.snowflake.SnowflakeConnector')
    @patch('dto_api.services.artifact_service.artifact_service')
    def test_readyz_all_healthy(self, mock_artifact_service, mock_snowflake, mock_get_db_manager):
        """Test readiness check when all dependencies are healthy."""
        # Mock database manager
        mock_db_manager = Mock()
        mock_db_manager.health_check.return_value = True
        mock_get_db_manager.return_value = mock_db_manager
        
        # Mock Snowflake connector
        mock_connector_instance = AsyncMock()
        mock_snowflake.return_value = mock_connector_instance
        
        # Mock artifact service
        mock_artifact_service.health_check.return_value = True
        
        response = self.client.get("/api/v1/readyz")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "ready"
        assert data["checks"]["database"]["status"] == "healthy"
        assert data["checks"]["snowflake"]["status"] == "healthy"
        assert data["checks"]["artifact_storage"]["status"] == "healthy"
        
        # Verify response times are included
        assert "response_time_ms" in data["checks"]["database"]
        assert "response_time_ms" in data["checks"]["snowflake"]
        assert "response_time_ms" in data["checks"]["artifact_storage"]
    
    @patch('dto_api.db.models.get_db_manager')
    @patch('dto_api.adapters.connectors.snowflake.SnowflakeConnector')
    @patch('dto_api.services.artifact_service.artifact_service')
    def test_readyz_database_unhealthy(self, mock_artifact_service, mock_snowflake, mock_get_db_manager):
        """Test readiness check when database is unhealthy."""
        # Mock database manager failure
        mock_db_manager = Mock()
        mock_db_manager.health_check.return_value = False
        mock_get_db_manager.return_value = mock_db_manager
        
        # Mock other services as healthy
        mock_connector_instance = AsyncMock()
        mock_snowflake.return_value = mock_connector_instance
        mock_artifact_service.health_check.return_value = True
        
        response = self.client.get("/api/v1/readyz")
        
        assert response.status_code == 503
        data = response.json()
        
        assert data["detail"]["status"] == "not_ready"
        assert data["detail"]["checks"]["database"]["status"] == "unhealthy"
        assert data["detail"]["checks"]["snowflake"]["status"] == "healthy"
        assert data["detail"]["checks"]["artifact_storage"]["status"] == "healthy"
        assert "Service not ready" in data["detail"]["message"]
    
    @patch('dto_api.db.models.get_db_manager')
    @patch('dto_api.adapters.connectors.snowflake.SnowflakeConnector')
    @patch('dto_api.services.artifact_service.artifact_service')
    def test_readyz_snowflake_unhealthy(self, mock_artifact_service, mock_snowflake, mock_get_db_manager):
        """Test readiness check when Snowflake is unhealthy."""
        # Mock database as healthy
        mock_db_manager = Mock()
        mock_db_manager.health_check.return_value = True
        mock_get_db_manager.return_value = mock_db_manager
        
        # Mock Snowflake connector failure
        mock_connector_instance = AsyncMock()
        mock_connector_instance.connect.side_effect = Exception("Connection failed")
        mock_snowflake.return_value = mock_connector_instance
        
        # Mock artifact service as healthy
        mock_artifact_service.health_check.return_value = True
        
        response = self.client.get("/api/v1/readyz")
        
        assert response.status_code == 503
        data = response.json()
        
        assert data["detail"]["status"] == "not_ready"
        assert data["detail"]["checks"]["database"]["status"] == "healthy"
        assert data["detail"]["checks"]["snowflake"]["status"] == "unhealthy"
        assert "Connection failed" in data["detail"]["checks"]["snowflake"]["error"]
    
    @patch('dto_api.db.models.get_db_manager')
    @patch('dto_api.adapters.connectors.snowflake.SnowflakeConnector')
    @patch('dto_api.services.artifact_service.artifact_service')
    def test_readyz_artifact_storage_unhealthy(self, mock_artifact_service, mock_snowflake, mock_get_db_manager):
        """Test readiness check when artifact storage is unhealthy."""
        # Mock database as healthy
        mock_db_manager = Mock()
        mock_db_manager.health_check.return_value = True
        mock_get_db_manager.return_value = mock_db_manager
        
        # Mock Snowflake as healthy
        mock_connector_instance = AsyncMock()
        mock_snowflake.return_value = mock_connector_instance
        
        # Mock artifact service failure
        mock_artifact_service.health_check.return_value = False
        
        response = self.client.get("/api/v1/readyz")
        
        assert response.status_code == 503
        data = response.json()
        
        assert data["detail"]["status"] == "not_ready"
        assert data["detail"]["checks"]["database"]["status"] == "healthy"
        assert data["detail"]["checks"]["snowflake"]["status"] == "healthy"
        assert data["detail"]["checks"]["artifact_storage"]["status"] == "unhealthy"
    
    @patch('dto_api.db.models.get_db_manager')
    @patch('dto_api.adapters.connectors.snowflake.SnowflakeConnector')
    @patch('dto_api.services.artifact_service.artifact_service')
    def test_readyz_multiple_failures(self, mock_artifact_service, mock_snowflake, mock_get_db_manager):
        """Test readiness check when multiple dependencies fail."""
        # Mock database failure
        mock_get_db_manager.side_effect = Exception("Database connection error")
        
        # Mock Snowflake failure
        mock_connector_instance = AsyncMock()
        mock_connector_instance.connect.side_effect = Exception("Snowflake error")
        mock_snowflake.return_value = mock_connector_instance
        
        # Mock artifact service failure
        mock_artifact_service.health_check.side_effect = Exception("MinIO error")
        
        response = self.client.get("/api/v1/readyz")
        
        assert response.status_code == 503
        data = response.json()
        
        assert data["detail"]["status"] == "not_ready"
        assert data["detail"]["checks"]["database"]["status"] == "unhealthy"
        assert data["detail"]["checks"]["snowflake"]["status"] == "unhealthy"
        assert data["detail"]["checks"]["artifact_storage"]["status"] == "unhealthy"
        
        # Verify error messages are captured
        assert "Database connection error" in data["detail"]["checks"]["database"]["error"]
        assert "Snowflake error" in data["detail"]["checks"]["snowflake"]["error"]
        assert "MinIO error" in data["detail"]["checks"]["artifact_storage"]["error"]
    
    @patch('dto_api.db.models.get_db_manager')
    @patch('dto_api.adapters.connectors.snowflake.SnowflakeConnector')
    @patch('dto_api.services.artifact_service.artifact_service')
    def test_readyz_response_structure(self, mock_artifact_service, mock_snowflake, mock_get_db_manager):
        """Test readiness response structure and required fields."""
        # Mock all services as healthy
        mock_db_manager = Mock()
        mock_db_manager.health_check.return_value = True
        mock_get_db_manager.return_value = mock_db_manager
        
        mock_connector_instance = AsyncMock()
        mock_snowflake.return_value = mock_connector_instance
        mock_artifact_service.health_check.return_value = True
        
        response = self.client.get("/api/v1/readyz")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify top-level structure
        assert "status" in data
        assert "checks" in data
        
        # Verify each check has required fields
        for check_name in ["database", "snowflake", "artifact_storage"]:
            check = data["checks"][check_name]
            assert "status" in check
            assert check["status"] in ["healthy", "unhealthy"]
            
            if check["status"] == "healthy":
                assert "response_time_ms" in check
                assert isinstance(check["response_time_ms"], int)
            else:
                assert "error" in check
    
    @patch('dto_api.db.models.get_db_manager')
    @patch('dto_api.adapters.connectors.snowflake.SnowflakeConnector')
    @patch('dto_api.services.artifact_service.artifact_service')
    def test_readyz_database_type_info(self, mock_artifact_service, mock_snowflake, mock_get_db_manager):
        """Test that database type information is included."""
        mock_db_manager = Mock()
        mock_db_manager.health_check.return_value = True
        mock_get_db_manager.return_value = mock_db_manager
        
        mock_connector_instance = AsyncMock()
        mock_snowflake.return_value = mock_connector_instance
        mock_artifact_service.health_check.return_value = True
        
        response = self.client.get("/api/v1/readyz")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["checks"]["database"]["type"] == "postgresql"
        assert data["checks"]["artifact_storage"]["type"] == "minio"
    
    def test_healthz_endpoint(self):
        """Test basic health check endpoint."""
        response = self.client.get("/api/v1/healthz")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"
        assert "timestamp" in data
    
    def test_version_endpoint(self):
        """Test version information endpoint."""
        response = self.client.get("/api/v1/version")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "version" in data
        assert "build_date" in data
        assert "commit_sha" in data
