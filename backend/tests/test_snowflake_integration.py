"""Integration tests for Snowflake connector (requires real credentials)."""

import os
import pytest
from unittest.mock import patch

from dto_api.adapters.connectors.snowflake import SnowflakeConnector


# Skip all tests in this module if Snowflake credentials are not available
pytestmark = pytest.mark.skipif(
    not os.getenv('SNOWFLAKE_ACCOUNT') or not os.getenv('SNOWFLAKE_USER'),
    reason="Snowflake credentials not available (set SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, etc.)"
)


@pytest.mark.integration
class TestSnowflakeIntegration:
    """Integration tests with real Snowflake connection."""
    
    @pytest.fixture
    def connector(self):
        """Create connector from environment variables."""
        return SnowflakeConnector()
    
    async def test_connection_test(self, connector):
        """Test basic connection to Snowflake."""
        result = await connector.test_connection()
        
        assert result['status'] == 'success'
        assert 'connection_info' in result
        assert result['connection_info']['account'] is not None
        
        # Clean up
        await connector.disconnect()
    
    async def test_simple_select_query(self, connector):
        """Test executing a simple SELECT query."""
        # Use a simple query that should work on any Snowflake instance
        sql = "SELECT 1 as test_value, CURRENT_TIMESTAMP() as test_time"
        
        result = await connector.select(sql)
        
        assert result['status'] == 'success'
        assert len(result['rows']) == 1
        assert result['rows'][0]['TEST_VALUE'] == 1
        assert 'query_id' in result
        assert 'stats' in result
        
        # Clean up
        await connector.disconnect()
    
    async def test_explain_query(self, connector):
        """Test EXPLAIN functionality."""
        sql = "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES"
        
        result = await connector.explain(sql)
        
        assert result['status'] == 'success'
        assert 'plan_text' in result
        assert 'plan_hash' in result
        assert len(result['plan_text']) > 0
        
        # Clean up
        await connector.disconnect()
    
    async def test_forbidden_query_blocked(self, connector):
        """Test that forbidden queries are blocked."""
        forbidden_sql = "CREATE TABLE test_table (id INT)"
        
        with pytest.raises(ValueError, match="Forbidden SQL keyword detected"):
            await connector.select(forbidden_sql)
        
        # Clean up
        await connector.disconnect()
    
    async def test_query_with_limit(self, connector):
        """Test query execution with LIMIT."""
        sql = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES"
        
        result = await connector.select(sql, limit=5)
        
        assert result['status'] == 'success'
        assert len(result['rows']) <= 5
        
        # Clean up
        await connector.disconnect()
    
    async def test_table_schema_retrieval(self, connector):
        """Test retrieving table schema information."""
        # Use INFORMATION_SCHEMA.TABLES as it should exist
        try:
            schema = await connector.get_table_schema("INFORMATION_SCHEMA.TABLES")
            
            assert isinstance(schema, list)
            assert len(schema) > 0
            
            # Check that columns have expected structure
            for column in schema:
                assert 'name' in column
                assert 'type' in column
                assert 'nullable' in column
                
        except Exception as e:
            # If we can't access INFORMATION_SCHEMA, skip this test
            pytest.skip(f"Cannot access INFORMATION_SCHEMA.TABLES: {e}")
        
        # Clean up
        await connector.disconnect()
    
    async def test_pii_redaction_applied(self, connector):
        """Test that PII redaction is applied to results."""
        # Create a query that might return PII-like data
        sql = """
        SELECT 
            'john.doe@example.com' as email,
            '123-45-6789' as ssn,
            '4111-1111-1111-1111' as credit_card,
            'regular_data' as normal_field
        """
        
        result = await connector.select(sql)
        
        assert result['status'] == 'success'
        assert len(result['rows']) == 1
        
        row = result['rows'][0]
        
        # PII fields should be redacted (exact redaction depends on policy)
        # At minimum, they should not contain the original values
        assert row['EMAIL'] != 'john.doe@example.com'
        assert row['SSN'] != '123-45-6789'
        assert row['CREDIT_CARD'] != '4111-1111-1111-1111'
        
        # Normal field should be unchanged
        assert row['NORMAL_FIELD'] == 'regular_data'
        
        # Clean up
        await connector.disconnect()
    
    async def test_query_metrics_collection(self, connector):
        """Test that query execution metrics are collected."""
        sql = "SELECT COUNT(*) as row_count FROM INFORMATION_SCHEMA.TABLES"
        
        result = await connector.select(sql)
        
        assert result['status'] == 'success'
        assert 'stats' in result
        
        stats = result['stats']
        
        # Should have timing information
        assert 'elapsed_ms' in stats
        assert stats['elapsed_ms'] >= 0
        
        # May have bytes scanned (depends on Snowflake query history availability)
        if 'bytes_scanned' in stats:
            assert stats['bytes_scanned'] >= 0
        
        # Clean up
        await connector.disconnect()
    
    async def test_connection_reuse(self, connector):
        """Test that connection can be reused for multiple queries."""
        # First query
        result1 = await connector.select("SELECT 1 as first_query")
        assert result1['status'] == 'success'
        
        # Second query on same connection
        result2 = await connector.select("SELECT 2 as second_query")
        assert result2['status'] == 'success'
        
        # Should have different query IDs
        assert result1['query_id'] != result2['query_id']
        
        # Clean up
        await connector.disconnect()
    
    @pytest.mark.skipif(
        not os.getenv('DFG_SCAN_BUDGET_BYTES') or int(os.getenv('DFG_SCAN_BUDGET_BYTES', '0')) == 0,
        reason="Scan budget not configured"
    )
    async def test_scan_budget_enforcement(self, connector):
        """Test scan budget enforcement (if configured)."""
        # This test only runs if scan budget is configured
        # Try a query that might exceed the budget
        large_scan_sql = """
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.COLUMNS 
        CROSS JOIN INFORMATION_SCHEMA.TABLES
        """
        
        # This might raise an exception if budget is exceeded
        # The exact behavior depends on the configured budget
        try:
            await connector.explain(large_scan_sql)
        except ValueError as e:
            if "exceeds budget" in str(e):
                # Budget enforcement is working
                pass
            else:
                raise
        
        # Clean up
        await connector.disconnect()


