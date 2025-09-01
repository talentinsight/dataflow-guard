"""AI Adapter Interface - stub implementation for test compilation."""

import json
from typing import Dict, Any, List

import structlog

from dto_api.models.tests import (
    CompileRequest,
    CompileResponse,
    IR,
    IRAssertion,
    IRFilter
)

logger = structlog.get_logger()


class AIAdapterInterface:
    """AI Adapter interface for compiling NL/Formula to IR and SQL."""
    
    def __init__(self):
        # TODO: Initialize actual AI provider connection
        self.model_name = "local-llm:Q4_K_M"
        self.temperature = 0.0
        self.top_p = 1.0
        self.seed = 42
    
    async def compile_expression(self, request: CompileRequest) -> CompileResponse:
        """Compile natural language or formula expression to IR and SQL."""
        try:
            logger.info(
                "Compiling expression with AI",
                expression_length=len(request.expression),
                dataset=request.dataset,
                test_type=request.test_type
            )
            
            # TODO: Implement actual AI compilation
            # For now, return mock IR based on expression patterns
            ir = await self._mock_compile(request)
            
            # Generate SQL preview (stub)
            sql_preview = await self._generate_sql_preview(ir)
            
            # Mock confidence score
            confidence = 0.85
            
            warnings = []
            if "complex" in request.expression.lower():
                warnings.append("Complex expression detected - please review generated SQL")
            
            logger.info(
                "Expression compilation completed",
                confidence=confidence,
                warnings_count=len(warnings)
            )
            
            return CompileResponse(
                ir=ir,
                sql_preview=sql_preview,
                confidence=confidence,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error("AI compilation failed", exc_info=e)
            raise
    
    async def _mock_compile(self, request: CompileRequest) -> IR:
        """Mock compilation logic based on expression patterns."""
        expression = request.expression.lower()
        
        # Detect test type from expression if not provided
        if not request.test_type:
            if "unique" in expression or "duplicate" in expression:
                test_type = "uniqueness"
            elif "null" in expression or "missing" in expression:
                test_type = "not_null"
            elif "count" in expression or "rows" in expression:
                test_type = "row_count"
            elif "fresh" in expression or "recent" in expression:
                test_type = "freshness"
            elif "==" in expression or "equals" in expression:
                test_type = "rule"
            else:
                test_type = "rule"
        else:
            test_type = request.test_type
        
        # Create mock IR based on test type
        if test_type == "uniqueness":
            assertion = IRAssertion(
                kind="uniqueness",
                left="ORDER_ID",
                right="",
                tolerance={"dup_rows": 0}
            )
        elif test_type == "not_null":
            assertion = IRAssertion(
                kind="not_null",
                left="ORDER_ID",
                right=""
            )
        elif test_type == "row_count":
            assertion = IRAssertion(
                kind="row_count_range",
                left="COUNT(*)",
                right={"min": 1000, "max": 1000000}
            )
        elif test_type == "freshness":
            assertion = IRAssertion(
                kind="freshness",
                left="MAX(ORDER_TS)",
                right="CURRENT_TIMESTAMP()",
                tolerance={"hours": 24}
            )
        else:  # rule
            assertion = IRAssertion(
                kind="equality_with_tolerance",
                left="ORDER_TOTAL",
                right={"expr": "ITEMS_TOTAL + TAX + SHIPPING"},
                tolerance={"abs": 0.01}
            )
        
        # Add filters if expression mentions time windows
        filters = []
        if "last" in expression and "days" in expression:
            filters.append(IRFilter(
                type="time_window",
                column="ORDER_TS",
                value=30,
                operator="last_days"
            ))
        
        return IR(
            dataset=request.dataset,
            filters=filters,
            joins=[],
            aggregations=[],
            assertion=assertion,
            partition_by=[],
            dialect="snowflake"  # Default dialect
        )
    
    async def _generate_sql_preview(self, ir: IR) -> str:
        """Generate SQL preview from IR with Snowflake LATERAL FLATTEN support."""
        # Check if this is a JSON/VARIANT test requiring FLATTEN
        is_json_test = self._is_json_variant_test(ir)
        
        if is_json_test:
            return self._generate_json_sql(ir)
        
        # Regular SQL generation
        if ir.assertion.kind == "uniqueness":
            sql = f"""
-- Uniqueness test for {ir.dataset}
SELECT 
    {ir.assertion.left},
    COUNT(*) as duplicate_count
FROM {ir.dataset}
WHERE 1=1
GROUP BY {ir.assertion.left}
HAVING COUNT(*) > 1
LIMIT 100;
"""
        elif ir.assertion.kind == "not_null":
            sql = f"""
-- Not null test for {ir.dataset}
SELECT COUNT(*) as null_count
FROM {ir.dataset}
WHERE {ir.assertion.left} IS NULL;
"""
        elif ir.assertion.kind == "row_count_range":
            sql = f"""
-- Row count test for {ir.dataset}
SELECT COUNT(*) as row_count
FROM {ir.dataset};
"""
        elif ir.assertion.kind == "freshness":
            sql = f"""
-- Freshness test for {ir.dataset}
SELECT 
    {ir.assertion.left} as max_timestamp,
    CURRENT_TIMESTAMP() as current_timestamp,
    DATEDIFF('hour', {ir.assertion.left}, CURRENT_TIMESTAMP()) as hours_lag
FROM {ir.dataset};
"""
        else:  # equality_with_tolerance
            sql = f"""
-- Business rule test for {ir.dataset}
SELECT 
    COUNT(*) as violation_count,
    AVG(ABS({ir.assertion.left} - ({ir.assertion.right['expr']}))) as avg_difference
FROM {ir.dataset}
WHERE ABS({ir.assertion.left} - ({ir.assertion.right['expr']})) > {ir.assertion.tolerance.get('abs', 0.01)};
"""
        
        return sql.strip()
    
    def _is_json_variant_test(self, ir: IR) -> bool:
        """Check if this test requires JSON/VARIANT processing."""
        # Look for JSON path expressions in assertion
        assertion_str = str(ir.assertion.left) + str(ir.assertion.right)
        return '$.' in assertion_str or 'json' in ir.assertion.kind.lower() or 'variant' in ir.assertion.kind.lower()
    
    def _generate_json_sql(self, ir: IR) -> str:
        """Generate Snowflake SQL with LATERAL FLATTEN for JSON/VARIANT tests."""
        if ir.assertion.kind == "json_path_exists":
            # Test if JSON path exists
            json_path = ir.assertion.left  # e.g., "$.id"
            sql = f"""
-- JSON path existence test for {ir.dataset}
SELECT 
    COUNT(*) as total_rows,
    COUNT(GET_PATH(payload, '{json_path}')) as path_exists_count,
    COUNT(*) - COUNT(GET_PATH(payload, '{json_path}')) as missing_path_count
FROM {ir.dataset}
WHERE payload IS NOT NULL;
"""
        
        elif ir.assertion.kind == "json_array_flatten":
            # Test array flattening cardinality
            array_path = ir.assertion.left  # e.g., "$.items"
            sql = f"""
-- JSON array flatten cardinality test for {ir.dataset}
WITH flattened AS (
    SELECT 
        t.id,
        f.value as item
    FROM {ir.dataset} t,
    LATERAL FLATTEN(input => GET_PATH(t.payload, '{array_path}')) f
),
source_count AS (
    SELECT COUNT(*) as source_rows FROM {ir.dataset}
),
flattened_count AS (
    SELECT COUNT(*) as flattened_rows FROM flattened
)
SELECT 
    s.source_rows,
    f.flattened_rows,
    ABS(s.source_rows - f.flattened_rows) as cardinality_diff
FROM source_count s, flattened_count f;
"""
        
        elif ir.assertion.kind == "json_type_check":
            # Test JSON field type
            json_path = ir.assertion.left
            expected_type = ir.assertion.right.get('type', 'STRING')
            sql = f"""
-- JSON type check test for {ir.dataset}
SELECT 
    COUNT(*) as total_rows,
    COUNT(CASE WHEN TYPEOF(GET_PATH(payload, '{json_path}')) = '{expected_type}' THEN 1 END) as correct_type_count,
    COUNT(CASE WHEN TYPEOF(GET_PATH(payload, '{json_path}')) != '{expected_type}' THEN 1 END) as wrong_type_count
FROM {ir.dataset}
WHERE GET_PATH(payload, '{json_path}') IS NOT NULL;
"""
        
        elif ir.assertion.kind == "json_uniqueness":
            # Test uniqueness of JSON field
            json_path = ir.assertion.left
            sql = f"""
-- JSON field uniqueness test for {ir.dataset}
SELECT 
    GET_PATH(payload, '{json_path}') as json_value,
    COUNT(*) as duplicate_count
FROM {ir.dataset}
WHERE GET_PATH(payload, '{json_path}') IS NOT NULL
GROUP BY GET_PATH(payload, '{json_path}')
HAVING COUNT(*) > 1
LIMIT 100;
"""
        
        elif ir.assertion.kind == "json_mapping_equivalence":
            # Test that PREP columns match JSON paths
            json_path = ir.assertion.left
            prep_column = ir.assertion.right.get('column', 'mapped_field')
            sql = f"""
-- JSON mapping equivalence test for {ir.dataset}
SELECT 
    COUNT(*) as total_rows,
    COUNT(CASE WHEN {prep_column} = GET_PATH(payload, '{json_path}') THEN 1 END) as matching_rows,
    COUNT(CASE WHEN {prep_column} != GET_PATH(payload, '{json_path}') THEN 1 END) as mismatched_rows
FROM {ir.dataset}
WHERE payload IS NOT NULL AND {prep_column} IS NOT NULL;
"""
        
        else:
            # Default JSON validation
            sql = f"""
-- JSON validity test for {ir.dataset}
SELECT 
    COUNT(*) as total_rows,
    COUNT(CASE WHEN TRY_PARSE_JSON(payload) IS NOT NULL THEN 1 END) as valid_json_count,
    COUNT(CASE WHEN TRY_PARSE_JSON(payload) IS NULL THEN 1 END) as invalid_json_count
FROM {ir.dataset}
WHERE payload IS NOT NULL;
"""
        
        return sql.strip()
    
    async def explain_failure(self, test_result: Dict[str, Any]) -> str:
        """Generate explanation for test failure (stub)."""
        # TODO: Implement actual AI-powered failure explanation
        return f"Test failed with {test_result.get('violations', 0)} violations. Review the sample data for patterns."
    
    async def propose_tolerance(self, dataset: str, test_type: str, historical_data: Dict[str, Any]) -> Dict[str, float]:
        """Propose tolerance values based on historical data (stub)."""
        # TODO: Implement AI-powered tolerance suggestion
        if test_type == "rule":
            return {"abs": 0.01, "pct": 0.1}
        elif test_type == "row_count":
            return {"pct": 5.0}
        else:
            return {}
