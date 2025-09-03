"""Test compilation service - converts test templates to SQL."""

from typing import Dict, List, Optional, Any
import structlog

logger = structlog.get_logger()


class CompileService:
    """Service for compiling test templates into executable SQL."""
    
    def __init__(self):
        pass
    
    def compile_tests(self, tests: List[Dict[str, Any]], dataset_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Compile test templates into SQL.
        
        Args:
            tests: List of test definitions with type and parameters
            dataset_hint: Optional table name hint (e.g., "SCHEMA.TABLE")
            
        Returns:
            Dict with compiled SQL blocks and metadata
        """
        try:
            logger.info("Compiling tests", test_count=len(tests), dataset=dataset_hint)
            
            compiled_tests = []
            for test in tests:
                compiled_test = self._compile_single_test(test, dataset_hint)
                compiled_tests.append(compiled_test)
            
            # Combine into a single SQL block for execution
            combined_sql = self._combine_sql_blocks(compiled_tests)
            
            return {
                "sql": combined_sql,
                "tests": compiled_tests,
                "meta": {
                    "test_count": len(tests),
                    "dataset": dataset_hint,
                    "compilation_version": "1.0"
                }
            }
            
        except Exception as e:
            logger.error("Test compilation failed", error=str(e))
            raise
    
    def _compile_single_test(self, test: Dict[str, Any], dataset_hint: Optional[str]) -> Dict[str, Any]:
        """Compile a single test template to SQL."""
        test_type = test.get("type", "row_count")
        test_name = test.get("name", f"test_{test_type}")
        
        if test_type == "row_count":
            return self._compile_row_count_test(test, dataset_hint, test_name)
        elif test_type == "schema":
            return self._compile_schema_test(test, dataset_hint, test_name)
        elif test_type == "null_check":
            return self._compile_null_check_test(test, dataset_hint, test_name)
        elif test_type == "duplicate_check":
            return self._compile_duplicate_check_test(test, dataset_hint, test_name)
        else:
            # Default to row count for unknown types
            logger.warning("Unknown test type, defaulting to row_count", test_type=test_type)
            return self._compile_row_count_test(test, dataset_hint, test_name)
    
    def _compile_row_count_test(self, test: Dict[str, Any], dataset_hint: Optional[str], test_name: str) -> Dict[str, Any]:
        """Compile row count test to SQL."""
        table = dataset_hint or test.get("dataset", "SAMPLE_TABLE")
        filter_condition = test.get("filter")
        expected_min = test.get("expected_min", 0)
        expected_max = test.get("expected_max")
        
        sql = f"SELECT COUNT(*) AS row_count FROM {table}"
        if filter_condition:
            sql += f" WHERE {filter_condition}"
        
        return {
            "name": test_name,
            "type": "row_count",
            "sql": sql,
            "expected": {
                "min_rows": expected_min,
                "max_rows": expected_max
            },
            "meta": {
                "table": table,
                "filter": filter_condition
            }
        }
    
    def _compile_schema_test(self, test: Dict[str, Any], dataset_hint: Optional[str], test_name: str) -> Dict[str, Any]:
        """Compile schema validation test to SQL."""
        table = dataset_hint or test.get("dataset", "SAMPLE_TABLE")
        expected_columns = test.get("expected_columns", [])
        
        # Parse table name for INFORMATION_SCHEMA query
        if "." in table:
            parts = table.split(".")
            if len(parts) == 3:  # DATABASE.SCHEMA.TABLE
                database, schema, table_name = parts
            else:  # SCHEMA.TABLE
                schema, table_name = parts
                database = "CURRENT_DATABASE()"
        else:
            schema = "PUBLIC"
            table_name = table
            database = "CURRENT_DATABASE()"
        
        sql = f"""
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = '{schema}' 
  AND TABLE_NAME = '{table_name}'
ORDER BY ORDINAL_POSITION
        """.strip()
        
        return {
            "name": test_name,
            "type": "schema",
            "sql": sql,
            "expected": {
                "columns": expected_columns
            },
            "meta": {
                "table": table,
                "schema": schema,
                "table_name": table_name
            }
        }
    
    def _compile_null_check_test(self, test: Dict[str, Any], dataset_hint: Optional[str], test_name: str) -> Dict[str, Any]:
        """Compile null value check test to SQL."""
        table = dataset_hint or test.get("dataset", "SAMPLE_TABLE")
        column = test.get("column", "id")
        expected_nulls = test.get("expected_nulls", 0)
        
        sql = f"SELECT COUNT(*) AS null_count FROM {table} WHERE {column} IS NULL"
        
        return {
            "name": test_name,
            "type": "null_check",
            "sql": sql,
            "expected": {
                "null_count": expected_nulls
            },
            "meta": {
                "table": table,
                "column": column
            }
        }
    
    def _compile_duplicate_check_test(self, test: Dict[str, Any], dataset_hint: Optional[str], test_name: str) -> Dict[str, Any]:
        """Compile duplicate detection test to SQL."""
        table = dataset_hint or test.get("dataset", "SAMPLE_TABLE")
        columns = test.get("columns", ["id"])
        expected_duplicates = test.get("expected_duplicates", 0)
        
        column_list = ", ".join(columns)
        sql = f"""
SELECT COUNT(*) AS duplicate_count 
FROM (
    SELECT {column_list}, COUNT(*) as cnt
    FROM {table}
    GROUP BY {column_list}
    HAVING COUNT(*) > 1
) duplicates
        """.strip()
        
        return {
            "name": test_name,
            "type": "duplicate_check",
            "sql": sql,
            "expected": {
                "duplicate_count": expected_duplicates
            },
            "meta": {
                "table": table,
                "columns": columns
            }
        }
    
    def _combine_sql_blocks(self, compiled_tests: List[Dict[str, Any]]) -> str:
        """Combine individual test SQL blocks into a single executable script."""
        sql_blocks = []
        
        sql_blocks.append("-- DataFlowGuard Test Suite")
        sql_blocks.append("-- Generated SQL for test execution")
        sql_blocks.append("")
        
        for i, test in enumerate(compiled_tests, 1):
            sql_blocks.append(f"-- Test {i}: {test['name']} ({test['type']})")
            sql_blocks.append(test['sql'] + ";")
            sql_blocks.append("")
        
        return "\n".join(sql_blocks)


# Global service instance
compile_service = CompileService()
