"""Settings and configuration models."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, SecretStr


class ConnectionSettings(BaseModel):
    """Database connection settings."""
    
    name: str = Field(..., description="Connection name")
    type: Literal["snowflake", "postgres", "bigquery", "redshift"] = Field(
        ..., description="Connection type"
    )
    host: Optional[str] = Field(None, description="Database host")
    port: Optional[int] = Field(None, description="Database port")
    database: str = Field(..., description="Database name")
    schema: Optional[str] = Field(None, description="Default schema")
    username: Optional[str] = Field(None, description="Username")
    password: Optional[SecretStr] = Field(None, description="Password (discouraged)")
    warehouse: Optional[str] = Field(None, description="Warehouse (Snowflake)")
    role: Optional[str] = Field(None, description="Role")
    auth_method: Literal["password", "iam", "oidc", "kerberos", "mtls", "vault", "private_key"] = Field(
        default="password", description="Authentication method"
    )
    connection_params: Dict[str, Any] = Field(
        default_factory=dict, description="Additional connection parameters"
    )
    read_only: bool = Field(default=True, description="Enforce read-only access")
    enabled: bool = Field(default=True, description="Whether connection is enabled")
    
    # Snowflake-specific fields
    account: Optional[str] = Field(None, description="Snowflake account identifier")
    region: Optional[str] = Field(None, description="Snowflake region")
    private_key_path: Optional[str] = Field(None, description="Path to private key file")
    private_key_passphrase: Optional[SecretStr] = Field(None, description="Private key passphrase")
    
    def mask_secrets(self) -> "ConnectionSettings":
        """Return a copy with secrets masked for API responses."""
        masked = self.model_copy()
        if masked.password:
            masked.password = SecretStr("******")
        if masked.private_key_passphrase:
            masked.private_key_passphrase = SecretStr("******")
        return masked


class AuthProviderSettings(BaseModel):
    """Authentication provider settings."""
    
    name: str = Field(..., description="Provider name")
    type: Literal["oidc", "saml", "iam", "kerberos", "mtls"] = Field(
        ..., description="Provider type"
    )
    issuer_url: Optional[str] = Field(None, description="OIDC issuer URL")
    client_id: Optional[str] = Field(None, description="OIDC client ID")
    client_secret: Optional[SecretStr] = Field(None, description="OIDC client secret")
    scopes: List[str] = Field(default_factory=list, description="Required scopes")
    role_mapping: Dict[str, str] = Field(
        default_factory=dict, description="Map provider roles to DTO roles"
    )
    enabled: bool = Field(default=True, description="Whether provider is enabled")


class PolicySettings(BaseModel):
    """Security and operational policies."""
    
    # AI Policies
    external_ai_enabled: bool = Field(default=False, description="Allow external AI providers")
    ai_pii_redaction: bool = Field(default=True, description="Redact PII in AI context")
    ai_prompt_logging: bool = Field(default=True, description="Log AI prompts for audit")
    
    # SQL Policies  
    sql_preview_enabled: bool = Field(default=False, description="Show SQL preview to users")
    admin_power_mode: bool = Field(default=False, description="Enable admin SQL preview mode")
    explain_preflight: bool = Field(default=True, description="Run EXPLAIN before execution")
    
    # Data Policies
    sample_rows_enabled: bool = Field(default=True, description="Include sample rows in reports")
    sample_row_limit: int = Field(default=100, description="Maximum sample rows")
    pii_redaction_enabled: bool = Field(default=True, description="Redact PII in samples")
    
    # Execution Policies
    default_time_budget_seconds: int = Field(default=900, description="Default time budget (15min)")
    max_time_budget_seconds: int = Field(default=3600, description="Maximum time budget (1hr)")
    auto_sampling_threshold: int = Field(default=1000000, description="Auto-sample above N rows")
    
    # Security Policies
    static_secrets_forbidden: bool = Field(default=True, description="Forbid static secrets")
    vault_required: bool = Field(default=False, description="Require Vault for secrets")
    network_isolation: bool = Field(default=True, description="Require network isolation")
    
    # Retention Policies
    run_retention_days: int = Field(default=90, description="Run data retention days")
    artifact_retention_days: int = Field(default=30, description="Artifact retention days")


class AIProviderSettings(BaseModel):
    """AI provider configuration."""
    
    name: str = Field(..., description="Provider name")
    type: Literal["local_llm", "azure_openai", "vertex_ai", "openai"] = Field(
        ..., description="Provider type"
    )
    endpoint_url: Optional[str] = Field(None, description="Provider endpoint")
    model_name: str = Field(..., description="Model name")
    api_key: Optional[SecretStr] = Field(None, description="API key")
    temperature: float = Field(default=0.0, description="Temperature for determinism")
    top_p: float = Field(default=1.0, description="Top-p setting")
    seed: int = Field(default=42, description="Random seed")
    timeout_seconds: int = Field(default=30, description="Request timeout")
    enabled: bool = Field(default=True, description="Whether provider is enabled")


class SystemSettings(BaseModel):
    """System-wide settings."""
    
    connections: List[ConnectionSettings] = Field(
        default_factory=list, description="Database connections"
    )
    auth_providers: List[AuthProviderSettings] = Field(
        default_factory=list, description="Authentication providers"
    )
    ai_providers: List[AIProviderSettings] = Field(
        default_factory=list, description="AI providers"
    )
    policies: PolicySettings = Field(
        default_factory=PolicySettings, description="Security and operational policies"
    )
    
    # Storage settings
    artifact_storage_type: Literal["s3", "gcs", "azure", "local"] = Field(
        default="local", description="Artifact storage type"
    )
    artifact_storage_config: Dict[str, Any] = Field(
        default_factory=dict, description="Storage configuration"
    )
    
    # Database settings
    run_store_url: str = Field(
        default="postgresql://dto:dto@localhost:5432/dto", 
        description="Run store database URL"
    )
