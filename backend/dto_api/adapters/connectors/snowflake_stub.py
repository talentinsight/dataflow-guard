"""Snowflake connector adapter stub with SELECT-only guardrails."""

from typing import Dict, List, Any, Optional
import re

import structlog

logger = structlog.get_logger()


class SnowflakeConnector:
    """Snowflake database connector with read-only enforcement."""
    
    def __init__(self, connection_config: Dict[str, Any]):
        self.config = connection_config
        self.connection = None
        
        # Enforce read-only policy
        if not connection_config.get("read_only", True):
            raise ValueError("Snowflake connector must be configured as read-only")
    
    async def connect(self) -> None:
        """Establish connection to Snowflake."""
        try:
            logger.info("Connecting to Snowflake", account=self.config.get("host"))
            
            # TODO: Implement actual Snowflake connection
            # import snowflake.connector
            # self.connection = snowflake.connector.connect(
            #     account=self.config["host"],
            #     user=self.config["username"],
            #     password=self.config["password"],
            #     database=self.config["database"],
            #     schema=self.config.get("schema", "PUBLIC"),
            #     warehouse=self.config.get("warehouse"),
            #     role=self.config.get("role")
            # )
            
            # Mock connection for stub
            self.connection = {"status": "connected", "type": "snowflake"}
            
            logger.info("Snowflake connection established")
            
        except Exception as e:
            logger.error("Failed to connect to Snowflake", exc_info=e)
            raise
    
    async def disconnect(self) -> None:
        """Close connection to Snowflake."""
        if self.connection:
            # TODO: Implement actual disconnection
            # self.connection.close()
            self.connection = None
            logger.info("Snowflake connection closed")
    
    async def execute_query(self, sql: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute SQL query with SELECT-only enforcement."""
        try:
            # Enforce SELECT-only policy
            self._validate_read_only_sql(sql)
            
            logger.info("Executing Snowflake query", sql_preview=sql[:100])
            
            if not self.connection:
                await self.connect()
            
            # TODO: Implement actual query execution
            # cursor = self.connection.cursor()
            # cursor.execute(sql, params or {})
            # results = cursor.fetchall()
            # columns = [desc[0] for desc in cursor.description]
            # return [dict(zip(columns, row)) for row in results]
            
            # Mock results for stub
            return [
                {"ORDER_ID": 12345, "ORDER_TOTAL": 100.50, "CUSTOMER_ID": 1001},
                {"ORDER_ID": 12346, "ORDER_TOTAL": 250.00, "CUSTOMER_ID": 1002}
            ]
            
        except Exception as e:
            logger.error("Snowflake query execution failed", sql=sql[:100], exc_info=e)
            raise
    
    async def explain_query(self, sql: str) -> Dict[str, Any]:
        """Get query execution plan."""
        try:
            explain_sql = f"EXPLAIN {sql}"
            self._validate_read_only_sql(sql)  # Validate original query
            
            logger.info("Getting Snowflake query plan")
            
            # TODO: Implement actual EXPLAIN execution
            # results = await self.execute_query(explain_sql)
            
            # Mock explain result
            return {
                "query_plan": "Mock execution plan",
                "estimated_cost": 100,
                "estimated_rows": 1000,
                "operations": ["TableScan", "Filter", "Project"]
            }
            
        except Exception as e:
            logger.error("Failed to explain Snowflake query", exc_info=e)
            raise
    
    async def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema information."""
        try:
            # Use INFORMATION_SCHEMA to get column info
            sql = f"""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = '{table_name.upper()}'
            ORDER BY ORDINAL_POSITION
            """
            
            results = await self.execute_query(sql)
            return results
            
        except Exception as e:
            logger.error("Failed to get table schema", table_name=table_name, exc_info=e)
            raise
    
    async def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """Get basic table statistics."""
        try:
            sql = f"SELECT COUNT(*) as row_count FROM {table_name}"
            results = await self.execute_query(sql)
            
            return {
                "row_count": results[0]["row_count"] if results else 0,
                "last_analyzed": None  # Would get from Snowflake metadata
            }
            
        except Exception as e:
            logger.error("Failed to get table stats", table_name=table_name, exc_info=e)
            raise
    
    def _validate_read_only_sql(self, sql: str) -> None:
        """Validate SQL is read-only (SELECT/EXPLAIN only)."""
        sql_upper = sql.upper().strip()
        
        # Remove comments and normalize whitespace
        sql_clean = re.sub(r'--.*?\n', ' ', sql_upper)
        sql_clean = re.sub(r'/\*.*?\*/', ' ', sql_clean, flags=re.DOTALL)
        sql_clean = re.sub(r'\s+', ' ', sql_clean).strip()
        
        # Check for allowed statements
        allowed_prefixes = ['SELECT', 'WITH', 'EXPLAIN']
        
        if not any(sql_clean.startswith(prefix) for prefix in allowed_prefixes):
            raise ValueError(f"Only SELECT and EXPLAIN statements are allowed. Got: {sql_clean[:50]}")
        
        # Check for forbidden keywords (DDL/DML)
        forbidden_keywords = [
            'INSERT', 'UPDATE', 'DELETE', 'MERGE', 'TRUNCATE',
            'CREATE', 'ALTER', 'DROP', 'RENAME',
            'GRANT', 'REVOKE', 'SET', 'USE',
            'CALL', 'EXECUTE'
        ]
        
        for keyword in forbidden_keywords:
            if re.search(rf'\b{keyword}\b', sql_clean):
                raise ValueError(f"Forbidden SQL keyword detected: {keyword}")
        
        logger.debug("SQL validation passed", sql_preview=sql[:100])
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test database connectivity."""
        try:
            await self.connect()
            
            # Simple connectivity test
            results = await self.execute_query("SELECT CURRENT_TIMESTAMP() as test_time")
            
            await self.disconnect()
            
            return {
                "status": "success",
                "test_time": results[0]["test_time"] if results else None,
                "message": "Connection test successful"
            }
            
        except Exception as e:
            logger.error("Connection test failed", exc_info=e)
            return {
                "status": "failed",
                "error": str(e),
                "message": "Connection test failed"
            }
