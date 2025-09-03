"""Test management and compilation endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import structlog

from dto_api.models.tests import (
    TestSuite,
    CompileRequest,
    CompileResponse,
    ProposeRequest,
    ProposeResponse,
    TestDefinition,
    TestProposal,
    IR,
    IRAssertion
)
from dto_api.services.ai_adapter_iface import AIAdapterInterface
from dto_api.services.planner import TestPlannerService
from dto_api.services.compile_service import compile_service

router = APIRouter()
logger = structlog.get_logger()

# Mock test catalog for UI demo
DEMO_TEST_CATALOG = [
    {
        "id": "data-quality",
        "name": "Data Quality Check",
        "description": "Validate data completeness and accuracy",
        "category": "Quality",
        "tests": [
            {"id": "null-check", "name": "Null Value Check", "description": "Check for unexpected null values"},
            {"id": "duplicate-check", "name": "Duplicate Detection", "description": "Identify duplicate records"},
            {"id": "range-check", "name": "Value Range Validation", "description": "Ensure values are within expected ranges"},
        ]
    },
    {
        "id": "schema-validation", 
        "name": "Schema Validation",
        "description": "Check column types and constraints",
        "category": "Schema",
        "tests": [
            {"id": "type-check", "name": "Data Type Validation", "description": "Verify column data types"},
            {"id": "constraint-check", "name": "Constraint Validation", "description": "Check primary key and foreign key constraints"},
            {"id": "column-check", "name": "Column Existence", "description": "Ensure required columns exist"},
        ]
    },
    {
        "id": "freshness-check",
        "name": "Data Freshness", 
        "description": "Monitor data update frequency",
        "category": "Freshness",
        "tests": [
            {"id": "last-update", "name": "Last Update Check", "description": "Verify data was updated recently"},
            {"id": "batch-freshness", "name": "Batch Freshness", "description": "Check if latest batch is within SLA"},
        ]
    }
]


def get_ai_adapter() -> AIAdapterInterface:
    """Dependency to get AI adapter."""
    return AIAdapterInterface()


def get_planner_service() -> TestPlannerService:
    """Dependency to get test planner service."""
    return TestPlannerService()


@router.get("/tests/catalog")
async def get_test_catalog():
    """Get available test catalog for UI demo."""
    return {"tests": DEMO_TEST_CATALOG}


class TestCompileRequest(BaseModel):
    """Request model for test compilation."""
    tests: List[Dict[str, Any]]
    dataset: Optional[str] = None


class TestCompileResponse(BaseModel):
    """Response model for test compilation."""
    sql: str
    tests: List[Dict[str, Any]]
    meta: Dict[str, Any]


@router.post("/tests/compile", response_model=TestCompileResponse)
async def compile_tests(
    request: TestCompileRequest
) -> TestCompileResponse:
    """Compile test templates into executable SQL."""
    try:
        logger.info(
            "Compiling test templates",
            test_count=len(request.tests),
            dataset=request.dataset
        )
        
        # Use compile service to generate SQL
        result = compile_service.compile_tests(request.tests, request.dataset)
        
        logger.info(
            "Test compilation completed",
            test_count=len(result["tests"])
        )
        
        return TestCompileResponse(**result)
        
    except Exception as e:
        logger.error("Test compilation failed", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Compilation failed: {str(e)}")


@router.post("/tests/compile-expression", response_model=CompileResponse)
async def compile_expression(
    request: CompileRequest,
    ai_adapter: AIAdapterInterface = Depends(get_ai_adapter)
) -> CompileResponse:
    """Compile natural language or formula expression to IR and SQL."""
    try:
        logger.info(
            "Compiling test expression",
            expression=request.expression[:100] + "..." if len(request.expression) > 100 else request.expression,
            dataset=request.dataset,
            test_type=request.test_type
        )
        
        # Use AI adapter to compile expression
        result = await ai_adapter.compile_expression(request)
        
        logger.info(
            "Test compilation completed",
            confidence=result.confidence,
            warnings_count=len(result.warnings)
        )
        
        return result
        
    except Exception as e:
        logger.error("Test compilation failed", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Compilation failed: {str(e)}")


@router.post("/tests/propose", response_model=ProposeResponse)
async def propose_tests(
    request: ProposeRequest,
    planner: TestPlannerService = Depends(get_planner_service)
) -> ProposeResponse:
    """Get AI-proposed tests for datasets."""
    try:
        logger.info(
            "Proposing tests",
            datasets=request.datasets,
            catalog_id=request.catalog_id,
            profile=request.profile
        )
        
        proposals = await planner.propose_tests(request)
        
        logger.info(
            "Test proposals generated",
            total_proposed=proposals.total_proposed,
            auto_approvable=proposals.auto_approvable_count
        )
        
        return proposals
        
    except Exception as e:
        logger.error("Test proposal failed", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Proposal failed: {str(e)}")


@router.get("/suites", response_model=list[TestSuite])
async def list_suites() -> list[TestSuite]:
    """List all test suites."""
    try:
        # TODO: Implement actual suite listing from database
        # For now, return mock data
        from datetime import datetime
        
        mock_suites = [
            TestSuite(
                name="orders_basic",
                connection="snowflake_prod",
                description="Basic data quality tests for orders pipeline",
                tests=[
                    TestDefinition(
                        name="pk_uniqueness_orders",
                        type="uniqueness",
                        dataset="RAW.ORDERS",
                        keys=["ORDER_ID"],
                        tolerance={"dup_rows": 0},
                        severity="blocker",
                        gate="fail"
                    ),
                    TestDefinition(
                        name="business_rule_total_consistency",
                        type="rule",
                        expression="order_total == items_total + tax + shipping",
                        dataset="PREP.ORDERS",
                        window={"last_days": 30},
                        filters=[{
                            "column": "return_flag",
                            "operator": "equals",
                            "value": "N"
                        }],
                        tolerance={"abs": 0.01},
                        severity="major",
                        gate="fail"
                    )
                ],
                tags=["orders", "basic"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        return mock_suites
        
    except Exception as e:
        logger.error("Failed to list suites", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to list suites: {str(e)}")


@router.post("/suites", response_model=TestSuite)
async def create_suite(suite: TestSuite) -> TestSuite:
    """Create a new test suite."""
    try:
        logger.info("Creating test suite", suite_name=suite.name)
        
        # TODO: Implement actual suite creation in database
        # For now, just return the suite with timestamps
        from datetime import datetime
        
        suite.created_at = datetime.utcnow()
        suite.updated_at = datetime.utcnow()
        
        logger.info("Test suite created", suite_name=suite.name)
        return suite
        
    except Exception as e:
        logger.error("Failed to create suite", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to create suite: {str(e)}")


@router.get("/suites/{suite_id}", response_model=TestSuite)
async def get_suite(suite_id: str) -> TestSuite:
    """Get a specific test suite."""
    try:
        logger.info("Getting test suite", suite_id=suite_id)
        
        # TODO: Implement actual suite retrieval from database
        # For now, return mock data
        from datetime import datetime
        
        if suite_id == "orders_basic":
            return TestSuite(
                name="orders_basic",
                connection="snowflake_prod",
                description="Basic data quality tests for orders pipeline",
                tests=[
                    TestDefinition(
                        name="pk_uniqueness_orders",
                        type="uniqueness",
                        dataset="RAW.ORDERS",
                        keys=["ORDER_ID"],
                        tolerance={"dup_rows": 0},
                        severity="blocker",
                        gate="fail"
                    )
                ],
                tags=["orders", "basic"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        else:
            raise HTTPException(status_code=404, detail="Suite not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get suite", suite_id=suite_id, exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to get suite: {str(e)}")


@router.put("/suites/{suite_id}", response_model=TestSuite)
async def update_suite(suite_id: str, suite: TestSuite) -> TestSuite:
    """Update a test suite."""
    try:
        logger.info("Updating test suite", suite_id=suite_id)
        
        # TODO: Implement actual suite update in database
        from datetime import datetime
        
        suite.updated_at = datetime.utcnow()
        
        logger.info("Test suite updated", suite_id=suite_id)
        return suite
        
    except Exception as e:
        logger.error("Failed to update suite", suite_id=suite_id, exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to update suite: {str(e)}")


@router.delete("/suites/{suite_id}")
async def delete_suite(suite_id: str) -> dict:
    """Delete a test suite."""
    try:
        logger.info("Deleting test suite", suite_id=suite_id)
        
        # TODO: Implement actual suite deletion from database
        
        logger.info("Test suite deleted", suite_id=suite_id)
        return {"message": "Suite deleted successfully"}
        
    except Exception as e:
        logger.error("Failed to delete suite", suite_id=suite_id, exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to delete suite: {str(e)}")
