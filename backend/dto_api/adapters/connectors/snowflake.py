"""Real Snowflake connector with SELECT-only guardrails and EXPLAIN pre-check."""

import os
import re
import json
import hashlib
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone
from pathlib import Path

import structlog
import snowflake.connector
from snowflake.connector import DictCursor
from snowflake.connector.errors import Error as SnowflakeError

from dto_api.policies.pii_redaction import PIIRedactionPolicy

logger = structlog.get_logger()


class SnowflakeConnector:
    """Real Snowflake database connector with read-only enforcement."""
    
    def __init__(self, settings: Optional[Dict[str, Any]] = None):
        """Initialize Snowflake connector with settings or environment variables."""
        self.settings = settings or self._load_from_env()
        self.connection = None
        self.pii_policy = PIIRedactionPolicy(enabled=True)
        
        # Validate required settings
        self._validate_settings()
        
        # Security settings from environment
        self.select_timeout = int(os.getenv('DFG_SELECT_TIMEOUT', '60'))
        self.scan_budget_bytes = int(os.getenv('DFG_SCAN_BUDGET_BYTES', '0'))
        self.sample_limit = int(os.getenv('DFG_SAMPLE_LIMIT', '1000'))
        self.allowed_schemas = self._parse_allowed_schemas()
        self.query_tag = os.getenv('DFG_QUERY_TAG', 'DataFlowGuard')
        self.log_pii = os.getenv('DFG_LOG_PII', 'false').lower() == 'true'
        
        # SQL validation patterns
        self._forbidden_keywords = [
            'INSERT', 'UPDATE', 'DELETE', 'MERGE', 'CREATE', 'ALTER', 'DROP',
            'TRUNCATE', 'GRANT', 'REVOKE', 'CALL', 'USE', 'COPY', 'PUT', 'GET',
            'BEGIN', 'COMMIT', 'ROLLBACK', 'SET', 'UNSET'
        ]
    
    def _load_from_env(self) -> Dict[str, Any]:
        """Load Snowflake settings from environment variables."""
        settings = {
            'account': os.getenv('SNOWFLAKE_ACCOUNT'),
            'user': os.getenv('SNOWFLAKE_USER'),
            'password': os.getenv('SNOWFLAKE_PASSWORD'),
            'private_key_path': os.getenv('SNOWFLAKE_PRIVATE_KEY_PATH'),
            'private_key_passphrase': os.getenv('SNOWFLAKE_PRIVATE_KEY_PASSPHRASE'),
            'role': os.getenv('SNOWFLAKE_ROLE'),
            'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
            'database': os.getenv('SNOWFLAKE_DATABASE'),
            'schema': os.getenv('SNOWFLAKE_SCHEMA'),
            'region': os.getenv('SNOWFLAKE_REGION'),
            'host': os.getenv('SNOWFLAKE_HOST'),
        }
        
        # Remove None values
        return {k: v for k, v in settings.items() if v is not None}
    
    def _validate_settings(self) -> None:
        """Validate required Snowflake settings."""
        required = ['account', 'user']
        missing = [key for key in required if not self.settings.get(key)]
        
        if missing:
            raise ValueError(f"Missing required Snowflake settings: {missing}")
        
        # Must have either password or private key
        has_password = bool(self.settings.get('password'))
        has_private_key = bool(self.settings.get('private_key_path'))
        
        if not (has_password or has_private_key):
            raise ValueError("Must provide either password or private_key_path for authentication")
    
    def _parse_allowed_schemas(self) -> List[str]:
        """Parse allowed schemas from environment."""
        allowed = os.getenv('DFG_ALLOWED_SCHEMAS', '')
        if not allowed:
            return []
        return [schema.strip() for schema in allowed.split(',')]
    
    def _load_private_key(self) -> Optional[bytes]:
        """Load private key from file if specified."""
        key_path = self.settings.get('private_key_path')
        if not key_path:
            return None
        
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.serialization import load_pem_private_key
            
            with open(key_path, 'rb') as key_file:
                private_key_data = key_file.read()
            
            passphrase = self.settings.get('private_key_passphrase')
            passphrase_bytes = passphrase.encode() if passphrase else None
            
            private_key = load_pem_private_key(
                private_key_data,
                password=passphrase_bytes
            )
            
            return private_key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
        except Exception as e:
            logger.error("Failed to load private key", key_path=key_path, error=str(e))
            raise ValueError(f"Failed to load private key: {e}")
    
    async def connect(self) -> None:
        """Establish connection to Snowflake with security settings."""
        try:
            logger.info("Connecting to Snowflake", account=self.settings.get('account'))
            
            # Build connection parameters
            conn_params = {
                'account': self.settings['account'],
                'user': self.settings['user'],
            }
            
            # Add authentication
            if self.settings.get('password'):
                conn_params['password'] = self.settings['password']
            elif self.settings.get('private_key_path'):
                conn_params['private_key'] = self._load_private_key()
            
            # Add optional parameters
            for key in ['role', 'warehouse', 'database', 'schema', 'region', 'host']:
                if self.settings.get(key):
                    conn_params[key] = self.settings[key]
            
            # Security and session parameters
            conn_params.update({
                'session_parameters': {
                    'QUERY_TAG': self.query_tag,
                    'STATEMENT_TIMEOUT_IN_SECONDS': self.select_timeout,
                    'JDBC_QUERY_RESULT_FORMAT': 'JSON',
                }
            })
            
            # Establish connection
            self.connection = snowflake.connector.connect(**conn_params)
            
            logger.info(
                "Snowflake connection established",
                account=self.settings.get('account'),
                role=self.settings.get('role'),
                warehouse=self.settings.get('warehouse')
            )
            
        except Exception as e:
            logger.error("Failed to connect to Snowflake", error=str(e))
            raise
    
    async def disconnect(self) -> None:
        """Close connection to Snowflake."""
        if self.connection:
            try:
                self.connection.close()
                logger.info("Snowflake connection closed")
            except Exception as e:
                logger.warning("Error closing Snowflake connection", error=str(e))
            finally:
                self.connection = None
    
    def _validate_sql(self, sql: str) -> None:
        """Validate SQL is SELECT-only and follows security rules."""
        # Normalize SQL
        sql_clean = re.sub(r'--.*?\n', ' ', sql, flags=re.MULTILINE)
        sql_clean = re.sub(r'/\*.*?\*/', ' ', sql_clean, flags=re.DOTALL)
        sql_clean = re.sub(r'\s+', ' ', sql_clean).strip()
        sql_upper = sql_clean.upper()
        
        # Check for single statement
        statements = [s.strip() for s in sql_clean.split(';') if s.strip()]
        if len(statements) > 1:
            raise ValueError("Only single statements are allowed")
        
        # Check for allowed statement types
        allowed_prefixes = ['SELECT', 'WITH', 'EXPLAIN']
        if not any(sql_upper.startswith(prefix) for prefix in allowed_prefixes):
            raise ValueError(f"Only SELECT, WITH, and EXPLAIN statements are allowed. Got: {sql_upper[:50]}")
        
        # Check for forbidden keywords
        for keyword in self._forbidden_keywords:
            if re.search(rf'\b{keyword}\b', sql_upper):
                raise ValueError(f"Forbidden SQL keyword detected: {keyword}")
        
        # Validate allowed schemas if configured
        if self.allowed_schemas:
            self._validate_schema_access(sql_upper)
        
        logger.debug("SQL validation passed", sql_preview=sql[:100])
    
    def _validate_schema_access(self, sql_upper: str) -> None:
        """Validate SQL only accesses allowed schemas."""
        # Extract potential schema references (simplified pattern matching)
        schema_patterns = [
            r'\bFROM\s+([A-Z_][A-Z0-9_]*\.[A-Z_][A-Z0-9_]*\.[A-Z_][A-Z0-9_]*)',
            r'\bJOIN\s+([A-Z_][A-Z0-9_]*\.[A-Z_][A-Z0-9_]*\.[A-Z_][A-Z0-9_]*)',
            r'\b([A-Z_][A-Z0-9_]*\.[A-Z_][A-Z0-9_]*\.[A-Z_][A-Z0-9_]*)',
        ]
        
        referenced_schemas = set()
        for pattern in schema_patterns:
            matches = re.findall(pattern, sql_upper)
            for match in matches:
                # Extract database.schema part
                parts = match.split('.')
                if len(parts) >= 2:
                    schema_ref = f"{parts[0]}.{parts[1]}"
                    referenced_schemas.add(schema_ref)
        
        # Check if all referenced schemas are allowed
        for schema_ref in referenced_schemas:
            if schema_ref not in self.allowed_schemas:
                raise ValueError(f"Access to schema '{schema_ref}' is not allowed. Allowed schemas: {self.allowed_schemas}")
    
    def _get_query_history(self, query_id: str) -> Dict[str, Any]:
        """Get query execution statistics from query history."""
        try:
            cursor = self.connection.cursor(DictCursor)
            
            # Query the query history for metrics
            history_sql = """
            SELECT 
                QUERY_ID,
                BYTES_SCANNED,
                EXECUTION_TIME,
                ROWS_PRODUCED,
                WAREHOUSE_NAME,
                ROLE_NAME,
                DATABASE_NAME,
                SCHEMA_NAME
            FROM INFORMATION_SCHEMA.QUERY_HISTORY 
            WHERE QUERY_ID = %s
            """
            
            cursor.execute(history_sql, (query_id,))
            result = cursor.fetchone()
            
            if result:
                return {
                    'bytes_scanned': result.get('BYTES_SCANNED', 0),
                    'elapsed_ms': result.get('EXECUTION_TIME', 0),
                    'rows': result.get('ROWS_PRODUCED', 0),
                    'warehouse': result.get('WAREHOUSE_NAME'),
                    'role': result.get('ROLE_NAME'),
                    'database': result.get('DATABASE_NAME'),
                    'schema': result.get('SCHEMA_NAME'),
                }
            else:
                logger.warning("Query not found in history", query_id=query_id)
                return {}
                
        except Exception as e:
            logger.warning("Failed to get query history", query_id=query_id, error=str(e))
            return {}
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test database connectivity and return connection info."""
        try:
            if not self.connection:
                await self.connect()
            
            cursor = self.connection.cursor(DictCursor)
            
            # Test query with connection info
            test_sql = """
            SELECT 
                CURRENT_TIMESTAMP() as test_time,
                CURRENT_ROLE() as current_role,
                CURRENT_WAREHOUSE() as current_warehouse,
                CURRENT_DATABASE() as current_database,
                CURRENT_SCHEMA() as current_schema,
                CURRENT_ACCOUNT() as current_account
            """
            
            cursor.execute(test_sql)
            result = cursor.fetchone()
            
            return {
                'status': 'success',
                'test_time': result['TEST_TIME'].isoformat() if result['TEST_TIME'] else None,
                'connection_info': {
                    'role': result.get('CURRENT_ROLE'),
                    'warehouse': result.get('CURRENT_WAREHOUSE'),
                    'database': result.get('CURRENT_DATABASE'),
                    'schema': result.get('CURRENT_SCHEMA'),
                    'account': result.get('CURRENT_ACCOUNT'),
                },
                'message': 'Connection test successful'
            }
            
        except Exception as e:
            logger.error("Connection test failed", error=str(e))
            return {
                'status': 'failed',
                'error': str(e),
                'message': 'Connection test failed'
            }
    
    async def explain(self, sql: str) -> Dict[str, Any]:
        """Get query execution plan using EXPLAIN."""
        try:
            # Validate SQL first
            self._validate_sql(sql)
            
            if not self.connection:
                await self.connect()
            
            cursor = self.connection.cursor(DictCursor)
            
            # Run EXPLAIN USING TEXT
            explain_sql = f"EXPLAIN USING TEXT {sql}"
            
            logger.info("Running EXPLAIN", sql_preview=sql[:100])
            
            cursor.execute(explain_sql)
            explain_results = cursor.fetchall()
            
            # Extract plan text
            plan_text = '\n'.join([row.get('step', '') for row in explain_results if row.get('step')])
            
            # Generate plan hash for audit
            plan_hash = hashlib.sha256(plan_text.encode()).hexdigest()[:16]
            
            # Check scan budget if configured
            estimated_bytes = self._estimate_scan_bytes(plan_text)
            if self.scan_budget_bytes > 0 and estimated_bytes > self.scan_budget_bytes:
                raise ValueError(f"Estimated scan bytes ({estimated_bytes}) exceeds budget ({self.scan_budget_bytes})")
            
            return {
                'plan_text': plan_text,
                'plan_hash': plan_hash,
                'estimated_bytes': estimated_bytes,
                'explain_results': explain_results,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error("EXPLAIN failed", sql_preview=sql[:100], error=str(e))
            raise
    
    def _estimate_scan_bytes(self, plan_text: str) -> int:
        """Estimate bytes to be scanned from execution plan (heuristic)."""
        # This is a simplified heuristic - in practice you'd parse the plan more carefully
        # Look for table scan operations and size estimates
        
        # Simple pattern matching for common size indicators
        size_patterns = [
            r'(\d+)\s*bytes',
            r'(\d+)\s*MB',
            r'(\d+)\s*GB',
        ]
        
        total_bytes = 0
        for pattern in size_patterns:
            matches = re.findall(pattern, plan_text, re.IGNORECASE)
            for match in matches:
                size = int(match)
                if 'MB' in pattern:
                    size *= 1024 * 1024
                elif 'GB' in pattern:
                    size *= 1024 * 1024 * 1024
                total_bytes += size
        
        return total_bytes
    
    async def select(self, sql: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """Execute SELECT query with security controls."""
        try:
            # Validate SQL first
            self._validate_sql(sql)
            
            if not self.connection:
                await self.connect()
            
            # Apply limit if specified
            if limit:
                if 'LIMIT' not in sql.upper():
                    sql = f"{sql.rstrip(';')} LIMIT {min(limit, self.sample_limit)}"
            
            cursor = self.connection.cursor(DictCursor)
            
            logger.info(
                "Executing SELECT query",
                sql_preview=sql[:100] if not self.log_pii else "[REDACTED]",
                limit=limit
            )
            
            start_time = datetime.now(timezone.utc)
            cursor.execute(sql)
            results = cursor.fetchall()
            end_time = datetime.now(timezone.utc)
            
            # Get query ID for metrics
            query_id = cursor.sfqid
            
            # Get execution statistics
            stats = self._get_query_history(query_id)
            stats['elapsed_ms'] = int((end_time - start_time).total_seconds() * 1000)
            
            # Check scan budget post-execution
            bytes_scanned = stats.get('bytes_scanned', 0)
            if self.scan_budget_bytes > 0 and bytes_scanned > self.scan_budget_bytes:
                logger.warning(
                    "Query exceeded scan budget",
                    query_id=query_id,
                    bytes_scanned=bytes_scanned,
                    budget=self.scan_budget_bytes
                )
            
            # Apply PII redaction to results
            masked_results = self.pii_policy.redact_sample_data(results)
            
            logger.info(
                "SELECT query completed",
                query_id=query_id,
                rows_returned=len(results),
                bytes_scanned=bytes_scanned,
                elapsed_ms=stats['elapsed_ms']
            )
            
            return {
                'query_id': query_id,
                'rows': masked_results,
                'stats': stats,
                'plan_text': '',  # Would be populated if EXPLAIN was run first
                'warehouse': stats.get('warehouse'),
                'role': stats.get('role'),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error("SELECT query failed", sql_preview=sql[:100], error=str(e))
            raise
    
    async def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema information."""
        try:
            if not self.connection:
                await self.connect()
            
            # Parse table name
            parts = table_name.split('.')
            if len(parts) == 3:
                database, schema, table = parts
            elif len(parts) == 2:
                database = self.settings.get('database')
                schema, table = parts
            else:
                database = self.settings.get('database')
                schema = self.settings.get('schema')
                table = parts[0]
            
            cursor = self.connection.cursor(DictCursor)
            
            schema_sql = """
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_DEFAULT,
                COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_CATALOG = %s 
              AND TABLE_SCHEMA = %s 
              AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
            """
            
            cursor.execute(schema_sql, (database, schema, table))
            results = cursor.fetchall()
            
            return [
                {
                    'name': row['COLUMN_NAME'],
                    'type': row['DATA_TYPE'],
                    'nullable': row['IS_NULLABLE'] == 'YES',
                    'default': row['COLUMN_DEFAULT'],
                    'comment': row['COMMENT']
                }
                for row in results
            ]
            
        except Exception as e:
            logger.error("Failed to get table schema", table_name=table_name, error=str(e))
            raise
    
    async def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """Get basic table statistics."""
        try:
            # Simple row count query
            count_sql = f"SELECT COUNT(*) as row_count FROM {table_name}"
            result = await self.select(count_sql)
            
            row_count = result['rows'][0]['ROW_COUNT'] if result['rows'] else 0
            
            return {
                'row_count': row_count,
                'last_analyzed': None,  # Would need additional queries to get this
                'query_id': result['query_id']
            }
            
        except Exception as e:
            logger.error("Failed to get table stats", table_name=table_name, error=str(e))
            raise
