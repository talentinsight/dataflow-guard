"""Report and run execution models."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class AIMetadata(BaseModel):
    """AI execution metadata."""
    
    model: str = Field(..., description="AI model used")
    seed: int = Field(..., description="Random seed for determinism")
    temperature: float = Field(..., description="Temperature setting")
    top_p: float = Field(..., description="Top-p setting")
    prompts_uri: Optional[str] = Field(None, description="URI to prompt log")


class ReportRecord(BaseModel):
    """JSONL report record - one per test result."""
    
    run_id: str = Field(..., description="Run identifier")
    suite: str = Field(..., description="Suite name")
    test: str = Field(..., description="Test name")
    status: Literal["pass", "fail", "error", "skip"] = Field(..., description="Test status")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Test metrics")
    sample_rows_uri: Optional[str] = Field(None, description="URI to sample rows")
    started_at: datetime = Field(..., description="Test start time")
    ended_at: datetime = Field(..., description="Test end time")
    ai: Optional[AIMetadata] = Field(None, description="AI execution metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RunSummary(BaseModel):
    """Test run summary."""
    
    run_id: str = Field(..., description="Run identifier")
    suite_name: str = Field(..., description="Suite name")
    status: Literal["running", "completed", "failed", "cancelled"] = Field(
        ..., description="Overall run status"
    )
    total_tests: int = Field(..., description="Total number of tests")
    passed_tests: int = Field(default=0, description="Number of passed tests")
    failed_tests: int = Field(default=0, description="Number of failed tests")
    error_tests: int = Field(default=0, description="Number of error tests")
    skipped_tests: int = Field(default=0, description="Number of skipped tests")
    started_at: datetime = Field(..., description="Run start time")
    ended_at: Optional[datetime] = Field(None, description="Run end time")
    execution_time_ms: Optional[int] = Field(None, description="Total execution time")
    artifacts: Dict[str, str] = Field(
        default_factory=dict, 
        description="Artifact URIs (html_report, jsonl_results, etc.)"
    )
    environment: str = Field(..., description="Execution environment")
    connection: str = Field(..., description="Connection used")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RunRequest(BaseModel):
    """Request to execute a test suite."""
    
    suite_id: str = Field(..., description="Suite identifier")
    connection_override: Optional[str] = Field(None, description="Override connection")
    test_filter: Optional[List[str]] = Field(None, description="Filter to specific tests")
    dry_run: bool = Field(default=False, description="Dry run mode (validate only)")
    budget_seconds: Optional[int] = Field(None, description="Time budget for execution")


class RunResponse(BaseModel):
    """Response from run execution request."""
    
    run_id: str = Field(..., description="Generated run identifier")
    status: str = Field(..., description="Initial run status")
    estimated_duration_seconds: Optional[int] = Field(None, description="Estimated duration")


class RunListRequest(BaseModel):
    """Request to list runs with filters."""
    
    status: Optional[Literal["running", "completed", "failed", "cancelled"]] = Field(
        None, description="Filter by status"
    )
    suite: Optional[str] = Field(None, description="Filter by suite name")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    limit: int = Field(default=50, description="Maximum results")
    offset: int = Field(default=0, description="Results offset")


class RunListResponse(BaseModel):
    """Response with list of runs."""
    
    runs: List[RunSummary] = Field(..., description="Run summaries")
    total: int = Field(..., description="Total matching runs")
    limit: int = Field(..., description="Applied limit")
    offset: int = Field(..., description="Applied offset")
