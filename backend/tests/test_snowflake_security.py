"""Test Snowflake security and SQL validation."""

import pytest
from unittest.mock import Mock, patch

from dto_api.adapters.connectors.snowflake import SnowflakeConnector


class TestSnowflakeSQLValidation:
    """Test SQL validation and security controls."""
    
    def setup_method(self):
        """Setup test connector."""
        self.connector = SnowflakeConnector({
            'account': 'test.region',
            'user': 'test_user',
            'password': 'test_pass',
            'database': 'TEST_DB',
            'schema': 'TEST_SCHEMA'
        })
    
    def test_select_allowed(self):
        """Test that SELECT queries are allowed."""
        valid_queries = [
            "SELECT * FROM orders",
            "SELECT COUNT(*) FROM orders WHERE status = 'active'",
            "WITH cte AS (SELECT * FROM orders) SELECT * FROM cte",
            "EXPLAIN SELECT * FROM orders",
            "  SELECT   *   FROM   orders  ",  # whitespace variations
        ]
        
        for query in valid_queries:
            # Should not raise exception
            self.connector._validate_sql(query)
    
    def test_ddl_dml_forbidden(self):
        """Test that DDL/DML statements are forbidden."""
        forbidden_queries = [
            "INSERT INTO orders VALUES (1, 'test')",
            "UPDATE orders SET status = 'inactive'",
            "DELETE FROM orders WHERE id = 1",
            "MERGE INTO orders USING source ON orders.id = source.id",
            "CREATE TABLE test (id INT)",
            "DROP TABLE orders",
            "ALTER TABLE orders ADD COLUMN test VARCHAR(50)",
            "TRUNCATE TABLE orders",
            "GRANT SELECT ON orders TO role",
            "REVOKE SELECT ON orders FROM role",
            "CALL procedure()",
            "USE DATABASE test",
            "COPY INTO orders FROM @stage",
            "PUT file:///tmp/data.csv @stage",
            "GET @stage/data.csv file:///tmp/",
            "BEGIN TRANSACTION",
            "COMMIT",
            "ROLLBACK",
            "SET SESSION query_tag = 'test'",
            "UNSET SESSION query_tag",
        ]
        
        for query in forbidden_queries:
            with pytest.raises(ValueError, match="Forbidden SQL keyword detected|Only SELECT"):
                self.connector._validate_sql(query)
    
    def test_multi_statement_forbidden(self):
        """Test that multi-statement queries are forbidden."""
        multi_statements = [
            "SELECT * FROM orders; SELECT * FROM customers;",
            "SELECT 1; DROP TABLE orders;",
            "SELECT * FROM orders;\n\nSELECT * FROM products;",
        ]
        
        for query in multi_statements:
            with pytest.raises(ValueError, match="Only single statements are allowed"):
                self.connector._validate_sql(query)
    
    def test_comments_ignored(self):
        """Test that SQL comments are properly ignored in validation."""
        queries_with_comments = [
            "-- This is a comment\nSELECT * FROM orders",
            "SELECT * FROM orders -- inline comment",
            "/* Multi-line\n   comment */ SELECT * FROM orders",
            "SELECT * FROM orders /* inline block comment */",
        ]
        
        for query in queries_with_comments:
            # Should not raise exception
            self.connector._validate_sql(query)
    
    def test_case_insensitive_validation(self):
        """Test that validation is case insensitive."""
        # These should be forbidden regardless of case
        forbidden_cases = [
            "insert into orders values (1)",
            "Insert Into orders Values (1)",
            "INSERT into ORDERS values (1)",
            "delete from orders",
            "Delete From Orders",
            "DELETE FROM ORDERS",
        ]
        
        for query in forbidden_cases:
            with pytest.raises(ValueError, match="Forbidden SQL keyword detected"):
                self.connector._validate_sql(query)
    
    def test_allowed_schema_validation(self):
        """Test schema access validation."""
        # Setup connector with allowed schemas
        connector = SnowflakeConnector({
            'account': 'test.region',
            'user': 'test_user',
            'password': 'test_pass',
            'database': 'TEST_DB',
            'schema': 'TEST_SCHEMA'
        })
        connector.allowed_schemas = ['PROD_DB.RAW', 'PROD_DB.PREP']
        
        # Allowed queries
        allowed_queries = [
            "SELECT * FROM PROD_DB.RAW.ORDERS",
            "SELECT * FROM PROD_DB.PREP.ORDERS",
            "SELECT * FROM PROD_DB.RAW.CUSTOMERS c JOIN PROD_DB.PREP.ORDERS o ON c.id = o.customer_id",
        ]
        
        for query in allowed_queries:
            # Should not raise exception
            connector._validate_sql(query)
        
        # Forbidden queries (accessing non-allowed schemas)
        forbidden_queries = [
            "SELECT * FROM PROD_DB.MART.ORDERS",
            "SELECT * FROM OTHER_DB.RAW.ORDERS",
            "SELECT * FROM PROD_DB.RAW.ORDERS o JOIN PROD_DB.MART.SUMMARY s ON o.id = s.order_id",
        ]
        
        for query in forbidden_queries:
            with pytest.raises(ValueError, match="Access to schema .* is not allowed"):
                connector._validate_sql(query)
    
    def test_empty_allowed_schemas(self):
        """Test that empty allowed schemas list allows all schemas."""
        connector = SnowflakeConnector({
            'account': 'test.region',
            'user': 'test_user',
            'password': 'test_pass',
            'database': 'TEST_DB',
            'schema': 'TEST_SCHEMA'
        })
        connector.allowed_schemas = []
        
        # Should allow any schema when list is empty
        query = "SELECT * FROM ANY_DB.ANY_SCHEMA.ANY_TABLE"
        connector._validate_sql(query)  # Should not raise exception


