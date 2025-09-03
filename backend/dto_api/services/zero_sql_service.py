"""
Zero-SQL Service: Natural Language to SQL Test Generation
"""
from typing import Dict, Any, List, Optional
import structlog

from dto_api.services.openai_adapter import OpenAIAdapter
from dto_api.services.local_ollama import LocalOllamaAdapter
from dto_api.adapters.connectors.snowflake import SnowflakeConnector

logger = structlog.get_logger()

class ZeroSQLService:
    """Service for converting natural language to SQL tests."""
    
    def __init__(self):
        self.openai_adapter = OpenAIAdapter()
        self.ollama_adapter = LocalOllamaAdapter()
        self.snowflake_connector = SnowflakeConnector()
    
    async def get_available_ai_provider(self) -> Optional[str]:
        """Get the first available AI provider."""
        
        # Check OpenAI first
        openai_health = await self.openai_adapter.health()
        if openai_health.get("status") == "healthy":
            return "openai"
        
        # Fallback to Ollama
        ollama_health = await self.ollama_adapter.health()
        if ollama_health.get("status") == "healthy":
            return "ollama"
        
        return None
    
    async def generate_test_from_natural_language(
        self, 
        natural_language: str,
        source_table: str,
        prep_table: str,
        mart_table: str
    ) -> Dict[str, Any]:
        """Generate SQL test from natural language description."""
        
        try:
            # Get table schemas
            table_schema = await self._get_table_schemas([source_table, prep_table, mart_table])
            
            # Get available AI provider
            provider = await self.get_available_ai_provider()
            if not provider:
                return {
                    "success": False,
                    "error": "No AI provider available. Configure OPENAI_API_KEY or start Ollama.",
                    "sql": None
                }
            
            # Generate SQL using available provider
            if provider == "openai":
                result = await self.openai_adapter.generate_sql_from_natural_language(
                    natural_language=natural_language,
                    table_schema=table_schema
                )
            else:  # ollama
                result = await self.ollama_adapter.generate_sql_from_natural_language(
                    natural_language=natural_language,
                    table_schema=table_schema
                )
            
            if result.get("success"):
                # Validate generated SQL
                validation = await self._validate_generated_sql(result["sql"])
                result["validation"] = validation
                result["provider"] = provider
            
            return result
            
        except Exception as e:
            logger.error("Zero-SQL generation failed", 
                        natural_language=natural_language, 
                        exc_info=e)
            return {
                "success": False,
                "error": str(e),
                "sql": None
            }
    
    async def get_test_suggestions(
        self,
        source_table: str,
        prep_table: str, 
        mart_table: str
    ) -> List[Dict[str, Any]]:
        """Get AI-generated test suggestions based on table schemas."""
        
        try:
            # Get table schemas
            table_schema = await self._get_table_schemas([source_table, prep_table, mart_table])
            
            # Get available AI provider
            provider = await self.get_available_ai_provider()
            if not provider:
                return []
            
            # Generate suggestions
            if provider == "openai":
                suggestions = await self.openai_adapter.generate_test_suggestions(table_schema)
            else:  # ollama
                suggestions = await self.ollama_adapter.generate_test_suggestions(table_schema)
            
            # Add provider info
            for suggestion in suggestions:
                suggestion["provider"] = provider
            
            return suggestions
            
        except Exception as e:
            logger.error("Failed to get test suggestions", exc_info=e)
            return []
    
    async def _get_table_schemas(self, table_names: List[str]) -> Dict[str, Any]:
        """Get schema information for tables."""
        
        schemas = {}
        
        try:
            await self.snowflake_connector.connect()
            
            for table_name in table_names:
                # Parse table name (DATABASE.SCHEMA.TABLE)
                parts = table_name.split('.')
                if len(parts) != 3:
                    continue
                
                database, schema, table = parts
                
                # Get column information
                describe_sql = f"DESCRIBE TABLE {table_name}"
                columns_result = await self.snowflake_connector.execute_query(describe_sql)
                
                # Format columns
                columns = []
                for col in columns_result:
                    columns.append({
                        "name": col.get("name"),
                        "type": col.get("type"),
                        "nullable": col.get("null?") == "Y",
                        "default": col.get("default"),
                        "primary_key": col.get("primary key") == "Y"
                    })
                
                schemas[table_name] = {
                    "database": database,
                    "schema": schema,
                    "table": table,
                    "columns": columns
                }
            
            await self.snowflake_connector.disconnect()
            
        except Exception as e:
            logger.error("Failed to get table schemas", exc_info=e)
        
        return schemas
    
    async def _validate_generated_sql(self, sql: str) -> Dict[str, Any]:
        """Validate generated SQL without executing it."""
        
        validation = {
            "is_valid": False,
            "is_safe": False,
            "issues": []
        }
        
        if not sql:
            validation["issues"].append("No SQL generated")
            return validation
        
        sql_upper = sql.upper().strip()
        
        # Check if it's a SELECT statement
        if not sql_upper.startswith("SELECT"):
            validation["issues"].append("Only SELECT statements are allowed")
            return validation
        
        # Check for dangerous keywords
        dangerous_keywords = [
            "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", 
            "TRUNCATE", "MERGE", "GRANT", "REVOKE"
        ]
        
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                validation["issues"].append(f"Dangerous keyword detected: {keyword}")
                return validation
        
        # Basic syntax validation (could be enhanced)
        if sql.count("(") != sql.count(")"):
            validation["issues"].append("Unmatched parentheses")
            return validation
        
        # If we get here, it looks safe
        validation["is_valid"] = True
        validation["is_safe"] = True
        
        return validation

# Example natural language prompts for testing:
EXAMPLE_PROMPTS = [
    "Check if all customer emails are valid (contain @ symbol)",
    "Count how many customers have missing registration dates", 
    "Verify that all customer IDs in PREP table exist in RAW table",
    "Check if email quality flags are correctly assigned based on email format",
    "Find duplicate customer records based on email address",
    "Validate that all aggregated counts in MART match the source data",
    "Check for customers with invalid status values",
    "Verify that processed_at timestamp is recent (within last 24 hours)"
]
