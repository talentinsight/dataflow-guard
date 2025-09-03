"""
OpenAI Adapter for Zero-SQL Natural Language to SQL Generation
"""
import os
import json
from typing import Dict, Any, List, Optional
import structlog
try:
    import openai
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None
    AsyncOpenAI = None

from dto_api.services.ai_adapter_iface import AIAdapterInterface

logger = structlog.get_logger()

class OpenAIAdapter(AIAdapterInterface):
    """OpenAI GPT adapter for natural language to SQL conversion."""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4')
        self.client = None
        
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI package not installed. Install with: pip install openai")
            return
        
        if self.api_key and AsyncOpenAI:
            self.client = AsyncOpenAI(api_key=self.api_key)
    
    async def health(self) -> Dict[str, Any]:
        """Check OpenAI API health."""
        if not OPENAI_AVAILABLE:
            return {
                "status": "unavailable",
                "error": "OpenAI package not installed. Run: pip install openai",
                "model": None
            }
        
        if not self.api_key:
            return {
                "status": "unavailable",
                "error": "OPENAI_API_KEY not configured",
                "model": None
            }
        
        if not self.client:
            return {
                "status": "error", 
                "error": "OpenAI client not initialized",
                "model": self.model
            }
        
        try:
            # Test with a simple completion
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            return {
                "status": "healthy",
                "model": self.model,
                "usage": response.usage.dict() if response.usage else None
            }
        except Exception as e:
            logger.error("OpenAI health check failed", exc_info=e)
            return {
                "status": "error",
                "error": str(e),
                "model": self.model
            }
    
    async def generate_sql_from_natural_language(
        self, 
        natural_language: str, 
        table_schema: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Convert natural language to SQL query."""
        
        if not self.client:
            return {
                "success": False,
                "error": "OpenAI client not available",
                "sql": None
            }
        
        try:
            # Build schema context
            schema_context = self._build_schema_context(table_schema)
            
            # Create prompt for SQL generation
            system_prompt = f"""You are an expert SQL analyst. Convert natural language requests to SQL queries.

SCHEMA CONTEXT:
{schema_context}

RULES:
1. Generate ONLY SELECT statements (no INSERT/UPDATE/DELETE)
2. Use proper table aliases and joins when needed
3. Include appropriate WHERE clauses for data quality checks
4. Return valid SQL that can be executed directly
5. Focus on data validation and quality metrics

Return response as JSON:
{{
    "sql": "SELECT ...",
    "explanation": "Brief explanation of what the query does",
    "test_type": "data_quality|row_count|transformation_validation|business_rules"
}}"""

            user_prompt = f"""Convert this natural language request to SQL:

"{natural_language}"

Generate a SQL query that validates or tests this requirement."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.1  # Low temperature for consistent SQL generation
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                result = json.loads(content)
                return {
                    "success": True,
                    "sql": result.get("sql"),
                    "explanation": result.get("explanation"),
                    "test_type": result.get("test_type", "data_quality"),
                    "usage": response.usage.dict() if response.usage else None
                }
            except json.JSONDecodeError:
                # Fallback: extract SQL from response
                sql = self._extract_sql_from_text(content)
                return {
                    "success": True,
                    "sql": sql,
                    "explanation": "Generated from natural language",
                    "test_type": "data_quality",
                    "usage": response.usage.dict() if response.usage else None
                }
                
        except Exception as e:
            logger.error("OpenAI SQL generation failed", 
                        natural_language=natural_language, 
                        exc_info=e)
            return {
                "success": False,
                "error": str(e),
                "sql": None
            }
    
    async def generate_test_suggestions(
        self, 
        table_schema: Dict[str, Any],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Generate test suggestions based on table schema."""
        
        if not self.client:
            return []
        
        try:
            schema_context = self._build_schema_context(table_schema)
            
            prompt = f"""Analyze this database schema and suggest data quality tests:

SCHEMA:
{schema_context}

Generate 5-8 specific test suggestions in JSON format:
[
    {{
        "test_name": "Check for NULL emails",
        "natural_language": "Find rows where email is null or empty",
        "test_type": "data_quality",
        "priority": "high"
    }},
    ...
]

Focus on:
- Data quality issues (nulls, duplicates, format validation)
- Business rule validation
- Referential integrity
- Data transformation accuracy"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            
            try:
                suggestions = json.loads(content)
                return suggestions if isinstance(suggestions, list) else []
            except json.JSONDecodeError:
                logger.warning("Failed to parse test suggestions JSON")
                return []
                
        except Exception as e:
            logger.error("Failed to generate test suggestions", exc_info=e)
            return []
    
    def _build_schema_context(self, table_schema: Dict[str, Any]) -> str:
        """Build schema context for AI prompts."""
        context_parts = []
        
        for table_name, schema_info in table_schema.items():
            context_parts.append(f"TABLE: {table_name}")
            
            if "columns" in schema_info:
                for col in schema_info["columns"]:
                    col_info = f"  - {col.get('name', 'unknown')}: {col.get('type', 'unknown')}"
                    if col.get('nullable') is False:
                        col_info += " NOT NULL"
                    if col.get('primary_key'):
                        col_info += " PRIMARY KEY"
                    context_parts.append(col_info)
            
            context_parts.append("")  # Empty line between tables
        
        return "\n".join(context_parts)
    
    def _extract_sql_from_text(self, text: str) -> Optional[str]:
        """Extract SQL from text response."""
        # Look for SQL between ```sql and ``` or just ```
        import re
        
        # Try to find SQL block
        sql_pattern = r'```(?:sql)?\s*(SELECT.*?)```'
        match = re.search(sql_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        # Fallback: look for SELECT statement
        select_pattern = r'(SELECT\s+.*?)(?:\n\n|\Z)'
        match = re.search(select_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        return None
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generic text generation (legacy interface)."""
        if not self.client:
            return "OpenAI client not available"
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get('max_tokens', 200),
                temperature=kwargs.get('temperature', 0.7)
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error("OpenAI generation failed", exc_info=e)
            return f"Error: {str(e)}"