class TestSnowflakeConnection:
    """Test Snowflake connection and authentication."""
    
    def test_missing_required_settings(self):
        """Test that missing required settings raise ValueError."""
        with pytest.raises(ValueError, match="Missing required Snowflake settings"):
            SnowflakeConnector({})
        
        with pytest.raises(ValueError, match="Missing required Snowflake settings"):
            SnowflakeConnector({'account': 'test'})  # missing user
    
    def test_missing_auth_method(self):
        """Test that missing authentication method raises ValueError."""
        with pytest.raises(ValueError, match="Must provide either password or private_key_path"):
            SnowflakeConnector({
                'account': 'test.region',
                'user': 'test_user'
                # No password or private_key_path
            })
    
    def test_valid_password_auth(self):
        """Test valid password authentication settings."""
        # Should not raise exception
        connector = SnowflakeConnector({
            'account': 'test.region',
            'user': 'test_user',
            'password': 'test_pass'
        })
        assert connector.settings['password'] == 'test_pass'
    
    def test_valid_private_key_auth(self):
        """Test valid private key authentication settings."""
        # Should not raise exception
        connector = SnowflakeConnector({
            'account': 'test.region',
            'user': 'test_user',
            'private_key_path': '/path/to/key.pem'
        })
        assert connector.settings['private_key_path'] == '/path/to/key.pem'
    
    def test_environment_variable_loading(self):
        """Test loading settings from environment variables."""
        with patch.dict('os.environ', {
            'SNOWFLAKE_ACCOUNT': 'env.account',
            'SNOWFLAKE_USER': 'env_user',
            'SNOWFLAKE_PASSWORD': 'env_pass',
            'SNOWFLAKE_DATABASE': 'ENV_DB',
            'SNOWFLAKE_ROLE': 'ENV_ROLE'
        }):
            connector = SnowflakeConnector()
            
            assert connector.settings['account'] == 'env.account'
            assert connector.settings['user'] == 'env_user'
            assert connector.settings['password'] == 'env_pass'
            assert connector.settings['database'] == 'ENV_DB'
            assert connector.settings['role'] == 'ENV_ROLE'
    
    def test_settings_override_environment(self):
        """Test that explicit settings override environment variables."""
        with patch.dict('os.environ', {
            'SNOWFLAKE_ACCOUNT': 'env.account',
            'SNOWFLAKE_USER': 'env_user',
        }):
            connector = SnowflakeConnector({
                'account': 'override.account',
                'user': 'override_user',
                'password': 'override_pass'
            })
            
            assert connector.settings['account'] == 'override.account'
            assert connector.settings['user'] == 'override_user'
            assert connector.settings['password'] == 'override_pass'


class TestSnowflakeBudgetControls:
    """Test budget and safety controls."""
    
    def setup_method(self):
        """Setup test connector with budget controls."""
        with patch.dict('os.environ', {
            'DFG_SELECT_TIMEOUT': '30',
            'DFG_SCAN_BUDGET_BYTES': '1000000',
            'DFG_SAMPLE_LIMIT': '500',
            'DFG_QUERY_TAG': 'TestTag'
        }):
            self.connector = SnowflakeConnector({
                'account': 'test.region',
                'user': 'test_user',
                'password': 'test_pass'
            })
    
    def test_budget_settings_loaded(self):
        """Test that budget settings are loaded from environment."""
        assert self.connector.select_timeout == 30
        assert self.connector.scan_budget_bytes == 1000000
        assert self.connector.sample_limit == 500
        assert self.connector.query_tag == 'TestTag'
    
    def test_scan_budget_estimation(self):
        """Test scan budget estimation from execution plan."""
        plan_text = """
        GlobalStats
        partitionsTotal=1
        partitionsAssigned=1
        bytesAssigned=2500000
        
        TableScan
        table=ORDERS
        bytes=2500000 MB
        """
        
        estimated = self.connector._estimate_scan_bytes(plan_text)
        # Should detect the bytes value
        assert estimated > 0
    
    def test_default_budget_settings(self):
        """Test default budget settings when environment variables are not set."""
        with patch.dict('os.environ', {}, clear=True):
            connector = SnowflakeConnector({
                'account': 'test.region',
                'user': 'test_user',
                'password': 'test_pass'
            })
            
            assert connector.select_timeout == 60  # default
            assert connector.scan_budget_bytes == 0  # disabled by default
            assert connector.sample_limit == 1000  # default
            assert connector.query_tag == 'DataFlowGuard'  # default
