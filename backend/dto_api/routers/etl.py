"""
ETL Pipeline Testing Router
Real Snowflake-based ETL pipeline testing endpoints
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Dict, Any, Optional
import structlog
import asyncio
import uuid
from datetime import datetime

from dto_api.adapters.connectors.snowflake import SnowflakeConnector
from dto_api.services.compile_service import compile_service

router = APIRouter()
logger = structlog.get_logger()

# In-memory storage for demo (replace with DB in production)
pipeline_runs: Dict[str, Dict] = {}

@router.post("/etl/pipeline/run")
async def run_etl_pipeline(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a real ETL pipeline test against Snowflake
    Raw → Prep → Mart transformation with validation
    """
    try:
        run_id = str(uuid.uuid4())
        
        # Extract configuration
        source_schema = request.get("source_schema", "PROD_DB.RAW")
        target_schema = request.get("target_schema", "PROD_DB.MART") 
        table_pattern = request.get("table_pattern", "CUSTOMERS")
        validation_rules = request.get("validation_rules", [])
        
        logger.info("Starting ETL pipeline run", 
                   run_id=run_id, 
                   source_schema=source_schema,
                   target_schema=target_schema)
        
        # Initialize run tracking
        pipeline_runs[run_id] = {
            "id": run_id,
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
            "source_schema": source_schema,
            "target_schema": target_schema,
            "table_pattern": table_pattern,
            "validation_rules": validation_rules,
            "steps": [],
            "current_step": "initializing"
        }
        
        # Start async pipeline execution
        asyncio.create_task(_execute_etl_pipeline(run_id, request))
        
        return {
            "run_id": run_id,
            "status": "running",
            "message": "ETL pipeline started successfully",
            "estimated_duration": "3-5 minutes",
            "steps": ["Raw Data Validation", "Prep Layer Transform", "Mart Layer Aggregation"]
        }
        
    except Exception as e:
        logger.error("Failed to start ETL pipeline", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to start pipeline: {str(e)}")


async def _execute_etl_pipeline(run_id: str, request: Dict[str, Any]):
    """Execute the actual ETL pipeline steps"""
    try:
        run_data = pipeline_runs[run_id]
        connector = SnowflakeConnector()
        
        # Step 1: Raw Data Validation
        run_data["current_step"] = "raw_validation"
        run_data["steps"].append({
            "name": "Raw Data Validation",
            "status": "running",
            "started_at": datetime.utcnow().isoformat()
        })
        
        await connector.connect()
        
        # Validate source table exists and has data
        source_table = f"{request.get('source_schema')}.{request.get('table_pattern')}"
        
        # First, get table schema to identify primary key
        schema_sql = f"""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = SPLIT_PART('{source_table}', '.', 2)
        AND TABLE_NAME = SPLIT_PART('{source_table}', '.', 3)
        ORDER BY ORDINAL_POSITION
        """
        
        schema_result = await connector.execute_query(schema_sql)
        
        # Find primary key or first column as fallback
        primary_key = None
        for col in schema_result:
            if 'ID' in col['COLUMN_NAME'].upper():
                primary_key = col['COLUMN_NAME']
                break
        
        if not primary_key and schema_result:
            primary_key = schema_result[0]['COLUMN_NAME']
        
        validation_sql = f"""
        SELECT 
            COUNT(*) as row_count,
            COUNT(DISTINCT {primary_key}) as unique_records,
            CURRENT_TIMESTAMP() as validation_time
        FROM {source_table}
        """
        
        raw_validation_result = await connector.execute_query(validation_sql)
        
        # Update step status
        run_data["steps"][-1].update({
            "status": "completed",
            "finished_at": datetime.utcnow().isoformat(),
            "result": raw_validation_result
        })
        
        await asyncio.sleep(1)  # Simulate processing time
        
        # Step 2: Prep Layer Transform
        run_data["current_step"] = "prep_transform"
        run_data["steps"].append({
            "name": "Prep Layer Transform",
            "status": "running", 
            "started_at": datetime.utcnow().isoformat()
        })
        
        # Create prep table with data cleaning
        prep_table = f"{request.get('target_schema')}.PREP_{request.get('table_pattern')}"
        
        prep_sql = f"""
        CREATE OR REPLACE TABLE {prep_table} AS
        SELECT 
            *,
            CASE 
                WHEN EMAIL IS NULL THEN 'MISSING_EMAIL'
                WHEN EMAIL NOT LIKE '%@%' THEN 'INVALID_EMAIL'
                ELSE 'VALID_EMAIL'
            END as email_quality_flag,
            CURRENT_TIMESTAMP() as processed_at
        FROM {source_table}
        WHERE {primary_key} IS NOT NULL
        """
        
        prep_result = await connector.execute_query(prep_sql)
        
        run_data["steps"][-1].update({
            "status": "completed",
            "finished_at": datetime.utcnow().isoformat(),
            "result": prep_result
        })
        
        await asyncio.sleep(2)  # Simulate processing time
        
        # Step 3: Mart Layer Aggregation
        run_data["current_step"] = "mart_aggregation"
        run_data["steps"].append({
            "name": "Mart Layer Aggregation",
            "status": "running",
            "started_at": datetime.utcnow().isoformat()
        })
        
        # Create mart table with business metrics
        mart_table = f"{request.get('target_schema')}.MART_{request.get('table_pattern')}_SUMMARY"
        
        mart_sql = f"""
        CREATE OR REPLACE TABLE {mart_table} AS
        SELECT 
            email_quality_flag,
            COUNT(*) as customer_count,
            COUNT(DISTINCT STATUS) as status_variety,
            AVG(CREDIT_SCORE) as avg_credit_score,
            MIN(REGISTRATION_DATE) as earliest_registration,
            MAX(REGISTRATION_DATE) as latest_registration,
            CURRENT_TIMESTAMP() as mart_created_at
        FROM {prep_table}
        GROUP BY email_quality_flag
        """
        
        mart_result = await connector.execute_query(mart_sql)
        
        run_data["steps"][-1].update({
            "status": "completed",
            "finished_at": datetime.utcnow().isoformat(),
            "result": mart_result
        })
        
        # Final validation
        validation_sql = f"SELECT * FROM {mart_table} ORDER BY customer_count DESC"
        final_result = await connector.execute_query(validation_sql)
        
        # Complete the run
        run_data.update({
            "status": "completed",
            "finished_at": datetime.utcnow().isoformat(),
            "current_step": "completed",
            "final_result": final_result,
            "summary": {
                "total_steps": len(run_data["steps"]),
                "successful_steps": len([s for s in run_data["steps"] if s["status"] == "completed"]),
                "tables_created": [prep_table, mart_table]
            }
        })
        
        await connector.disconnect()
        logger.info("ETL pipeline completed successfully", run_id=run_id)
        
    except Exception as e:
        logger.error("ETL pipeline failed", run_id=run_id, exc_info=e)
        run_data.update({
            "status": "failed",
            "finished_at": datetime.utcnow().isoformat(),
            "error": str(e),
            "current_step": "failed"
        })


@router.get("/etl/pipeline/{run_id}")
async def get_pipeline_status(run_id: str) -> Dict[str, Any]:
    """Get the current status of an ETL pipeline run"""
    if run_id not in pipeline_runs:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    
    return pipeline_runs[run_id]


@router.post("/etl/data/upload")
async def upload_test_data(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Upload test data file for ETL pipeline testing"""
    try:
        # Validate file type
        if not file.filename.endswith(('.csv', '.json', '.parquet')):
            raise HTTPException(status_code=400, detail="Unsupported file type. Use CSV, JSON, or Parquet.")
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # For demo, just return file info
        # In production, you'd upload to Snowflake stage or S3
        
        return {
            "filename": file.filename,
            "size_bytes": file_size,
            "size_mb": round(file_size / 1024 / 1024, 2),
            "type": file.content_type,
            "status": "uploaded",
            "message": f"File {file.filename} uploaded successfully"
        }
        
    except Exception as e:
        logger.error("File upload failed", filename=file.filename, exc_info=e)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/etl/pipeline/runs")
async def list_pipeline_runs() -> Dict[str, Any]:
    """List all pipeline runs"""
    return {
        "runs": list(pipeline_runs.values()),
        "total": len(pipeline_runs)
    }


@router.delete("/etl/pipeline/{run_id}")
async def cancel_pipeline_run(run_id: str) -> Dict[str, Any]:
    """Cancel a running pipeline"""
    if run_id not in pipeline_runs:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    
    run_data = pipeline_runs[run_id]
    if run_data["status"] == "running":
        run_data.update({
            "status": "cancelled",
            "finished_at": datetime.utcnow().isoformat(),
            "current_step": "cancelled"
        })
        
    return {"message": "Pipeline run cancelled", "run_id": run_id}
