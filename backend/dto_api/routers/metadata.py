"""
Snowflake Metadata Browser
Real-time database, schema, and table discovery
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import structlog

from dto_api.adapters.connectors.snowflake import SnowflakeConnector

router = APIRouter()
logger = structlog.get_logger()

@router.get("/metadata/databases")
async def get_databases() -> Dict[str, Any]:
    """Get all available databases from Snowflake."""
    try:
        connector = SnowflakeConnector()
        await connector.connect()
        
        # Use SHOW DATABASES which works without INFORMATION_SCHEMA
        result = await connector.execute_query("SHOW DATABASES")
        await connector.disconnect()
        
        # Filter out system databases
        databases = [
            {
                "DATABASE_NAME": row.get("name", ""),
                "CREATED": row.get("created_on", ""),
                "COMMENT": row.get("comment", "")
            }
            for row in result
            if row.get("name", "").upper() not in ["INFORMATION_SCHEMA", "SNOWFLAKE", "SNOWFLAKE_SAMPLE_DATA"]
        ]
        
        return {
            "databases": databases,
            "count": len(databases)
        }
        
    except Exception as e:
        logger.error("Failed to get databases", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to get databases: {str(e)}")


@router.get("/metadata/schemas/{database_name}")
async def get_schemas(database_name: str) -> Dict[str, Any]:
    """Get all schemas in a database."""
    try:
        connector = SnowflakeConnector()
        await connector.connect()
        
        sql = f"SHOW SCHEMAS IN DATABASE {database_name}"
        
        result = await connector.execute_query(sql)
        await connector.disconnect()
        
        # Filter out system schemas and format response
        schemas = [
            {
                "SCHEMA_NAME": row.get("name", ""),
                "CREATED": row.get("created_on", ""),
                "COMMENT": row.get("comment", "")
            }
            for row in result
            if row.get("name", "").upper() not in ["INFORMATION_SCHEMA"]
        ]
        
        return {
            "database": database_name,
            "schemas": schemas,
            "count": len(schemas)
        }
        
    except Exception as e:
        logger.error("Failed to get schemas", database=database_name, exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to get schemas: {str(e)}")


@router.get("/metadata/tables/{database_name}/{schema_name}")
async def get_tables(database_name: str, schema_name: str) -> Dict[str, Any]:
    """Get all tables in a schema."""
    try:
        connector = SnowflakeConnector()
        await connector.connect()
        
        sql = f"SHOW TABLES IN SCHEMA {database_name}.{schema_name}"
        
        result = await connector.execute_query(sql)
        await connector.disconnect()
        
        # Format response
        tables = [
            {
                "TABLE_NAME": row.get("name", ""),
                "TABLE_TYPE": row.get("kind", ""),
                "ROW_COUNT": row.get("rows", 0),
                "BYTES": row.get("bytes", 0),
                "CREATED": row.get("created_on", ""),
                "COMMENT": row.get("comment", "")
            }
            for row in result
        ]
        
        return {
            "database": database_name,
            "schema": schema_name,
            "tables": tables,
            "count": len(tables)
        }
        
    except Exception as e:
        logger.error("Failed to get tables", database=database_name, schema=schema_name, exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to get tables: {str(e)}")


@router.get("/metadata/columns/{database_name}/{schema_name}/{table_name}")
async def get_columns(database_name: str, schema_name: str, table_name: str) -> Dict[str, Any]:
    """Get all columns in a table."""
    try:
        connector = SnowflakeConnector()
        await connector.connect()
        
        sql = f"DESCRIBE TABLE {database_name}.{schema_name}.{table_name}"
        
        result = await connector.execute_query(sql)
        await connector.disconnect()
        
        # Format columns response
        columns = [
            {
                "COLUMN_NAME": row.get("name", ""),
                "DATA_TYPE": row.get("type", ""),
                "IS_NULLABLE": row.get("null?", ""),
                "COLUMN_DEFAULT": row.get("default", ""),
                "COMMENT": row.get("comment", "")
            }
            for row in result
        ]
        
        return {
            "database": database_name,
            "schema": schema_name,
            "table": table_name,
            "columns": columns,
            "column_count": len(columns)
        }
        
    except Exception as e:
        logger.error("Failed to get columns", 
                    database=database_name, 
                    schema=schema_name, 
                    table=table_name, 
                    exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to get columns: {str(e)}")


@router.get("/metadata/browse")
async def browse_metadata() -> Dict[str, Any]:
    """Get complete metadata hierarchy for UI tree view."""
    try:
        connector = SnowflakeConnector()
        await connector.connect()
        
        # Get databases with their schemas and tables
        hierarchy_sql = """
        SELECT 
            d.DATABASE_NAME,
            s.SCHEMA_NAME,
            t.TABLE_NAME,
            t.ROW_COUNT,
            t.BYTES
        FROM INFORMATION_SCHEMA.DATABASES d
        LEFT JOIN INFORMATION_SCHEMA.SCHEMATA s ON d.DATABASE_NAME = s.CATALOG_NAME
        LEFT JOIN INFORMATION_SCHEMA.TABLES t ON s.TABLE_SCHEMA = t.TABLE_SCHEMA 
            AND s.CATALOG_NAME = t.TABLE_CATALOG
        WHERE d.DATABASE_NAME NOT IN ('INFORMATION_SCHEMA', 'SNOWFLAKE')
        AND (s.SCHEMA_NAME IS NULL OR s.SCHEMA_NAME NOT IN ('INFORMATION_SCHEMA'))
        AND (t.TABLE_TYPE IS NULL OR t.TABLE_TYPE = 'BASE TABLE')
        ORDER BY d.DATABASE_NAME, s.SCHEMA_NAME, t.TABLE_NAME
        """
        
        result = await connector.execute_query(hierarchy_sql)
        await connector.disconnect()
        
        # Build hierarchical structure
        hierarchy = {}
        for row in result:
            db_name = row['DATABASE_NAME']
            schema_name = row['SCHEMA_NAME']
            table_name = row['TABLE_NAME']
            
            if db_name not in hierarchy:
                hierarchy[db_name] = {}
            
            if schema_name and schema_name not in hierarchy[db_name]:
                hierarchy[db_name][schema_name] = []
            
            if table_name and schema_name:
                hierarchy[db_name][schema_name].append({
                    "name": table_name,
                    "row_count": row.get('ROW_COUNT', 0),
                    "size_bytes": row.get('BYTES', 0)
                })
        
        return {
            "hierarchy": hierarchy,
            "total_databases": len(hierarchy),
            "total_schemas": sum(len(schemas) for schemas in hierarchy.values()),
            "total_tables": sum(
                len(tables) 
                for schemas in hierarchy.values() 
                for tables in schemas.values()
            )
        }
        
    except Exception as e:
        logger.error("Failed to browse metadata", exc_info=e)
        raise HTTPException(status_code=500, detail=f"Failed to browse metadata: {str(e)}")
