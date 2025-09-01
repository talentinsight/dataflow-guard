"""Test definition and execution models."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class TestTolerance(BaseModel):
    """Test tolerance configuration."""
    
    abs: Optional[float] = Field(None, description="Absolute tolerance")
    pct: Optional[float] = Field(None, description="Percentage tolerance") 
    dup_rows: Optional[int] = Field(None, description="Duplicate rows tolerance")


class TestWindow(BaseModel):
    """Time window for test execution."""
    
    last_days: Optional[int] = Field(None, description="Last N days")
    last_hours: Optional[int] = Field(None, description="Last N hours")
    batch_id: Optional[str] = Field(None, description="Specific batch ID")
    start_date: Optional[datetime] = Field(None, description="Window start")
    end_date: Optional[datetime] = Field(None, description="Window end")


class TestFilter(BaseModel):
    """Filter conditions for test execution."""
    
    column: str = Field(..., description="Column to filter on")
    operator: Literal["equals", "not_equals", "in", "not_in", "gt", "lt", "gte", "lte"] = Field(
        ..., description="Filter operator"
    )
    value: Union[str, int, float, List[Union[str, int, float]]] = Field(
        ..., description="Filter value(s)"
    )


class TestDefinition(BaseModel):
    """Zero-SQL test definition."""
    
    name: str = Field(..., description="Test name")
    type: Literal[
        "uniqueness", "not_null", "freshness", "row_count", 
        "reconciliation", "rule", "schema", "drift"
    ] = Field(..., description="Test type")
    dataset: str = Field(..., description="Target dataset")
    keys: Optional[List[str]] = Field(None, description="Key columns for uniqueness/PK tests")
    expression: Optional[str] = Field(None, description="Business rule expression")
    window: Optional[TestWindow] = Field(None, description="Time window")
    filters: Optional[List[TestFilter]] = Field(None, description="Filter conditions")
    tolerance: Optional[TestTolerance] = Field(None, description="Tolerance settings")
    severity: Literal["blocker", "major", "minor"] = Field(default="major", description="Test severity")
    gate: Literal["fail", "warn"] = Field(default="fail", description="Gate behavior")
    enabled: bool = Field(default=True, description="Whether test is enabled")


class TestSuite(BaseModel):
    """Collection of tests."""
    
    name: str = Field(..., description="Suite name")
    connection: str = Field(..., description="Connection identifier")
    tests: List[TestDefinition] = Field(..., description="Test definitions")
    description: Optional[str] = Field(None, description="Suite description")
    tags: List[str] = Field(default_factory=list, description="Suite tags")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class IRFilter(BaseModel):
    """IR filter representation."""
    
    type: str = Field(..., description="Filter type")
    column: str = Field(..., description="Column name")
    value: Any = Field(..., description="Filter value")
    operator: Optional[str] = Field(None, description="Filter operator")


class IRJoin(BaseModel):
    """IR join representation."""
    
    left: str = Field(..., description="Left join key")
    right: str = Field(..., description="Right join key") 
    type: Literal["inner", "left", "right", "full"] = Field(default="left", description="Join type")


class IRAssertion(BaseModel):
    """IR assertion representation."""
    
    kind: str = Field(..., description="Assertion kind")
    left: str = Field(..., description="Left operand")
    right: Union[str, Dict[str, Any]] = Field(..., description="Right operand")
    tolerance: Optional[Dict[str, float]] = Field(None, description="Tolerance settings")


class IR(BaseModel):
    """Intermediate Representation - AI compiler output."""
    
    ir_version: str = Field(default="1.0", description="IR version")
    dataset: str = Field(..., description="Target dataset")
    filters: List[IRFilter] = Field(default_factory=list, description="Filter conditions")
    joins: List[IRJoin] = Field(default_factory=list, description="Join conditions")
    aggregations: List[Dict[str, Any]] = Field(default_factory=list, description="Aggregation specs")
    assertion: IRAssertion = Field(..., description="Test assertion")
    partition_by: List[str] = Field(default_factory=list, description="Partition columns")
    dialect: str = Field(..., description="Target SQL dialect")


class CompileRequest(BaseModel):
    """Request to compile NL/Formula to IR."""
    
    expression: str = Field(..., description="Natural language or formula expression")
    dataset: str = Field(..., description="Target dataset")
    catalog_context: Optional[Dict[str, Any]] = Field(None, description="Catalog context")
    test_type: Optional[str] = Field(None, description="Hint for test type")


class CompileResponse(BaseModel):
    """Response from test compilation."""
    
    ir: IR = Field(..., description="Generated IR")
    sql_preview: str = Field(..., description="Generated SQL (if preview enabled)")
    confidence: float = Field(..., description="AI confidence score 0-1")
    warnings: List[str] = Field(default_factory=list, description="Compilation warnings")


class TestProposal(BaseModel):
    """AI-proposed test."""
    
    test_def: TestDefinition = Field(..., description="Proposed test definition")
    rationale: str = Field(..., description="Why this test is recommended")
    confidence: float = Field(..., description="AI confidence score 0-1")
    auto_approvable: bool = Field(default=False, description="Can be auto-approved")


class ProposeRequest(BaseModel):
    """Request for AI test proposals."""
    
    datasets: List[str] = Field(..., description="Target datasets")
    catalog_id: str = Field(..., description="Catalog context")
    profile: Literal["smoke", "standard", "deep", "custom"] = Field(
        default="standard", description="Test profile"
    )
    layers: Optional[List[str]] = Field(None, description="Target layers (RAW/PREP/MART)")


class ProposeResponse(BaseModel):
    """Response with AI test proposals."""
    
    proposals: List[TestProposal] = Field(..., description="Test proposals")
    total_proposed: int = Field(..., description="Total number of proposals")
    auto_approvable_count: int = Field(..., description="Number of auto-approvable tests")


class TestResult(BaseModel):
    """Individual test execution result."""
    
    test_name: str = Field(..., description="Test name")
    status: Literal["pass", "fail", "error", "skip"] = Field(..., description="Test status")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Test metrics")
    violations: Optional[int] = Field(None, description="Number of violations")
    sample_rows_uri: Optional[str] = Field(None, description="URI to sample violation rows")
    error_message: Optional[str] = Field(None, description="Error message if status=error")
    started_at: datetime = Field(..., description="Test start time")
    ended_at: datetime = Field(..., description="Test end time")
    execution_time_ms: int = Field(..., description="Execution time in milliseconds")
