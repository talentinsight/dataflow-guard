"""Source Evidence Package (SEP) validation endpoints."""

from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends
import structlog

from dto_api.adapters.connectors.snowflake import SnowflakeConnector

router = APIRouter()
logger = structlog.get_logger()


class SEPWindow(BaseModel):
    """Time window for SEP validation."""
    
    column: str = Field(..., description="Timestamp column name")
    from_time: datetime = Field(..., alias="from", description="Window start time")
    to_time: datetime = Field(..., alias="to", description="Window end time")


class SEPManifest(BaseModel):
    """Expected metrics from source evidence package."""
    
    batch_id: str = Field(..., description="Batch identifier")
    expected_rowcount: int = Field(..., description="Expected row count")
    control_totals: Dict[str, Any] = Field(..., description="Control totals (SUM, DISTINCT, MIN, MAX)")


class SEPTolerances(BaseModel):
    """Tolerances for SEP validation."""
    
    rowcount_abs: int = Field(default=0, description="Absolute row count tolerance")
    rowcount_pct: float = Field(default=0.0, description="Percentage row count tolerance")
    totals_pct: float = Field(default=0.5, description="Control totals percentage tolerance")


class SEPValidateRequest(BaseModel):
    """Request to validate Source Evidence Package."""
    
    raw_table: str = Field(..., description="RAW table to validate")
    window: SEPWindow = Field(..., description="Time window for validation")
    manifest: SEPManifest = Field(..., description="Expected metrics from source")
    tolerances: SEPTolerances = Field(default_factory=SEPTolerances, description="Validation tolerances")


class SEPValidationResult(BaseModel):
    """Result of SEP validation."""
    
    status: str = Field(..., description="Validation status (pass/fail)")
    batch_id: str = Field(..., description="Batch ID validated")
    actual_metrics: Dict[str, Any] = Field(..., description="Actual metrics from RAW table")
    expected_metrics: Dict[str, Any] = Field(..., description="Expected metrics from manifest")
    differences: Dict[str, Any] = Field(..., description="Differences between actual and expected")
    within_tolerance: Dict[str, bool] = Field(..., description="Which metrics are within tolerance")
    query_id: Optional[str] = Field(None, description="Snowflake query ID for audit")


def get_snowflake_connector() -> SnowflakeConnector:
    """Dependency to get Snowflake connector."""
    return SnowflakeConnector()


