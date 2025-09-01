"""Test JSON/VARIANT compilation with LATERAL FLATTEN."""

import pytest
from unittest.mock import Mock

from dto_api.services.ai_adapter_iface import AIAdapterInterface
from dto_api.models.tests import CompileRequest, IR, IRAssertion


class TestJSONVariantCompilation:
    """Test JSON/VARIANT test compilation with Snowflake LATERAL FLATTEN."""
    
    def setup_method(self):
        """Setup test AI adapter."""
        self.ai_adapter = AIAdapterInterface()
    
    def test_json_path_exists_compilation(self):
        """Test compilation of JSON path existence test."""
        # Create IR for JSON path existence test
        ir = IR(
            dataset="RAW.EVENTS",
            assertion=IRAssertion(
                kind="json_path_exists",
                left="$.id",
                right=""
            ),
            dialect="snowflake"
        )
        
        sql = self.ai_adapter._generate_json_sql(ir)
        
        # Should use GET_PATH function
        assert "GET_PATH(payload, '$.id')" in sql
        assert "path_exists_count" in sql
        assert "missing_path_count" in sql
        assert "RAW.EVENTS" in sql
    
    def test_json_array_flatten_compilation(self):
        """Test compilation of JSON array flatten cardinality test."""
        ir = IR(
            dataset="RAW.ORDERS",
            assertion=IRAssertion(
                kind="json_array_flatten",
                left="$.items",
                right=""
            ),
            dialect="snowflake"
        )
        
        sql = self.ai_adapter._generate_json_sql(ir)
        
        # Should use LATERAL FLATTEN
        assert "LATERAL FLATTEN" in sql
        assert "GET_PATH(t.payload, '$.items')" in sql
        assert "source_rows" in sql
        assert "flattened_rows" in sql
        assert "cardinality_diff" in sql
    
    def test_json_type_check_compilation(self):
        """Test compilation of JSON type check test."""
        ir = IR(
            dataset="RAW.EVENTS",
            assertion=IRAssertion(
                kind="json_type_check",
                left="$.amount",
                right={"type": "NUMBER"}
            ),
            dialect="snowflake"
        )
        
        sql = self.ai_adapter._generate_json_sql(ir)
        
        # Should use TYPEOF function
        assert "TYPEOF(GET_PATH(payload, '$.amount'))" in sql
        assert "= 'NUMBER'" in sql
        assert "correct_type_count" in sql
        assert "wrong_type_count" in sql
    
    def test_json_uniqueness_compilation(self):
        """Test compilation of JSON field uniqueness test."""
        ir = IR(
            dataset="RAW.EVENTS",
            assertion=IRAssertion(
                kind="json_uniqueness",
                left="$.user_id",
                right=""
            ),
            dialect="snowflake"
        )
        
        sql = self.ai_adapter._generate_json_sql(ir)
        
        # Should check uniqueness of JSON field
        assert "GET_PATH(payload, '$.user_id')" in sql
        assert "GROUP BY GET_PATH(payload, '$.user_id')" in sql
        assert "HAVING COUNT(*) > 1" in sql
        assert "duplicate_count" in sql
    
    def test_json_mapping_equivalence_compilation(self):
        """Test compilation of JSON mapping equivalence test."""
        ir = IR(
            dataset="PREP.ORDERS",
            assertion=IRAssertion(
                kind="json_mapping_equivalence",
                left="$.order_total",
                right={"column": "order_total"}
            ),
            dialect="snowflake"
        )
        
        sql = self.ai_adapter._generate_json_sql(ir)
        
        # Should compare PREP column with JSON path
        assert "order_total = GET_PATH(payload, '$.order_total')" in sql
        assert "matching_rows" in sql
        assert "mismatched_rows" in sql
        assert "payload IS NOT NULL AND order_total IS NOT NULL" in sql
    
    def test_json_validity_compilation(self):
        """Test compilation of default JSON validity test."""
        ir = IR(
            dataset="RAW.EVENTS",
            assertion=IRAssertion(
                kind="json_validity",
                left="",
                right=""
            ),
            dialect="snowflake"
        )
        
        sql = self.ai_adapter._generate_json_sql(ir)
        
        # Should use TRY_PARSE_JSON
        assert "TRY_PARSE_JSON(payload)" in sql
        assert "valid_json_count" in sql
        assert "invalid_json_count" in sql
    
    def test_is_json_variant_test_detection(self):
        """Test detection of JSON/VARIANT tests."""
        # JSON path in assertion
        ir_json_path = IR(
            dataset="RAW.EVENTS",
            assertion=IRAssertion(
                kind="uniqueness",
                left="$.id",
                right=""
            ),
            dialect="snowflake"
        )
        assert self.ai_adapter._is_json_variant_test(ir_json_path)
        
        # JSON in assertion kind
        ir_json_kind = IR(
            dataset="RAW.EVENTS",
            assertion=IRAssertion(
                kind="json_path_exists",
                left="id",
                right=""
            ),
            dialect="snowflake"
        )
        assert self.ai_adapter._is_json_variant_test(ir_json_kind)
        
        # VARIANT in assertion kind
        ir_variant_kind = IR(
            dataset="RAW.EVENTS",
            assertion=IRAssertion(
                kind="variant_type_check",
                left="field",
                right=""
            ),
            dialect="snowflake"
        )
        assert self.ai_adapter._is_json_variant_test(ir_variant_kind)
        
        # Regular test (not JSON/VARIANT)
        ir_regular = IR(
            dataset="RAW.EVENTS",
            assertion=IRAssertion(
                kind="uniqueness",
                left="id",
                right=""
            ),
            dialect="snowflake"
        )
        assert not self.ai_adapter._is_json_variant_test(ir_regular)
    
    async def test_compile_json_expression_integration(self):
        """Test end-to-end compilation of JSON expression."""
        request = CompileRequest(
            expression="$.items array should flatten to match item count",
            dataset="RAW.ORDERS",
            test_type="json_array_flatten"
        )
        
        # Mock the compilation to return JSON IR
        result = await self.ai_adapter.compile_expression(request)
        
        # Should return valid compile response
        assert result.ir is not None
        assert result.sql_preview is not None
        assert result.confidence > 0
        assert isinstance(result.warnings, list)
    
    def test_complex_json_flatten_sql(self):
        """Test complex JSON flatten SQL generation."""
        ir = IR(
            dataset="RAW.ORDERS",
            assertion=IRAssertion(
                kind="json_array_flatten",
                left="$.line_items",
                right=""
            ),
            dialect="snowflake"
        )
        
        sql = self.ai_adapter._generate_json_sql(ir)
        
        # Verify SQL structure
        lines = sql.split('\n')
        
        # Should have WITH clause for flattened data
        assert any('WITH flattened AS' in line for line in lines)
        
        # Should have source count CTE
        assert any('source_count AS' in line for line in lines)
        
        # Should have flattened count CTE
        assert any('flattened_count AS' in line for line in lines)
        
        # Should join the CTEs
        assert any('FROM source_count s, flattened_count f' in line for line in lines)
        
        # Should calculate difference
        assert any('ABS(s.source_rows - f.flattened_rows)' in line for line in lines)
    
    def test_json_sql_injection_protection(self):
        """Test that JSON path values are properly escaped."""
        # Test with potentially dangerous JSON path
        ir = IR(
            dataset="RAW.EVENTS",
            assertion=IRAssertion(
                kind="json_path_exists",
                left="$'; DROP TABLE orders; --",
                right=""
            ),
            dialect="snowflake"
        )
        
        sql = self.ai_adapter._generate_json_sql(ir)
        
        # The dangerous path should be treated as a literal string
        assert "DROP TABLE" in sql  # It's in the path string, but not as SQL
        assert "GET_PATH(payload, '$'; DROP TABLE orders; --')" in sql
        
        # Should not contain unescaped SQL injection
        assert sql.count("DROP TABLE") == 1  # Only in the quoted path
    
    def test_json_type_variations(self):
        """Test different JSON type checks."""
        types_to_test = ["STRING", "NUMBER", "BOOLEAN", "ARRAY", "OBJECT"]
        
        for json_type in types_to_test:
            ir = IR(
                dataset="RAW.EVENTS",
                assertion=IRAssertion(
                    kind="json_type_check",
                    left="$.field",
                    right={"type": json_type}
                ),
                dialect="snowflake"
            )
            
            sql = self.ai_adapter._generate_json_sql(ir)
            
            # Should check for the specific type
            assert f"= '{json_type}'" in sql
            assert "TYPEOF(GET_PATH(payload, '$.field'))" in sql
