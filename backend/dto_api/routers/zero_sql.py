"""
Zero-SQL Router: Natural Language to SQL API
"""
from typing import List, Dict, Any
import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from dto_api.services.zero_sql_service import ZeroSQLService, EXAMPLE_PROMPTS

router = APIRouter()
logger = structlog.get_logger()

class NaturalLanguageRequest(BaseModel):
    natural_language: str
    source_table: str
    prep_table: str
    mart_table: str

class TestSuggestionsRequest(BaseModel):
    source_table: str
    prep_table: str
    mart_table: str

@router.post("/zero-sql/generate")
async def generate_sql_from_natural_language(request: NaturalLanguageRequest):
    """Convert natural language to SQL test."""
    
    try:
        zero_sql_service = ZeroSQLService()
        
        result = await zero_sql_service.generate_test_from_natural_language(
            natural_language=request.natural_language,
            source_table=request.source_table,
            prep_table=request.prep_table,
            mart_table=request.mart_table
        )
        
        return result
        
    except Exception as e:
        logger.error("Zero-SQL generation failed", exc_info=e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/zero-sql/suggestions")
async def get_test_suggestions(request: TestSuggestionsRequest):
    """Get AI-generated test suggestions for tables."""
    
    try:
        zero_sql_service = ZeroSQLService()
        
        suggestions = await zero_sql_service.get_test_suggestions(
            source_table=request.source_table,
            prep_table=request.prep_table,
            mart_table=request.mart_table
        )
        
        return {
            "suggestions": suggestions,
            "count": len(suggestions)
        }
        
    except Exception as e:
        logger.error("Test suggestions failed", exc_info=e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/zero-sql/examples")
async def get_example_prompts():
    """Get example natural language prompts."""
    
    return {
        "examples": EXAMPLE_PROMPTS,
        "count": len(EXAMPLE_PROMPTS)
    }

@router.get("/zero-sql/health")
async def get_ai_health():
    """Check AI provider health status."""
    
    try:
        zero_sql_service = ZeroSQLService()
        
        # Check both providers
        openai_health = await zero_sql_service.openai_adapter.health()
        ollama_health = await zero_sql_service.ollama_adapter.health()
        
        available_provider = await zero_sql_service.get_available_ai_provider()
        
        return {
            "available_provider": available_provider,
            "providers": {
                "openai": openai_health,
                "ollama": ollama_health
            },
            "status": "healthy" if available_provider else "no_providers_available"
        }
        
    except Exception as e:
        logger.error("AI health check failed", exc_info=e)
        raise HTTPException(status_code=500, detail=str(e))
