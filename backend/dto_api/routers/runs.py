"""Test run execution and reporting endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException, Depends, Query
import structlog

from dto_api.models.reports import (
    RunRequest,
    RunResponse,
    RunSummary,
    RunListRequest,
    RunListResponse,
    ReportRecord
)
from dto_api.models.tests import TestResult
from dto_api.services.runner import RunnerService

router = APIRouter()
logger = structlog.get_logger()


def get_runner_service() -> RunnerService:
    """Dependency to get runner service."""
    return RunnerService()


@router.post("/suites/{suite_id}/run", response_model=RunResponse)
async def run_suite(
    suite_id: str,
    request: RunRequest,
    runner: RunnerService = Depends(get_runner_service)
) -> RunResponse:
    """Execute a test suite."""
    try:
        logger.info(
            "Starting test suite run",
            suite_id=suite_id,
            dry_run=request.dry_run,
            budget_seconds=request.budget_seconds
        )
        
        # Override suite_id from path parameter
        request.suite_id = suite_id
        
        result = await runner.execute_suite(request)
        
        logger.info(
            "Test suite run initiated",
            run_id=result.run_id,
            estimated_duration=result.estimated_duration_seconds
        )
        
        return result
        
    except Exception as e:
        logger.error("Failed to start test run", suite_id=suite_id, exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to start run: {str(e)}")


@router.get("/runs", response_model=RunListResponse)
async def list_runs(
    status: str = Query(None, description="Filter by status"),
    suite: str = Query(None, description="Filter by suite name"),
    limit: int = Query(50, description="Maximum results"),
    offset: int = Query(0, description="Results offset"),
    runner: RunnerService = Depends(get_runner_service)
) -> RunListResponse:
    """List test runs with optional filters."""
    try:
        logger.info(
            "Listing test runs",
            status=status,
            suite=suite,
            limit=limit,
            offset=offset
        )
        
        # Create request object
        list_request = RunListRequest(
            status=status,
            suite=suite,
            limit=limit,
            offset=offset
        )
        
        result = await runner.list_runs(list_request)
        
        return result
        
    except Exception as e:
        logger.error("Failed to list runs", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to list runs: {str(e)}")


@router.get("/runs/{run_id}", response_model=RunSummary)
async def get_run(
    run_id: str,
    runner: RunnerService = Depends(get_runner_service)
) -> RunSummary:
    """Get run summary by ID."""
    try:
        logger.info("Getting run summary", run_id=run_id)
        
        result = await runner.get_run_summary(run_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Run not found")
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get run", run_id=run_id, exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to get run: {str(e)}")


@router.get("/runs/{run_id}/results", response_model=List[TestResult])
async def get_run_results(
    run_id: str,
    limit: int = Query(100, description="Maximum results"),
    offset: int = Query(0, description="Results offset"),
    runner: RunnerService = Depends(get_runner_service)
) -> List[TestResult]:
    """Get paginated test results for a run."""
    try:
        logger.info(
            "Getting run results",
            run_id=run_id,
            limit=limit,
            offset=offset
        )
        
        results = await runner.get_run_results(run_id, limit=limit, offset=offset)
        
        return results
        
    except Exception as e:
        logger.error("Failed to get run results", run_id=run_id, exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")


@router.get("/runs/{run_id}/artifacts")
async def get_run_artifacts(
    run_id: str,
    runner: RunnerService = Depends(get_runner_service)
) -> dict:
    """Get artifact URIs for a run."""
    try:
        logger.info("Getting run artifacts", run_id=run_id)
        
        artifacts = await runner.get_run_artifacts(run_id)
        
        if not artifacts:
            raise HTTPException(status_code=404, detail="Run not found or no artifacts")
            
        return artifacts
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get run artifacts", run_id=run_id, exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to get artifacts: {str(e)}")


@router.get("/runs/{run_id}/ai/prompts")
async def get_run_ai_prompts(
    run_id: str,
    runner: RunnerService = Depends(get_runner_service)
) -> dict:
    """Get AI prompt log for a run (redacted)."""
    try:
        logger.info("Getting AI prompts for run", run_id=run_id)
        
        prompts = await runner.get_ai_prompts(run_id)
        
        if not prompts:
            raise HTTPException(status_code=404, detail="Run not found or no AI prompts")
            
        return prompts
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get AI prompts", run_id=run_id, exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to get AI prompts: {str(e)}")


@router.post("/runs/{run_id}/cancel")
async def cancel_run(
    run_id: str,
    runner: RunnerService = Depends(get_runner_service)
) -> dict:
    """Cancel a running test suite."""
    try:
        logger.info("Cancelling test run", run_id=run_id)
        
        success = await runner.cancel_run(run_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Run not found or not cancellable")
            
        logger.info("Test run cancelled", run_id=run_id)
        return {"message": "Run cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel run", run_id=run_id, exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to cancel run: {str(e)}")
