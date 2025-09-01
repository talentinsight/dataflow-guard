"""Test security policies and guardrails."""

import pytest

from dto_api.adapters.connectors.snowflake_stub import SnowflakeConnector
from dto_api.adapters.connectors.postgres_stub import PostgresConnector
from dto_api.policies.pii_redaction import PIIRedactionPolicy
from dto_api.policies.sql_preview_off import SQLPreviewPolicy, SQLPreviewMode


class TestSQLValidation:
    """Test SQL validation and SELECT-only enforcement."""
    
    def test_snowflake_select_allowed(self):
        """Test that SELECT queries are allowed."""
        connector = SnowflakeConnector({"read_only": True})
        
        # These should not raise exceptions
        connector._validate_read_only_sql("SELECT * FROM orders")
        connector._validate_read_only_sql("SELECT COUNT(*) FROM orders WHERE status = 'active'")
        connector._validate_read_only_sql("WITH cte AS (SELECT * FROM orders) SELECT * FROM cte")
        connector._validate_read_only_sql("EXPLAIN SELECT * FROM orders")
    
    def test_snowflake_ddl_forbidden(self):
        """Test that DDL statements are forbidden."""
        connector = SnowflakeConnector({"read_only": True})
        
        forbidden_queries = [
            "CREATE TABLE test (id INT)",
            "DROP TABLE orders",
            "ALTER TABLE orders ADD COLUMN test VARCHAR(50)",
            "INSERT INTO orders VALUES (1, 'test')",
            "UPDATE orders SET status = 'inactive'",
            "DELETE FROM orders WHERE id = 1",
            "TRUNCATE TABLE orders",
            "MERGE INTO orders USING source ON orders.id = source.id"
        ]
        
        for query in forbidden_queries:
            with pytest.raises(ValueError, match="Forbidden SQL keyword detected|Only SELECT"):
                connector._validate_read_only_sql(query)
    
    def test_postgres_select_allowed(self):
        """Test that SELECT queries are allowed in PostgreSQL."""
        connector = PostgresConnector({"read_only": True})
        
        # These should not raise exceptions
        connector._validate_read_only_sql("SELECT * FROM orders")
        connector._validate_read_only_sql("EXPLAIN (FORMAT JSON) SELECT * FROM orders")
    
    def test_postgres_ddl_forbidden(self):
        """Test that DDL statements are forbidden in PostgreSQL."""
        connector = PostgresConnector({"read_only": True})
        
        forbidden_queries = [
            "CREATE TABLE test (id SERIAL)",
            "DROP TABLE orders",
            "INSERT INTO orders VALUES (1, 'test')",
            "UPDATE orders SET status = 'inactive'",
            "DELETE FROM orders WHERE id = 1",
            "VACUUM orders",
            "ANALYZE orders"
        ]
        
        for query in forbidden_queries:
            with pytest.raises(ValueError, match="Forbidden SQL keyword detected|Only SELECT"):
                connector._validate_read_only_sql(query)


