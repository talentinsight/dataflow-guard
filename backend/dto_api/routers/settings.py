"""Settings and configuration endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException
import structlog

from dto_api.models.settings import (
    SystemSettings,
    ConnectionSettings,
    AuthProviderSettings,
    AIProviderSettings,
    PolicySettings
)

router = APIRouter()
logger = structlog.get_logger()


@router.get("/settings/connections", response_model=List[ConnectionSettings])
async def get_connections() -> List[ConnectionSettings]:
    """Get all database connections with secrets masked."""
    try:
        # TODO: Implement actual settings retrieval from database
        # For now, return mock data with security defaults
        mock_connections = [
            ConnectionSettings(
                name="snowflake_prod",
                type="snowflake",
                account="xy12345.eu-west-1",
                username="dfg_runner",
                database="PROD_DB",
                schema="RAW",
                warehouse="ANALYTICS_WH",
                role="DFG_RO",
                region="eu-west-1",
                auth_method="private_key",
                read_only=True,
                enabled=True
            ),
            ConnectionSettings(
                name="postgres_dev",
                type="postgres",
                host="localhost",
                port=5432,
                database="dev_db",
                schema="public",
                username="dto_user",
                auth_method="password",
                read_only=True,
                enabled=True
            )
        ]
        
        # Mask secrets before returning
        return [conn.mask_secrets() for conn in mock_connections]
        
    except Exception as e:
        logger.error("Failed to get connections", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to get connections: {str(e)}")


@router.post("/settings/connections", response_model=ConnectionSettings)
async def create_connection(connection: ConnectionSettings) -> ConnectionSettings:
    """Create a new database connection."""
    try:
        logger.info("Creating connection", connection_name=connection.name)
        
        # Enforce security defaults
        connection.read_only = True
        
        # TODO: Implement actual connection creation in database
        # TODO: Validate connection before saving
        
        logger.info("Connection created", connection_name=connection.name)
        return connection.mask_secrets()
        
    except Exception as e:
        logger.error("Failed to create connection", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to create connection: {str(e)}")


@router.post("/settings/connections/test-connection")
async def test_connection(connection: ConnectionSettings) -> dict:
    """Test a database connection."""
    try:
        logger.info("Testing connection", connection_name=connection.name, connection_type=connection.type)
        
        if connection.type == "snowflake":
            from dto_api.adapters.connectors.snowflake import SnowflakeConnector
            
            # Convert connection settings to connector format
            settings = {
                'account': connection.account,
                'user': connection.username,
                'role': connection.role,
                'warehouse': connection.warehouse,
                'database': connection.database,
                'schema': connection.schema,
                'region': connection.region,
            }
            
            # Add authentication details
            if connection.auth_method == "password" and connection.password:
                settings['password'] = connection.password.get_secret_value()
            elif connection.auth_method == "private_key":
                settings['private_key_path'] = connection.private_key_path
                if connection.private_key_passphrase:
                    settings['private_key_passphrase'] = connection.private_key_passphrase.get_secret_value()
            
            connector = SnowflakeConnector(settings)
            result = await connector.test_connection()
            await connector.disconnect()
            
            return result
        
        elif connection.type == "postgres":
            # TODO: Implement PostgreSQL test connection
            return {
                'status': 'success',
                'message': 'PostgreSQL connection test not yet implemented'
            }
        
        else:
            return {
                'status': 'failed',
                'message': f'Connection type {connection.type} not supported'
            }
        
    except Exception as e:
        logger.error("Connection test failed", connection_name=connection.name, exc_info=e)
        return {
            'status': 'failed',
            'error': str(e),
            'message': 'Connection test failed'
        }


@router.get("/settings/auth-providers", response_model=List[AuthProviderSettings])
async def get_auth_providers() -> List[AuthProviderSettings]:
    """Get all authentication providers."""
    try:
        # TODO: Implement actual auth provider retrieval
        mock_providers = [
            AuthProviderSettings(
                name="corporate_oidc",
                type="oidc",
                issuer_url="https://auth.company.com",
                client_id="dto-app",
                scopes=["openid", "profile", "email"],
                role_mapping={
                    "data-engineers": "maintainer",
                    "data-analysts": "viewer",
                    "platform-admins": "admin"
                },
                enabled=True
            )
        ]
        
        return mock_providers
        
    except Exception as e:
        logger.error("Failed to get auth providers", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to get auth providers: {str(e)}")


@router.post("/settings/auth-providers", response_model=AuthProviderSettings)
async def create_auth_provider(provider: AuthProviderSettings) -> AuthProviderSettings:
    """Create a new authentication provider."""
    try:
        logger.info("Creating auth provider", provider_name=provider.name)
        
        # TODO: Implement actual auth provider creation
        # TODO: Validate provider configuration
        
        logger.info("Auth provider created", provider_name=provider.name)
        return provider
        
    except Exception as e:
        logger.error("Failed to create auth provider", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to create auth provider: {str(e)}")


@router.get("/settings/ai-providers", response_model=List[AIProviderSettings])
async def get_ai_providers() -> List[AIProviderSettings]:
    """Get all AI providers."""
    try:
        # TODO: Implement actual AI provider retrieval
        mock_providers = [
            AIProviderSettings(
                name="local_llm",
                type="local_llm",
                endpoint_url="http://localhost:11434",
                model_name="llama3.1:8b-instruct-q4_K_M",
                temperature=0.0,
                top_p=1.0,
                seed=42,
                timeout_seconds=30,
                enabled=True
            )
        ]
        
        return mock_providers
        
    except Exception as e:
        logger.error("Failed to get AI providers", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to get AI providers: {str(e)}")


@router.post("/settings/ai-providers", response_model=AIProviderSettings)
async def create_ai_provider(provider: AIProviderSettings) -> AIProviderSettings:
    """Create a new AI provider."""
    try:
        logger.info("Creating AI provider", provider_name=provider.name)
        
        # Enforce deterministic defaults
        provider.temperature = 0.0
        provider.top_p = 1.0
        provider.seed = 42
        
        # TODO: Implement actual AI provider creation
        # TODO: Validate provider connectivity
        
        logger.info("AI provider created", provider_name=provider.name)
        return provider
        
    except Exception as e:
        logger.error("Failed to create AI provider", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to create AI provider: {str(e)}")


@router.get("/settings/policies", response_model=PolicySettings)
async def get_policies() -> PolicySettings:
    """Get security and operational policies."""
    try:
        # TODO: Implement actual policy retrieval
        # Return secure defaults as specified in BRD
        return PolicySettings(
            # AI Policies - secure defaults
            external_ai_enabled=False,
            ai_pii_redaction=True,
            ai_prompt_logging=True,
            
            # SQL Policies - secure defaults
            sql_preview_enabled=False,
            admin_power_mode=False,
            explain_preflight=True,
            
            # Data Policies
            sample_rows_enabled=True,
            sample_row_limit=100,
            pii_redaction_enabled=True,
            
            # Execution Policies
            default_time_budget_seconds=900,  # 15 minutes
            max_time_budget_seconds=3600,    # 1 hour
            auto_sampling_threshold=1000000,
            
            # Security Policies - secure defaults
            static_secrets_forbidden=True,
            vault_required=False,
            network_isolation=True,
            
            # Retention Policies
            run_retention_days=90,
            artifact_retention_days=30
        )
        
    except Exception as e:
        logger.error("Failed to get policies", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to get policies: {str(e)}")


@router.post("/settings/policies", response_model=PolicySettings)
async def update_policies(policies: PolicySettings) -> PolicySettings:
    """Update security and operational policies."""
    try:
        logger.info("Updating policies")
        
        # TODO: Implement actual policy update
        # TODO: Validate policy changes don't compromise security
        
        logger.info("Policies updated")
        return policies
        
    except Exception as e:
        logger.error("Failed to update policies", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to update policies: {str(e)}")


@router.get("/settings", response_model=SystemSettings)
async def get_system_settings() -> SystemSettings:
    """Get all system settings."""
    try:
        # TODO: Implement actual system settings retrieval
        # For now, return defaults
        return SystemSettings(
            connections=[],
            auth_providers=[],
            ai_providers=[],
            policies=PolicySettings(),
            artifact_storage_type="local",
            artifact_storage_config={},
            run_store_url="postgresql://dto:dto@localhost:5432/dto"
        )
        
    except Exception as e:
        logger.error("Failed to get system settings", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to get system settings: {str(e)}")
