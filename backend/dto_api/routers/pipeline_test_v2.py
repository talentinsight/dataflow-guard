"""
Real ETL Pipeline Testing Router - Production Ready
"""
import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from dto_api.services.etl_test_engine import ETLTestEngine
from dto_api.services.report_generator import HTMLReportGenerator

router = APIRouter()
logger = structlog.get_logger()

# In-memory store for test runs
test_runs: Dict[str, Dict[str, Any]] = {}

class PipelineTestRequest(BaseModel):
    source_table: str
    prep_table: str
    mart_table: str
    test_types: List[str] = ["row_count", "data_quality", "transformation_validation", "business_rules"]

class PipelineTestStatus(BaseModel):
    run_id: str
    status: str
    current_step: str
    started_at: str
    finished_at: str | None = None
    error: str | None = None
    test_summary: Dict[str, Any] | None = None
    data_quality_score: float | None = None
    recommendations: List[str] | None = None
    html_report_url: str | None = None
    comprehensive_results: Dict[str, Any] | None = None

async def _execute_comprehensive_tests(run_id: str, request: PipelineTestRequest):
    """Execute comprehensive ETL pipeline tests."""
    try:
        run_data = test_runs[run_id]
        
        # Initialize test engine
        test_engine = ETLTestEngine()
        
        run_data["status"] = "running"
        run_data["current_step"] = "executing_comprehensive_tests"
        
        logger.info("Starting comprehensive ETL tests", 
                   run_id=run_id,
                   source_table=request.source_table,
                   prep_table=request.prep_table,
                   mart_table=request.mart_table,
                   test_types=request.test_types)
        
        # Execute all tests using the engine
        comprehensive_results = await test_engine.run_comprehensive_tests(
            source_table=request.source_table,
            prep_table=request.prep_table,
            mart_table=request.mart_table,
            test_types=request.test_types
        )
        
        # Store comprehensive results
        run_data["comprehensive_results"] = comprehensive_results
        run_data["test_summary"] = comprehensive_results["test_summary"]
        run_data["data_quality_score"] = comprehensive_results["data_quality_score"]
        run_data["recommendations"] = comprehensive_results["recommendations"]
        
        # Add HTML report URL
        run_data["html_report_url"] = f"/api/v1/pipeline/test/v2/{run_id}/report/html"
        
        # Mark test run as completed
        run_data["status"] = "completed"
        run_data["finished_at"] = datetime.utcnow().isoformat()
        run_data["current_step"] = "completed"
        
        logger.info("Comprehensive ETL tests completed", 
                   run_id=run_id,
                   quality_score=comprehensive_results["data_quality_score"],
                   tests_passed=comprehensive_results["test_summary"]["passed"],
                   tests_failed=comprehensive_results["test_summary"]["failed"],
                   execution_time=comprehensive_results["test_summary"]["execution_time_seconds"])
        
    except Exception as e:
        logger.error("Comprehensive ETL tests failed", run_id=run_id, exc_info=e)
        if run_id in test_runs:
            test_runs[run_id]["status"] = "failed"
            test_runs[run_id]["error"] = str(e)
            test_runs[run_id]["finished_at"] = datetime.utcnow().isoformat()
        raise

@router.post("/pipeline/test/v2", response_model=PipelineTestStatus)
async def run_comprehensive_pipeline_test(request: PipelineTestRequest):
    """Initiate a comprehensive ETL pipeline test run."""
    run_id = str(uuid.uuid4())
    
    test_runs[run_id] = {
        "run_id": run_id,
        "status": "pending",
        "current_step": "initialized",
        "started_at": datetime.utcnow().isoformat(),
        "request": request.dict()
    }
    
    # Start tests in background
    asyncio.create_task(_execute_comprehensive_tests(run_id, request))
    
    return PipelineTestStatus(**test_runs[run_id])

@router.get("/pipeline/test/v2/{run_id}", response_model=PipelineTestStatus)
async def get_comprehensive_test_status(run_id: str):
    """Get the status of a comprehensive ETL pipeline test run."""
    if run_id not in test_runs:
        raise HTTPException(status_code=404, detail="Pipeline test run not found")
    
    return PipelineTestStatus(**test_runs[run_id])

@router.get("/pipeline/test/v2/{run_id}/report")
async def get_test_report(run_id: str):
    """Get detailed test report with all metrics and recommendations."""
    if run_id not in test_runs:
        raise HTTPException(status_code=404, detail="Pipeline test run not found")
    
    run_data = test_runs[run_id]
    
    if run_data["status"] != "completed":
        raise HTTPException(status_code=400, detail="Test run not completed yet")
    
    if "comprehensive_results" not in run_data:
        raise HTTPException(status_code=404, detail="Test results not found")
    
    # Return comprehensive report
    report = {
        "run_id": run_id,
        "test_metadata": {
            "started_at": run_data["started_at"],
            "finished_at": run_data["finished_at"],
            "source_table": run_data["request"]["source_table"],
            "prep_table": run_data["request"]["prep_table"], 
            "mart_table": run_data["request"]["mart_table"],
            "test_types": run_data["request"]["test_types"]
        },
        "executive_summary": {
            "overall_status": "PASS" if run_data["comprehensive_results"]["test_summary"]["failed"] == 0 else "FAIL",
            "data_quality_score": run_data["data_quality_score"],
            "total_tests": run_data["test_summary"]["total_tests"],
            "tests_passed": run_data["test_summary"]["passed"],
            "tests_failed": run_data["test_summary"]["failed"],
            "tests_warnings": run_data["test_summary"]["warnings"],
            "execution_time_seconds": run_data["test_summary"]["execution_time_seconds"]
        },
        "detailed_results": run_data["comprehensive_results"]["test_results"],
        "recommendations": run_data["recommendations"],
        "report_generated_at": datetime.utcnow().isoformat()
    }
    
    return report

@router.get("/pipeline/test/v2/{run_id}/report/html")
async def get_test_report_html(run_id: str):
    """Get HTML formatted test report."""
    if run_id not in test_runs:
        raise HTTPException(status_code=404, detail="Pipeline test run not found")
    
    run_data = test_runs[run_id]
    
    if run_data["status"] != "completed":
        raise HTTPException(status_code=400, detail="Test run not completed yet")
    
    if "comprehensive_results" not in run_data:
        raise HTTPException(status_code=404, detail="Test results not found")
    
    # Generate comprehensive report data
    report_data = {
        "run_id": run_id,
        "test_metadata": {
            "started_at": run_data["started_at"],
            "finished_at": run_data["finished_at"],
            "source_table": run_data["request"]["source_table"],
            "prep_table": run_data["request"]["prep_table"], 
            "mart_table": run_data["request"]["mart_table"],
            "test_types": run_data["request"]["test_types"]
        },
        "executive_summary": {
            "overall_status": "PASS" if run_data["comprehensive_results"]["test_summary"]["failed"] == 0 else "FAIL",
            "data_quality_score": run_data["data_quality_score"],
            "total_tests": run_data["test_summary"]["total_tests"],
            "tests_passed": run_data["test_summary"]["passed"],
            "tests_failed": run_data["test_summary"]["failed"],
            "tests_warnings": run_data["test_summary"]["warnings"],
            "execution_time_seconds": run_data["test_summary"]["execution_time_seconds"]
        },
        "detailed_results": run_data["comprehensive_results"]["test_results"],
        "recommendations": run_data["recommendations"],
        "report_generated_at": datetime.utcnow().isoformat()
    }
    
    # Generate HTML report
    report_generator = HTMLReportGenerator()
    html_content = report_generator.generate_html_report(report_data)
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content, status_code=200)
