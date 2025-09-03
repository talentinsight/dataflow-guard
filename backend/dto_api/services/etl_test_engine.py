"""
Real ETL Test Engine - Comprehensive Pipeline Validation
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
import structlog

from dto_api.adapters.connectors.snowflake import SnowflakeConnector

logger = structlog.get_logger()

class ETLTestEngine:
    """Comprehensive ETL pipeline testing engine with real business logic."""
    
    def __init__(self):
        self.connector = SnowflakeConnector()
        
    async def run_comprehensive_tests(self, 
                                    source_table: str, 
                                    prep_table: str, 
                                    mart_table: str,
                                    test_types: List[str]) -> Dict[str, Any]:
        """Run comprehensive ETL pipeline tests."""
        
        results = {
            "test_summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0,
                "execution_time_seconds": 0
            },
            "test_results": [],
            "data_quality_score": 0.0,
            "recommendations": []
        }
        
        start_time = datetime.utcnow()
        
        try:
            await self.connector.connect()
            
            # 1. Row Count & Data Volume Tests
            if 'row_count' in test_types:
                row_test = await self._test_row_count_validation(source_table, prep_table, mart_table)
                results["test_results"].append(row_test)
                results["test_summary"]["total_tests"] += 1
                if row_test["status"] == "pass":
                    results["test_summary"]["passed"] += 1
                else:
                    results["test_summary"]["failed"] += 1
            
            # 2. Data Quality & Integrity Tests  
            if 'data_quality' in test_types:
                quality_test = await self._test_data_quality(source_table, prep_table, mart_table)
                results["test_results"].append(quality_test)
                results["test_summary"]["total_tests"] += 1
                if quality_test["status"] == "pass":
                    results["test_summary"]["passed"] += 1
                else:
                    results["test_summary"]["failed"] += 1
            
            # 3. Transformation Logic Validation
            if 'transformation_validation' in test_types:
                transform_test = await self._test_transformation_logic(source_table, prep_table, mart_table)
                results["test_results"].append(transform_test)
                results["test_summary"]["total_tests"] += 1
                if transform_test["status"] == "pass":
                    results["test_summary"]["passed"] += 1
                else:
                    results["test_summary"]["failed"] += 1
            
            # 4. Business Rule Compliance
            if 'business_rules' in test_types:
                business_test = await self._test_business_rules(source_table, prep_table, mart_table)
                results["test_results"].append(business_test)
                results["test_summary"]["total_tests"] += 1
                if business_test["status"] == "pass":
                    results["test_summary"]["passed"] += 1
                else:
                    results["test_summary"]["failed"] += 1
            
            # Calculate overall data quality score
            if results["test_summary"]["total_tests"] > 0:
                results["data_quality_score"] = round(
                    (results["test_summary"]["passed"] / results["test_summary"]["total_tests"]) * 100, 2
                )
            
            # Generate recommendations
            results["recommendations"] = self._generate_recommendations(results["test_results"])
            
        except Exception as e:
            logger.error("ETL test execution failed", exc_info=e)
            results["error"] = str(e)
        finally:
            await self.connector.disconnect()
            
        end_time = datetime.utcnow()
        results["test_summary"]["execution_time_seconds"] = (end_time - start_time).total_seconds()
        
        return results
    
    async def _test_row_count_validation(self, source_table: str, prep_table: str, mart_table: str) -> Dict[str, Any]:
        """Test row count consistency across pipeline layers."""
        
        sql = f"""
        SELECT 
            'source' as layer, 
            COUNT(*) as row_count,
            COUNT(DISTINCT CUSTOMER_ID) as unique_customers
        FROM {source_table}
        
        UNION ALL
        
        SELECT 
            'prep' as layer,
            COUNT(*) as row_count, 
            COUNT(DISTINCT CUSTOMER_ID) as unique_customers
        FROM {prep_table}
        
        UNION ALL
        
        SELECT 
            'mart' as layer,
            COUNT(*) as row_count,
            COUNT(DISTINCT email_quality_flag) as unique_customers  -- Different aggregation
        FROM {mart_table}
        """
        
        results = await self.connector.execute_query(sql)
        
        # Analyze results
        source_count = next((r['ROW_COUNT'] for r in results if r['LAYER'] == 'source'), 0)
        prep_count = next((r['ROW_COUNT'] for r in results if r['LAYER'] == 'prep'), 0)
        mart_count = next((r['ROW_COUNT'] for r in results if r['LAYER'] == 'mart'), 0)
        
        # Business rules: PREP should have <= SOURCE (filtering), MART should be aggregated
        prep_loss_rate = ((source_count - prep_count) / source_count * 100) if source_count > 0 else 0
        
        status = "pass"
        issues = []
        
        if prep_count > source_count:
            status = "fail"
            issues.append("PREP layer has more rows than SOURCE - possible data duplication")
        
        if prep_loss_rate > 50:
            status = "warning" if status == "pass" else status
            issues.append(f"High data loss in PREP layer: {prep_loss_rate:.1f}%")
        
        if mart_count == 0:
            status = "fail"
            issues.append("MART layer is empty")
        
        return {
            "test_name": "Row Count Validation",
            "test_type": "row_count",
            "status": status,
            "metrics": {
                "source_rows": source_count,
                "prep_rows": prep_count, 
                "mart_rows": mart_count,
                "prep_loss_rate_percent": round(prep_loss_rate, 2)
            },
            "issues": issues,
            "raw_data": results
        }
    
    async def _test_data_quality(self, source_table: str, prep_table: str, mart_table: str) -> Dict[str, Any]:
        """Test data quality metrics across pipeline."""
        
        sql = f"""
        SELECT 
            'prep_nulls' as check_type,
            COUNT(*) as total_rows,
            COUNT(CASE WHEN EMAIL IS NULL THEN 1 END) as null_emails,
            COUNT(CASE WHEN CUSTOMER_ID IS NULL THEN 1 END) as null_ids,
            COUNT(CASE WHEN EMAIL NOT LIKE '%@%' AND EMAIL IS NOT NULL THEN 1 END) as invalid_emails
        FROM {prep_table}
        
        UNION ALL
        
        SELECT 
            'mart_quality' as check_type,
            COUNT(*) as total_rows,
            COUNT(CASE WHEN customer_count <= 0 THEN 1 END) as zero_counts,
            0 as null_ids,
            0 as invalid_emails
        FROM {mart_table}
        """
        
        results = await self.connector.execute_query(sql)
        
        prep_data = next((r for r in results if r['CHECK_TYPE'] == 'prep_nulls'), {})
        mart_data = next((r for r in results if r['CHECK_TYPE'] == 'mart_quality'), {})
        
        issues = []
        status = "pass"
        
        # Check PREP quality
        if prep_data.get('NULL_EMAILS', 0) > 0:
            issues.append(f"Found {prep_data['NULL_EMAILS']} NULL emails in PREP layer")
            status = "warning"
        
        if prep_data.get('INVALID_EMAILS', 0) > 0:
            issues.append(f"Found {prep_data['INVALID_EMAILS']} invalid emails in PREP layer")
            status = "fail"
        
        # Check MART quality  
        if mart_data.get('ZERO_COUNTS', 0) > 0:
            issues.append(f"Found {mart_data['ZERO_COUNTS']} zero/negative counts in MART layer")
            status = "fail"
        
        return {
            "test_name": "Data Quality Assessment",
            "test_type": "data_quality", 
            "status": status,
            "metrics": {
                "prep_null_emails": prep_data.get('NULL_EMAILS', 0),
                "prep_invalid_emails": prep_data.get('INVALID_EMAILS', 0),
                "mart_zero_counts": mart_data.get('ZERO_COUNTS', 0)
            },
            "issues": issues,
            "raw_data": results
        }
    
    async def _test_transformation_logic(self, source_table: str, prep_table: str, mart_table: str) -> Dict[str, Any]:
        """Test transformation logic accuracy."""
        
        sql = f"""
        SELECT 
            COUNT(*) as total_prep_rows,
            COUNT(CASE WHEN email_quality_flag = 'VALID_EMAIL' THEN 1 END) as valid_flags,
            COUNT(CASE WHEN email_quality_flag = 'INVALID_EMAIL' THEN 1 END) as invalid_flags,
            COUNT(CASE WHEN email_quality_flag = 'MISSING_EMAIL' THEN 1 END) as missing_flags,
            -- Verify flag accuracy
            COUNT(CASE 
                WHEN EMAIL IS NULL AND email_quality_flag = 'MISSING_EMAIL' THEN 1
                WHEN EMAIL NOT LIKE '%@%' AND EMAIL IS NOT NULL AND email_quality_flag = 'INVALID_EMAIL' THEN 1
                WHEN EMAIL LIKE '%@%' AND email_quality_flag = 'VALID_EMAIL' THEN 1
            END) as correct_flags
        FROM {prep_table}
        WHERE email_quality_flag IS NOT NULL
        """
        
        results = await self.connector.execute_query(sql)
        
        if not results:
            return {
                "test_name": "Transformation Logic Validation",
                "test_type": "transformation_validation",
                "status": "fail",
                "issues": ["No transformation data found"],
                "raw_data": []
            }
        
        data = results[0]
        total_rows = data.get('TOTAL_PREP_ROWS', 0)
        correct_flags = data.get('CORRECT_FLAGS', 0)
        
        accuracy = (correct_flags / total_rows * 100) if total_rows > 0 else 0
        
        status = "pass" if accuracy >= 95 else "fail" if accuracy < 80 else "warning"
        issues = []
        
        if accuracy < 95:
            issues.append(f"Email quality flag accuracy is {accuracy:.1f}% (expected >= 95%)")
        
        return {
            "test_name": "Transformation Logic Validation", 
            "test_type": "transformation_validation",
            "status": status,
            "metrics": {
                "total_rows": total_rows,
                "correct_transformations": correct_flags,
                "accuracy_percentage": round(accuracy, 2),
                "valid_emails": data.get('VALID_FLAGS', 0),
                "invalid_emails": data.get('INVALID_FLAGS', 0), 
                "missing_emails": data.get('MISSING_FLAGS', 0)
            },
            "issues": issues,
            "raw_data": results
        }
    
    async def _test_business_rules(self, source_table: str, prep_table: str, mart_table: str) -> Dict[str, Any]:
        """Test business rule compliance."""
        
        sql = f"""
        SELECT 
            COUNT(*) as total_mart_rows,
            SUM(customer_count) as total_customers_aggregated,
            COUNT(CASE WHEN customer_count > 0 THEN 1 END) as positive_counts,
            (SELECT COUNT(*) FROM {prep_table}) as prep_total_for_validation
        FROM {mart_table}
        """
        
        results = await self.connector.execute_query(sql)
        
        if not results:
            return {
                "test_name": "Business Rules Validation",
                "test_type": "business_rules", 
                "status": "fail",
                "issues": ["No business rule data found"],
                "raw_data": []
            }
        
        data = results[0]
        mart_rows = data.get('TOTAL_MART_ROWS', 0)
        aggregated_customers = data.get('TOTAL_CUSTOMERS_AGGREGATED', 0)
        prep_total = data.get('PREP_TOTAL_FOR_VALIDATION', 0)
        
        issues = []
        status = "pass"
        
        # Business Rule 1: MART aggregation should match PREP totals
        if aggregated_customers != prep_total:
            issues.append(f"Aggregation mismatch: MART shows {aggregated_customers} customers, PREP has {prep_total}")
            status = "fail"
        
        # Business Rule 2: MART should have multiple categories (email quality flags)
        if mart_rows < 2:
            issues.append("MART should have multiple email quality categories")
            status = "warning"
        
        return {
            "test_name": "Business Rules Validation",
            "test_type": "business_rules",
            "status": status, 
            "metrics": {
                "mart_categories": mart_rows,
                "total_customers_aggregated": aggregated_customers,
                "prep_total_customers": prep_total
            },
            "issues": issues,
            "raw_data": results
        }
    
    def _generate_recommendations(self, test_results: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations based on test results."""
        
        recommendations = []
        
        for test in test_results:
            if test["status"] == "fail":
                if test["test_type"] == "row_count":
                    recommendations.append("🔍 Review data filtering logic in PREP layer - unexpected row count changes detected")
                elif test["test_type"] == "data_quality":
                    recommendations.append("🧹 Implement data cleansing rules for email validation and NULL handling")
                elif test["test_type"] == "transformation_validation":
                    recommendations.append("⚙️ Fix email quality flag logic - transformation accuracy below threshold")
                elif test["test_type"] == "business_rules":
                    recommendations.append("📊 Review aggregation logic in MART layer - business rule violations found")
            
            elif test["status"] == "warning":
                recommendations.append(f"⚠️ Monitor {test['test_name']} - potential issues detected")
        
        if not recommendations:
            recommendations.append("✅ All tests passed - pipeline is healthy!")
        
        return recommendations