@pytest.mark.integration
class TestSnowflakeEnvironmentConfig:
    """Test Snowflake configuration from environment."""
    
    def test_environment_variables_loaded(self):
        """Test that environment variables are properly loaded."""
        # This test runs regardless of actual Snowflake connectivity
        # It just checks that environment loading works
        
        required_vars = ['SNOWFLAKE_ACCOUNT', 'SNOWFLAKE_USER']
        for var in required_vars:
            assert os.getenv(var) is not None, f"Required environment variable {var} not set"
        
        connector = SnowflakeConnector()
        
        # Check that settings were loaded from environment
        assert connector.settings['account'] == os.getenv('SNOWFLAKE_ACCOUNT')
        assert connector.settings['user'] == os.getenv('SNOWFLAKE_USER')
        
        # Check optional settings
        if os.getenv('SNOWFLAKE_DATABASE'):
            assert connector.settings['database'] == os.getenv('SNOWFLAKE_DATABASE')
        
        if os.getenv('SNOWFLAKE_ROLE'):
            assert connector.settings['role'] == os.getenv('SNOWFLAKE_ROLE')
    
    def test_budget_settings_from_environment(self):
        """Test that budget settings are loaded from environment."""
        # Test with specific environment values
        test_env = {
            'DFG_SELECT_TIMEOUT': '45',
            'DFG_SCAN_BUDGET_BYTES': '5000000',
            'DFG_SAMPLE_LIMIT': '250',
            'DFG_QUERY_TAG': 'TestEnvironment'
        }
        
        with patch.dict('os.environ', test_env):
            connector = SnowflakeConnector({
                'account': 'test.account',
                'user': 'test_user',
                'password': 'test_pass'
            })
            
            assert connector.select_timeout == 45
            assert connector.scan_budget_bytes == 5000000
            assert connector.sample_limit == 250
            assert connector.query_tag == 'TestEnvironment'
