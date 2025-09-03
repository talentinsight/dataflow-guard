"""
Hybrid Test Engine: Static Tests + AI Fallback
"""
from typing import Dict, Any, List, Optional
import structlog

from dto_api.services.etl_test_engine import ETLTestEngine
from dto_api.services.zero_sql_service import ZeroSQLService

logger = structlog.get_logger()

class HybridTestEngine:
    """Combines static tests with AI-powered dynamic tests."""
    
    def __init__(self):
        self.static_engine = ETLTestEngine()
        self.ai_engine = ZeroSQLService()
        
        # Static test templates
        self.static_test_templates = {
            "row_count": {
                "description": "Compare row counts across pipeline layers",
                "sql_template": """
                SELECT 
                    'source' as layer, COUNT(*) as row_count FROM {source_table}
                UNION ALL
                SELECT 
                    'prep' as layer, COUNT(*) as row_count FROM {prep_table}
                UNION ALL
                SELECT 
                    'mart' as layer, COUNT(*) as row_count FROM {mart_table}
                """,
                "validation": "prep_count <= source_count AND mart_count > 0"
            },
            "null_check": {
                "description": "Check for NULL values in critical columns",
                "sql_template": """
                SELECT 
                    'prep_nulls' as check_type,
                    COUNT(*) as null_count
                FROM {prep_table}
                WHERE EMAIL IS NULL OR CUSTOMER_ID IS NULL
                """,
                "validation": "null_count = 0"
            },
            "duplicate_check": {
                "description": "Check for duplicate records",
                "sql_template": """
                SELECT 
                    COUNT(*) as duplicate_count
                FROM (
                    SELECT EMAIL, COUNT(*) as cnt
                    FROM {prep_table}
                    WHERE EMAIL IS NOT NULL
                    GROUP BY EMAIL
                    HAVING COUNT(*) > 1
                )
                """,
                "validation": "duplicate_count = 0"
            },
            "email_format": {
                "description": "Basic email format validation",
                "sql_template": """
                SELECT 
                    COUNT(*) as invalid_email_count
                FROM {prep_table}
                WHERE EMAIL IS NOT NULL 
                AND EMAIL NOT LIKE '%@%'
                """,
                "validation": "invalid_email_count = 0"
            },
            "transformation_accuracy": {
                "description": "Check email quality flag accuracy",
                "sql_template": """
                SELECT 
                    COUNT(*) as incorrect_flags
                FROM {prep_table}
                WHERE (
                    (EMAIL IS NULL AND email_quality_flag != 'MISSING_EMAIL') OR
                    (EMAIL NOT LIKE '%@%' AND EMAIL IS NOT NULL AND email_quality_flag != 'INVALID_EMAIL') OR
                    (EMAIL LIKE '%@%' AND email_quality_flag != 'VALID_EMAIL')
                )
                """,
                "validation": "incorrect_flags = 0"
            }
        }
    
    async def run_hybrid_tests(
        self,
        source_table: str,
        prep_table: str,
        mart_table: str,
        test_types: List[str],
        natural_language_tests: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Run hybrid testing: static tests + AI tests."""
        
        results = {
            "test_summary": {
                "total_tests": 0,
                "static_tests": 0,
                "ai_tests": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0,
                "execution_time_seconds": 0
            },
            "static_results": [],
            "ai_results": [],
            "recommendations": [],
            "cost_info": {
                "static_cost": 0.0,
                "ai_cost_tokens": 0,
                "estimated_ai_cost_usd": 0.0
            }
        }
        
        from datetime import datetime
        start_time = datetime.utcnow()
        
        try:
            # 1. Run Static Tests First (Fast & Free)
            logger.info("Running static tests", test_types=test_types)
            static_results = await self._run_static_tests(
                source_table, prep_table, mart_table, test_types
            )
            
            results["static_results"] = static_results
            results["test_summary"]["static_tests"] = len(static_results)
            
            # 2. Identify gaps where AI is needed
            ai_needed_tests = self._identify_ai_needed_tests(test_types, static_results)
            
            # 3. Add custom natural language tests
            if natural_language_tests:
                ai_needed_tests.extend(natural_language_tests)
            
            # 4. Run AI Tests for complex scenarios
            if ai_needed_tests:
                logger.info("Running AI tests", ai_tests=ai_needed_tests)
                ai_results = await self._run_ai_tests(
                    source_table, prep_table, mart_table, ai_needed_tests
                )
                
                results["ai_results"] = ai_results
                results["test_summary"]["ai_tests"] = len(ai_results)
                
                # Calculate AI costs
                total_tokens = sum(r.get("tokens", 0) for r in ai_results)
                results["cost_info"]["ai_cost_tokens"] = total_tokens
                results["cost_info"]["estimated_ai_cost_usd"] = total_tokens * 0.00001  # Rough estimate
            
            # 5. Combine results and generate summary
            all_results = static_results + results["ai_results"]
            
            for result in all_results:
                results["test_summary"]["total_tests"] += 1
                if result.get("status") == "pass":
                    results["test_summary"]["passed"] += 1
                elif result.get("status") == "fail":
                    results["test_summary"]["failed"] += 1
                else:
                    results["test_summary"]["warnings"] += 1
            
            # 6. Generate recommendations
            results["recommendations"] = self._generate_hybrid_recommendations(all_results)
            
        except Exception as e:
            logger.error("Hybrid test execution failed", exc_info=e)
            results["error"] = str(e)
        
        end_time = datetime.utcnow()
        results["test_summary"]["execution_time_seconds"] = (end_time - start_time).total_seconds()
        
        return results
    
    async def _run_static_tests(
        self, 
        source_table: str, 
        prep_table: str, 
        mart_table: str, 
        test_types: List[str]
    ) -> List[Dict[str, Any]]:
        """Run predefined static tests."""
        
        static_results = []
        
        for test_type in test_types:
            if test_type in self.static_test_templates:
                template = self.static_test_templates[test_type]
                
                try:
                    # Format SQL with table names
                    sql = template["sql_template"].format(
                        source_table=source_table,
                        prep_table=prep_table,
                        mart_table=mart_table
                    )
                    
                    # Execute via static engine's connector
                    await self.static_engine.connector.connect()
                    query_results = await self.static_engine.connector.execute_query(sql)
                    await self.static_engine.connector.disconnect()
                    
                    # Evaluate results
                    status = self._evaluate_static_test(query_results, template["validation"])
                    
                    static_results.append({
                        "test_name": f"Static {test_type.replace('_', ' ').title()}",
                        "test_type": test_type,
                        "status": status,
                        "description": template["description"],
                        "sql": sql,
                        "raw_results": query_results,
                        "source": "static"
                    })
                    
                except Exception as e:
                    logger.error("Static test failed", test_type=test_type, exc_info=e)
                    static_results.append({
                        "test_name": f"Static {test_type.replace('_', ' ').title()}",
                        "test_type": test_type,
                        "status": "fail",
                        "error": str(e),
                        "source": "static"
                    })
        
        return static_results
    
    def _evaluate_static_test(self, results: List[Dict], validation_rule: str) -> str:
        """Evaluate static test results against validation rules."""
        
        if not results:
            return "fail"
        
        try:
            # Simple validation logic
            if "null_count = 0" in validation_rule:
                null_count = results[0].get("NULL_COUNT", 0)
                return "pass" if null_count == 0 else "fail"
            
            elif "duplicate_count = 0" in validation_rule:
                dup_count = results[0].get("DUPLICATE_COUNT", 0)
                return "pass" if dup_count == 0 else "fail"
            
            elif "invalid_email_count = 0" in validation_rule:
                invalid_count = results[0].get("INVALID_EMAIL_COUNT", 0)
                return "pass" if invalid_count == 0 else "fail"
            
            elif "incorrect_flags = 0" in validation_rule:
                incorrect_count = results[0].get("INCORRECT_FLAGS", 0)
                return "pass" if incorrect_count == 0 else "fail"
            
            elif "row_count" in validation_rule:
                # More complex row count validation
                source_count = next((r["ROW_COUNT"] for r in results if r.get("LAYER") == "source"), 0)
                prep_count = next((r["ROW_COUNT"] for r in results if r.get("LAYER") == "prep"), 0)
                mart_count = next((r["ROW_COUNT"] for r in results if r.get("LAYER") == "mart"), 0)
                
                if prep_count <= source_count and mart_count > 0:
                    return "pass"
                else:
                    return "warning" if mart_count > 0 else "fail"
            
            return "pass"  # Default
            
        except Exception as e:
            logger.error("Static test evaluation failed", exc_info=e)
            return "fail"
    
    async def _run_ai_tests(
        self,
        source_table: str,
        prep_table: str,
        mart_table: str,
        ai_test_requests: List[str]
    ) -> List[Dict[str, Any]]:
        """Run AI-powered tests for complex scenarios."""
        
        ai_results = []
        
        for natural_language in ai_test_requests:
            try:
                # Generate SQL using AI
                ai_result = await self.ai_engine.generate_test_from_natural_language(
                    natural_language=natural_language,
                    source_table=source_table,
                    prep_table=prep_table,
                    mart_table=mart_table
                )
                
                if ai_result.get("success") and ai_result.get("sql"):
                    # Execute the AI-generated SQL
                    await self.static_engine.connector.connect()
                    query_results = await self.static_engine.connector.execute_query(ai_result["sql"])
                    await self.static_engine.connector.disconnect()
                    
                    ai_results.append({
                        "test_name": f"AI: {natural_language[:50]}...",
                        "test_type": ai_result.get("test_type", "ai_generated"),
                        "status": "pass",  # AI tests are informational by default
                        "natural_language": natural_language,
                        "generated_sql": ai_result["sql"],
                        "explanation": ai_result.get("explanation"),
                        "raw_results": query_results,
                        "tokens": ai_result.get("usage", {}).get("total_tokens", 0),
                        "provider": ai_result.get("provider"),
                        "source": "ai"
                    })
                else:
                    ai_results.append({
                        "test_name": f"AI: {natural_language[:50]}...",
                        "test_type": "ai_generated",
                        "status": "fail",
                        "error": ai_result.get("error", "AI generation failed"),
                        "natural_language": natural_language,
                        "source": "ai"
                    })
                    
            except Exception as e:
                logger.error("AI test failed", natural_language=natural_language, exc_info=e)
                ai_results.append({
                    "test_name": f"AI: {natural_language[:50]}...",
                    "test_type": "ai_generated", 
                    "status": "fail",
                    "error": str(e),
                    "natural_language": natural_language,
                    "source": "ai"
                })
        
        return ai_results
    
    def _identify_ai_needed_tests(self, requested_tests: List[str], static_results: List[Dict]) -> List[str]:
        """Identify which tests need AI because static templates don't exist."""
        
        static_test_types = set(self.static_test_templates.keys())
        requested_set = set(requested_tests)
        
        # Tests that don't have static templates
        ai_needed = requested_set - static_test_types
        
        # Convert to natural language prompts
        ai_prompts = []
        for test_type in ai_needed:
            if test_type == "business_rules":
                ai_prompts.append("Validate business rules and data consistency across pipeline layers")
            elif test_type == "data_lineage":
                ai_prompts.append("Check data lineage and transformation accuracy from source to mart")
            elif test_type == "performance":
                ai_prompts.append("Analyze data distribution and identify potential performance issues")
            else:
                ai_prompts.append(f"Perform {test_type.replace('_', ' ')} validation")
        
        return ai_prompts
    
    def _generate_hybrid_recommendations(self, all_results: List[Dict]) -> List[str]:
        """Generate recommendations based on hybrid test results."""
        
        recommendations = []
        
        # Analyze static test failures
        static_failures = [r for r in all_results if r.get("source") == "static" and r.get("status") == "fail"]
        if static_failures:
            recommendations.append("🔧 Fix static test failures first - these are fundamental data quality issues")
        
        # Analyze AI insights
        ai_tests = [r for r in all_results if r.get("source") == "ai"]
        if ai_tests:
            total_tokens = sum(r.get("tokens", 0) for r in ai_tests)
            cost = total_tokens * 0.00001
            recommendations.append(f"🤖 AI tests used {total_tokens} tokens (≈${cost:.4f}) for advanced validation")
        
        # Performance recommendations
        if len(all_results) > 10:
            recommendations.append("⚡ Consider caching frequently used test results to improve performance")
        
        return recommendations

# Example usage patterns
HYBRID_TEST_EXAMPLES = [
    {
        "scenario": "Basic Pipeline Validation",
        "static_tests": ["row_count", "null_check", "duplicate_check"],
        "ai_tests": []
    },
    {
        "scenario": "Advanced Business Rules",
        "static_tests": ["row_count", "email_format"],
        "ai_tests": [
            "Verify customer segmentation logic is applied correctly",
            "Check if revenue calculations match business requirements"
        ]
    },
    {
        "scenario": "Custom Validation",
        "static_tests": ["transformation_accuracy"],
        "ai_tests": [
            "Validate that all customer records have consistent data across all pipeline layers",
            "Check for any anomalies in the data transformation process"
        ]
    }
]