class TestPIIRedaction:
    """Test PII redaction policies."""
    
    def test_pii_redaction_enabled(self):
        """Test PII redaction when enabled."""
        policy = PIIRedactionPolicy(enabled=True)
        
        sample_data = [
            {
                "order_id": 12345,
                "customer_email": "john.doe@example.com",
                "phone_number": "555-123-4567",
                "order_total": 100.50
            }
        ]
        
        redacted = policy.redact_sample_data(sample_data)
        
        assert len(redacted) == 1
        assert redacted[0]["order_id"] == 12345  # Non-PII preserved
        assert redacted[0]["order_total"] == 100.50  # Non-PII preserved
        assert "[REDACTED_EMAIL]" in str(redacted[0]["customer_email"])
        assert "[REDACTED_PHONE]" in str(redacted[0]["phone_number"])
    
    def test_pii_redaction_disabled(self):
        """Test PII redaction when disabled."""
        policy = PIIRedactionPolicy(enabled=False)
        
        sample_data = [
            {
                "customer_email": "john.doe@example.com",
                "phone_number": "555-123-4567"
            }
        ]
        
        redacted = policy.redact_sample_data(sample_data)
        
        # Data should be unchanged when redaction is disabled
        assert redacted == sample_data
    
    def test_pii_column_detection(self):
        """Test PII column name detection."""
        policy = PIIRedactionPolicy(enabled=True)
        
        pii_columns = ["customer_email", "phone_number", "ssn", "credit_card_number"]
        non_pii_columns = ["order_id", "order_total", "status", "created_at"]
        
        for col in pii_columns:
            assert policy._is_pii_column(col), f"Column {col} should be detected as PII"
        
        for col in non_pii_columns:
            assert not policy._is_pii_column(col), f"Column {col} should not be detected as PII"
    
    def test_ai_context_redaction(self):
        """Test AI context redaction."""
        policy = PIIRedactionPolicy(enabled=True)
        
        context = "Customer john.doe@example.com called 555-123-4567 about order"
        redacted = policy.redact_ai_context(context)
        
        assert "john.doe@example.com" not in redacted
        assert "555-123-4567" not in redacted
        assert "[REDACTED_EMAIL]" in redacted
        assert "[REDACTED_PHONE]" in redacted


class TestSQLPreviewPolicy:
    """Test SQL preview policy enforcement."""
    
    def test_sql_preview_disabled(self):
        """Test SQL preview when completely disabled."""
        policy = SQLPreviewPolicy(mode=SQLPreviewMode.DISABLED)
        
        assert not policy.can_view_sql_preview("admin")
        assert not policy.can_view_sql_preview("maintainer")
        assert not policy.can_view_sql_preview("viewer")
        
        sql = "SELECT * FROM orders"
        assert policy.sanitize_sql_for_preview(sql, "admin") is None
    
    def test_sql_preview_admin_only(self):
        """Test SQL preview in admin-only mode."""
        policy = SQLPreviewPolicy(
            mode=SQLPreviewMode.ADMIN_ONLY,
            admin_power_mode=True
        )
        
        assert policy.can_view_sql_preview("admin")
        assert not policy.can_view_sql_preview("maintainer")
        assert not policy.can_view_sql_preview("viewer")
    
    def test_sql_preview_admin_power_mode_required(self):
        """Test that admin power mode is required."""
        policy = SQLPreviewPolicy(
            mode=SQLPreviewMode.ADMIN_ONLY,
            admin_power_mode=False
        )
        
        assert not policy.can_view_sql_preview("admin")
    
    def test_admin_sql_validation(self):
        """Test admin SQL request validation."""
        policy = SQLPreviewPolicy(
            mode=SQLPreviewMode.ADMIN_ONLY,
            admin_power_mode=True
        )
        
        # Valid SELECT query
        result = policy.validate_admin_sql_request("SELECT * FROM orders", "admin")
        assert result["allowed"] is True
        
        # Invalid DDL query
        result = policy.validate_admin_sql_request("DROP TABLE orders", "admin")
        assert result["allowed"] is False
        assert "DROP" in result["reason"]
        
        # Non-admin user
        result = policy.validate_admin_sql_request("SELECT * FROM orders", "viewer")
        assert result["allowed"] is False
    
    def test_sql_sanitization(self):
        """Test SQL sanitization for preview."""
        policy = SQLPreviewPolicy(
            mode=SQLPreviewMode.ADMIN_ONLY,
            admin_power_mode=True
        )
        
        sql = "SELECT * FROM orders WHERE api_key = 'secret123'"
        sanitized = policy.sanitize_sql_for_preview(sql, "admin")
        
        assert sanitized is not None
        assert "secret123" not in sanitized
        assert "[REDACTED_KEY]" in sanitized
        assert "WARNING" in sanitized
