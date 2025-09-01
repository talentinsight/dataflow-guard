"""PostgreSQL connector adapter stub with SELECT-only guardrails."""

from typing import Dict, List, Any, Optional
import re

import structlog

logger = structlog.get_logger()


class PostgresConnector:
    """PostgreSQL database connector with read-only enforcement."""
    
    def __init__(self, connection_config: Dict[str, Any]):
        self.config = connection_config
        self.connection = None
        
        # Enforce read-only policy
        if not connection_config.get("read_only", True):
            raise ValueError("PostgreSQL connector must be configured as read-only")
    
    async def connect(self) -> None:
        """Establish connection to PostgreSQL."""
        try:
            logger.info("Connecting to PostgreSQL", host=self.config.get("host"))
            
            # TODO: Implement actual PostgreSQL connection
            # import asyncpg
            # self.connection = await asyncpg.connect(
            #     host=self.config["host"],
            #     port=self.config.get("port", 5432),
            #     user=self.config["username"],
            #     password=self.config["password"],
            #     database=self.config["database"]
            # )
            
            # Mock connection for stub
            self.connection = {"status": "connected", "type": "postgresql"}
            
            logger.info("PostgreSQL connection established")
            
        except Exception as e:
            logger.error("Failed to connect to PostgreSQL", exc_info=e)
            raise
    
    async def disconnect(self) -> None:
        """Close connection to PostgreSQL."""
        if self.connection:
            # TODO: Implement actual disconnection
            # await self.connection.close()
            self.connection = None
            logger.info("PostgreSQL connection closed")
    
    async def execute_query(self, sql: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute SQL query with SELECT-only enforcement."""
        try:
            # Enforce SELECT-only policy
            self._validate_read_only_sql(sql)
            
            logger.info("Executing PostgreSQL query", sql_preview=sql[:100])
            
            if not self.connection:
                await self.connect()
            
            # TODO: Implement actual query execution
            # results = await self.connection.fetch(sql, *(params.values() if params else []))
            # return [dict(record) for record in results]
            
            # Mock results for stub
            return [
                {"order_id": 12345, "order_total": 100.50, "customer_id": 1001},
                {"order_id": 12346, "order_total": 250.00, "customer_id": 1002}
            ]
            
        except Exception as e:
            logger.error("PostgreSQL query execution failed", sql=sql[:100], exc_info=e)
            raise
    
    async def explain_query(self, sql: str) -> Dict[str, Any]:
        """Get query execution plan."""
        try:
            explain_sql = f"EXPLAIN (FORMAT JSON, ANALYZE FALSE) {sql}"
            self._validate_read_only_sql(sql)  # Validate original query
            
            logger.info("Getting PostgreSQL query plan")
            
            # TODO: Implement actual EXPLAIN execution
            # results = await self.execute_query(explain_sql)
            
            # Mock explain result
            return {
                "query_plan": "Mock execution plan",
                "estimated_cost": 100.0,
                "estimated_rows": 1000,
                "operations": ["Seq Scan", "Filter", "Sort"]
            }
            
        except Exception as e:
            logger.error("Failed to explain PostgreSQL query", exc_info=e)
            raise
    
    async def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema information."""
        try:
            # Parse schema.table if provided
            schema_name = "public"
            if "." in table_name:
                schema_name, table_name = table_name.split(".", 1)
            
            sql = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns 
            WHERE table_schema = $1 AND table_name = $2
            ORDER BY ordinal_position
            """
            
            results = await self.execute_query(sql, {"schema": schema_name, "table": table_name})
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
                "last_analyzed": None  # Would get from pg_stat_user_tables
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
            'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE',
            'CREATE', 'ALTER', 'DROP', 'RENAME',
            'GRANT', 'REVOKE', 'SET',
            'CALL', 'COPY', 'VACUUM', 'ANALYZE'
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
            results = await self.execute_query("SELECT NOW() as test_time")
            
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