@router.post("/sep/validate", response_model=SEPValidationResult)
async def validate_sep(
    request: SEPValidateRequest,
    connector: SnowflakeConnector = Depends(get_snowflake_connector)
) -> SEPValidationResult:
    """Validate Source Evidence Package against RAW table metrics."""
    try:
        logger.info(
            "Starting SEP validation",
            raw_table=request.raw_table,
            batch_id=request.manifest.batch_id,
            window_from=request.window.from_time,
            window_to=request.window.to_time
        )
        
        # Generate SQL to compute actual metrics
        metrics_sql = _generate_metrics_sql(request)
        
        # Execute query to get actual metrics
        result = await connector.select(metrics_sql)
        
        if not result['rows']:
            raise ValueError("No data found in the specified time window")
        
        actual_row = result['rows'][0]
        query_id = result['query_id']
        
        # Extract actual metrics
        actual_metrics = {
            'rowcount': actual_row.get('ACTUAL_ROWCOUNT', 0),
            'control_totals': {}
        }
        
        # Extract control totals from result
        for key in request.manifest.control_totals.keys():
            column_key = key.upper().replace('(', '_').replace(')', '').replace('.', '_')
            actual_metrics['control_totals'][key] = actual_row.get(f'ACTUAL_{column_key}')
        
        # Compare with expected metrics
        expected_metrics = {
            'rowcount': request.manifest.expected_rowcount,
            'control_totals': request.manifest.control_totals
        }
        
        # Calculate differences and check tolerances
        differences = {}
        within_tolerance = {}
        overall_status = "pass"
        
        # Check row count
        rowcount_diff = abs(actual_metrics['rowcount'] - expected_metrics['rowcount'])
        rowcount_pct_diff = (rowcount_diff / expected_metrics['rowcount'] * 100) if expected_metrics['rowcount'] > 0 else 0
        
        differences['rowcount'] = {
            'absolute': rowcount_diff,
            'percentage': rowcount_pct_diff
        }
        
        within_tolerance['rowcount'] = (
            rowcount_diff <= request.tolerances.rowcount_abs or
            rowcount_pct_diff <= request.tolerances.rowcount_pct
        )
        
        if not within_tolerance['rowcount']:
            overall_status = "fail"
        
        # Check control totals
        for key, expected_value in expected_metrics['control_totals'].items():
            actual_value = actual_metrics['control_totals'].get(key)
            
            if actual_value is not None and expected_value is not None:
                if isinstance(expected_value, (int, float)) and isinstance(actual_value, (int, float)):
                    abs_diff = abs(actual_value - expected_value)
                    pct_diff = (abs_diff / abs(expected_value) * 100) if expected_value != 0 else 0
                    
                    differences[key] = {
                        'absolute': abs_diff,
                        'percentage': pct_diff
                    }
                    
                    within_tolerance[key] = pct_diff <= request.tolerances.totals_pct
                    
                    if not within_tolerance[key]:
                        overall_status = "fail"
                else:
                    # String comparison
                    within_tolerance[key] = str(actual_value) == str(expected_value)
                    differences[key] = {
                        'match': within_tolerance[key]
                    }
                    
                    if not within_tolerance[key]:
                        overall_status = "fail"
            else:
                within_tolerance[key] = False
                differences[key] = {
                    'error': f'Missing value - actual: {actual_value}, expected: {expected_value}'
                }
                overall_status = "fail"
        
        logger.info(
            "SEP validation completed",
            batch_id=request.manifest.batch_id,
            status=overall_status,
            query_id=query_id,
            rowcount_diff=differences['rowcount']['absolute']
        )
        
        return SEPValidationResult(
            status=overall_status,
            batch_id=request.manifest.batch_id,
            actual_metrics=actual_metrics,
            expected_metrics=expected_metrics,
            differences=differences,
            within_tolerance=within_tolerance,
            query_id=query_id
        )
        
    except Exception as e:
        logger.error("SEP validation failed", exc_info=e)
        raise HTTPException(status_code=500, detail=f"SEP validation failed: {str(e)}")


def _generate_metrics_sql(request: SEPValidateRequest) -> str:
    """Generate SQL to compute actual metrics from RAW table."""
    
    # Base query with time window filter
    sql_parts = [
        "SELECT",
        "    COUNT(*) as ACTUAL_ROWCOUNT"
    ]
    
    # Add control total calculations
    for key, expected_value in request.manifest.control_totals.items():
        if key.startswith('SUM(') and key.endswith(')'):
            # Extract column name from SUM(column_name)
            column = key[4:-1]
            sql_parts.append(f"    , SUM({column}) as ACTUAL_SUM_{column.upper()}")
        
        elif key.startswith('DISTINCT(') and key.endswith(')'):
            # Extract column name from DISTINCT(column_name)
            column = key[9:-1]
            sql_parts.append(f"    , COUNT(DISTINCT {column}) as ACTUAL_DISTINCT_{column.upper()}")
        
        elif key.startswith('MIN(') and key.endswith(')'):
            # Extract column name from MIN(column_name)
            column = key[4:-1]
            sql_parts.append(f"    , MIN({column}) as ACTUAL_MIN_{column.upper()}")
        
        elif key.startswith('MAX(') and key.endswith(')'):
            # Extract column name from MAX(column_name)
            column = key[4:-1]
            sql_parts.append(f"    , MAX({column}) as ACTUAL_MAX_{column.upper()}")
        
        else:
            # Custom metric - try to parse or use as-is
            safe_key = key.upper().replace('(', '_').replace(')', '').replace('.', '_')
            sql_parts.append(f"    , {key} as ACTUAL_{safe_key}")
    
    # Add FROM clause and time window filter
    sql_parts.extend([
        f"FROM {request.raw_table}",
        f"WHERE {request.window.column} >= '{request.window.from_time.isoformat()}'",
        f"  AND {request.window.column} < '{request.window.to_time.isoformat()}'"
    ])
    
    return "\n".join(sql_parts)
