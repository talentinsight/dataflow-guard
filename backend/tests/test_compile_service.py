"""Unit tests for test compilation service."""

import pytest
from dto_api.services.compile_service import CompileService


class TestCompileService:
    """Test cases for CompileService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = CompileService()
    
    def test_compile_row_count_test(self):
        """Test row count test compilation."""
        tests = [{
            "name": "orders_count",
            "type": "row_count",
            "dataset": "RAW.ORDERS",
            "expected_min": 1000,
            "expected_max": 10000
        }]
        
        result = self.service.compile_tests(tests)
        
        assert result["meta"]["test_count"] == 1
        assert len(result["tests"]) == 1
        
        compiled_test = result["tests"][0]
        assert compiled_test["name"] == "orders_count"
        assert compiled_test["type"] == "row_count"
        assert "SELECT COUNT(*) AS row_count FROM RAW.ORDERS" in compiled_test["sql"]
        assert compiled_test["expected"]["min_rows"] == 1000
        assert compiled_test["expected"]["max_rows"] == 10000
    
    def test_compile_row_count_with_filter(self):
        """Test row count test with WHERE filter."""
        tests = [{
            "name": "active_orders",
            "type": "row_count",
            "dataset": "RAW.ORDERS",
            "filter": "status = 'ACTIVE'",
            "expected_min": 100
        }]
        
        result = self.service.compile_tests(tests)
        compiled_test = result["tests"][0]
        
        expected_sql = "SELECT COUNT(*) AS row_count FROM RAW.ORDERS WHERE status = 'ACTIVE'"
        assert compiled_test["sql"] == expected_sql
    
    def test_compile_schema_test(self):
        """Test schema validation test compilation."""
        tests = [{
            "name": "orders_schema",
            "type": "schema",
            "dataset": "RAW.ORDERS",
            "expected_columns": [
                {"name": "ORDER_ID", "type": "NUMBER"},
                {"name": "CUSTOMER_ID", "type": "NUMBER"}
            ]
        }]
        
        result = self.service.compile_tests(tests)
        compiled_test = result["tests"][0]
        
        assert compiled_test["type"] == "schema"
        assert "INFORMATION_SCHEMA.COLUMNS" in compiled_test["sql"]
        assert "TABLE_NAME = 'ORDERS'" in compiled_test["sql"]
        assert compiled_test["expected"]["columns"] == tests[0]["expected_columns"]
    
    def test_compile_null_check_test(self):
        """Test null value check compilation."""
        tests = [{
            "name": "order_id_nulls",
            "type": "null_check",
            "dataset": "RAW.ORDERS",
            "column": "ORDER_ID",
            "expected_nulls": 0
        }]
        
        result = self.service.compile_tests(tests)
        compiled_test = result["tests"][0]
        
        assert compiled_test["type"] == "null_check"
        assert "SELECT COUNT(*) AS null_count FROM RAW.ORDERS WHERE ORDER_ID IS NULL" in compiled_test["sql"]
        assert compiled_test["expected"]["null_count"] == 0
    
    def test_compile_duplicate_check_test(self):
        """Test duplicate detection compilation."""
        tests = [{
            "name": "order_id_duplicates",
            "type": "duplicate_check",
            "dataset": "RAW.ORDERS",
            "columns": ["ORDER_ID"],
            "expected_duplicates": 0
        }]
        
        result = self.service.compile_tests(tests)
        compiled_test = result["tests"][0]
        
        assert compiled_test["type"] == "duplicate_check"
        assert "GROUP BY ORDER_ID" in compiled_test["sql"]
        assert "HAVING COUNT(*) > 1" in compiled_test["sql"]
        assert compiled_test["expected"]["duplicate_count"] == 0
    
    def test_compile_multiple_tests(self):
        """Test compilation of multiple tests."""
        tests = [
            {
                "name": "row_count_test",
                "type": "row_count",
                "dataset": "RAW.ORDERS",
                "expected_min": 1000
            },
            {
                "name": "schema_test",
                "type": "schema",
                "dataset": "RAW.ORDERS",
                "expected_columns": []
            }
        ]
        
        result = self.service.compile_tests(tests)
        
        assert result["meta"]["test_count"] == 2
        assert len(result["tests"]) == 2
        assert result["tests"][0]["name"] == "row_count_test"
        assert result["tests"][1]["name"] == "schema_test"
        
        # Check combined SQL contains both tests
        combined_sql = result["sql"]
        assert "Test 1: row_count_test" in combined_sql
        assert "Test 2: schema_test" in combined_sql
    
    def test_compile_with_dataset_hint(self):
        """Test compilation with dataset hint override."""
        tests = [{
            "name": "test1",
            "type": "row_count"
        }]
        
        result = self.service.compile_tests(tests, dataset_hint="PROD.CUSTOMERS")
        compiled_test = result["tests"][0]
        
        assert "FROM PROD.CUSTOMERS" in compiled_test["sql"]
        assert compiled_test["meta"]["table"] == "PROD.CUSTOMERS"
    
    def test_compile_unknown_test_type(self):
        """Test compilation with unknown test type defaults to row_count."""
        tests = [{
            "name": "unknown_test",
            "type": "unknown_type",
            "dataset": "RAW.ORDERS"
        }]
        
        result = self.service.compile_tests(tests)
        compiled_test = result["tests"][0]
        
        # Should default to row_count behavior
        assert compiled_test["type"] == "row_count"
        assert "SELECT COUNT(*) AS row_count" in compiled_test["sql"]
    
    def test_compile_empty_tests(self):
        """Test compilation with empty test list."""
        result = self.service.compile_tests([])
        
        assert result["meta"]["test_count"] == 0
        assert len(result["tests"]) == 0
        assert result["sql"] == "-- DataFlowGuard Test Suite\n-- Generated SQL for test execution\n"
    
    def test_schema_test_with_database_schema_table(self):
        """Test schema test with full database.schema.table format."""
        tests = [{
            "name": "full_path_schema",
            "type": "schema",
            "dataset": "PROD.RAW.ORDERS"
        }]
        
        result = self.service.compile_tests(tests)
        compiled_test = result["tests"][0]
        
        assert "TABLE_SCHEMA = 'RAW'" in compiled_test["sql"]
        assert "TABLE_NAME = 'ORDERS'" in compiled_test["sql"]
        assert compiled_test["meta"]["schema"] == "RAW"
        assert compiled_test["meta"]["table_name"] == "ORDERS"
