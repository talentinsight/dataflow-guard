"""
Hybrid Test Router: Static Tests + AI Fallback
"""
from typing import List, Optional
import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from dto_api.services.hybrid_test_engine import HybridTestEngine, HYBRID_TEST_EXAMPLES

router = APIRouter()
logger = structlog.get_logger()

class HybridTestRequest(BaseModel):
    source_table: str
    prep_table: str
    mart_table: str
    test_types: List[str] = ["row_count", "null_check", "email_format", "transformation_accuracy"]
    natural_language_tests: Optional[List[str]] = None
    use_ai_fallback: bool = True

@router.post("/hybrid/test")
async def run_hybrid_pipeline_test(request: HybridTestRequest):
    """Run hybrid pipeline test with static tests + AI fallback."""
    
    try:
        hybrid_engine = HybridTestEngine()
        
        results = await hybrid_engine.run_hybrid_tests(
            source_table=request.source_table,
            prep_table=request.prep_table,
            mart_table=request.mart_table,
            test_types=request.test_types,
            natural_language_tests=request.natural_language_tests
        )
        
        return results
        
    except Exception as e:
        logger.error("Hybrid test execution failed", exc_info=e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hybrid/examples")
async def get_hybrid_test_examples():
    """Get example hybrid test configurations."""
    
    return {
        "examples": HYBRID_TEST_EXAMPLES,
        "available_static_tests": [
            "row_count",
            "null_check", 
            "duplicate_check",
            "email_format",
            "transformation_accuracy"
        ],
        "ai_test_examples": [
            "Check if customer segmentation rules are applied correctly",
            "Validate revenue calculations match business requirements",
            "Verify data consistency across all pipeline layers",
            "Check for anomalies in transformation process",
            "Validate referential integrity between tables"
        ]
    }

@router.get("/hybrid/cost-estimate")
async def estimate_test_costs(
    static_tests: int = 5,
    ai_tests: int = 2,
    avg_tokens_per_ai_test: int = 500
):
    """Estimate costs for hybrid testing."""
    
    total_ai_tokens = ai_tests * avg_tokens_per_ai_test
    estimated_ai_cost = total_ai_tokens * 0.00001  # Rough GPT-4 estimate
    
    return {
        "static_tests": {
            "count": static_tests,
            "cost_usd": 0.0,
            "execution_time_estimate_seconds": static_tests * 2
        },
        "ai_tests": {
            "count": ai_tests,
            "estimated_tokens": total_ai_tokens,
            "estimated_cost_usd": round(estimated_ai_cost, 4),
            "execution_time_estimate_seconds": ai_tests * 5
        },
        "total": {
            "estimated_cost_usd": round(estimated_ai_cost, 4),
            "execution_time_estimate_seconds": (static_tests * 2) + (ai_tests * 5)
        }
    }
