"""vLLM AI adapter with deterministic stub mode."""

import json
import hashlib
from typing import Dict, Any, Optional, List
import httpx
import structlog

from dto_api.models.tests import CompileRequest, CompileResponse
from dto_api.services.ai_adapter_iface import AIAdapterInterface

logger = structlog.get_logger()


class VLLMAdapter(AIAdapterInterface):
    """vLLM AI adapter with fallback to deterministic stub mode."""
    
    def __init__(self, base_url: str = "http://localhost:8000", model: str = "microsoft/DialoGPT-medium"):
        super().__init__()
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.provider = "vllm"
        self._client = httpx.AsyncClient(timeout=60.0)
        self._is_available = None  # Cache availability check
    
    async def health(self) -> Dict[str, Any]:
        """Check vLLM service health and model availability."""
        try:
            # Check if vLLM service is running
            response = await self._client.get(f"{self.base_url}/v1/models")
            if response.status_code == 200:
                models_data = response.json()
                models = models_data.get("data", [])
                model_ids = [m.get("id", "") for m in models]
                
                # Check if our specific model is available
                model_available = any(self.model in model_id for model_id in model_ids)
                
                if model_available:
                    self._is_available = True
                    return {
                        "ok": True,
                        "provider": self.provider,
                        "detail": f"vLLM service healthy, model '{self.model}' available",
                        "models": model_ids,
                        "base_url": self.base_url
                    }
                else:
                    self._is_available = False
                    return {
                        "ok": False,
                        "provider": self.provider,
                        "detail": f"vLLM service healthy but model '{self.model}' not found. Available: {model_ids}",
                        "models": model_ids,
                        "base_url": self.base_url
                    }
            else:
                self._is_available = False
                return {
                    "ok": False,
                    "provider": self.provider,
                    "detail": f"vLLM service returned status {response.status_code}",
                    "base_url": self.base_url
                }
                
        except httpx.ConnectError:
            self._is_available = False
            return {
                "ok": False,
                "provider": self.provider,
                "detail": f"Cannot connect to vLLM service at {self.base_url}",
                "base_url": self.base_url
            }
        except Exception as e:
            self._is_available = False
            return {
                "ok": False,
                "provider": self.provider,
                "detail": f"Health check failed: {str(e)}",
                "base_url": self.base_url
            }
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using vLLM or deterministic stub mode."""
        if not prompt:
            raise ValueError("Prompt cannot be empty")
        
        if len(prompt) > 20000:
            raise ValueError("Prompt too long (max 20000 characters)")
        
        # Check if vLLM is available (use cached result if available)
        if self._is_available is None:
            health_result = await self.health()
            self._is_available = health_result["ok"]
        
        if self._is_available:
            try:
                return await self._generate_with_vllm(prompt, **kwargs)
            except Exception as e:
                logger.warning("vLLM generation failed, falling back to stub mode", error=str(e))
                return self._generate_stub(prompt, **kwargs)
        else:
            logger.info("vLLM not available, using deterministic stub mode")
            return self._generate_stub(prompt, **kwargs)
    
    async def _generate_with_vllm(self, prompt: str, **kwargs) -> str:
        """Generate text using actual vLLM service via OpenAI-compatible API."""
        # Extract parameters with defaults
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", 1000)
        seed = kwargs.get("seed", self.seed)
        
        # vLLM uses OpenAI-compatible API
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "top_p": self.top_p,
            "max_tokens": max_tokens,
            "seed": int(seed),
            "stream": False
        }
        
        response = await self._client.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            raise Exception(f"vLLM API returned status {response.status_code}: {response.text}")
        
        result = response.json()
        
        # Extract response from OpenAI-compatible format
        choices = result.get("choices", [])
        if not choices:
            raise Exception("vLLM returned no choices")
        
        message = choices[0].get("message", {})
        generated_text = message.get("content", "")
        
        if not generated_text:
            raise Exception("vLLM returned empty response")
        
        logger.info(
            "vLLM generation completed",
            model=self.model,
            prompt_length=len(prompt),
            response_length=len(generated_text),
            temperature=temperature,
            usage=result.get("usage", {})
        )
        
        return generated_text
    
    def _generate_stub(self, prompt: str, **kwargs) -> str:
        """Generate deterministic stub response based on prompt hash."""
        # Create deterministic hash from prompt and seed
        seed = kwargs.get("seed", self.seed)
        content = f"{prompt}|{seed}|{self.model}|vllm"
        prompt_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        
        # Analyze prompt to generate appropriate response
        prompt_lower = prompt.lower()
        
        if "sql" in prompt_lower or "select" in prompt_lower:
            response = f"""-- vLLM Generated SQL (stub mode)
WITH test_data AS (
    SELECT 
        column_name,
        COUNT(*) as row_count,
        '{prompt_hash}' as generation_id
    FROM target_table
    WHERE test_condition IS NOT NULL
)
SELECT * FROM test_data
ORDER BY row_count DESC
LIMIT 100;"""
        
        elif "test" in prompt_lower and ("fresh" in prompt_lower or "recent" in prompt_lower):
            response = f"""Data Freshness Test Analysis (vLLM Stub):
Generation ID: {prompt_hash}
Test Type: Freshness validation
Analysis: Check if data was updated within the expected time window
Recommendation: Monitor MAX(timestamp_column) against current time
Threshold: Consider data stale if older than 24 hours"""
        
        elif "json" in prompt_lower or "variant" in prompt_lower or "flatten" in prompt_lower:
            response = f"""{{
  "test_type": "json_variant_analysis",
  "generation_id": "{prompt_hash}",
  "provider": "vllm_stub",
  "analysis": {{
    "json_structure": "nested_object_detected",
    "flatten_required": true,
    "path_validation": "$.field.subfield",
    "cardinality_check": "array_length_validation"
  }},
  "sql_approach": "LATERAL FLATTEN with Snowflake syntax",
  "recommendation": "Use GET_PATH for JSON field extraction"
}}"""
        
        elif "rule" in prompt_lower or "business" in prompt_lower:
            response = f"""Business Rule Validation (vLLM Stub):
Generation ID: {prompt_hash}
Rule Type: Data consistency check
Analysis: Compare calculated values with expected business logic
Example: order_total = items_total + tax + shipping
Tolerance: Allow small differences due to rounding (±0.01)
Validation: Flag records where ABS(difference) > tolerance"""
        
        elif "explain" in prompt_lower or "failure" in prompt_lower:
            response = f"""Test Failure Explanation (vLLM Stub):
Generation ID: {prompt_hash}
Root Cause Analysis:
1. Data Quality Issues: Check for null values, data type mismatches
2. Business Logic Changes: Verify if calculation rules have changed
3. Source System Issues: Investigate upstream data pipeline
4. Timing Issues: Consider data arrival delays or processing windows

Recommended Actions:
- Review sample failing records
- Check data lineage and transformations
- Validate source system health
- Consider adjusting test tolerances if appropriate"""
        
        else:
            # Generic response with more sophisticated structure
            response = f"""vLLM AI Analysis (Stub Mode):

Generation Metadata:
- ID: {prompt_hash}
- Provider: {self.provider}
- Model: {self.model}
- Seed: {seed}

Analysis Summary:
This is a deterministic stub response generated using vLLM adapter.
The response is consistent and reproducible based on the input prompt hash.

Key Insights:
- Prompt length: {len(prompt)} characters
- Response generated in stub mode due to service unavailability
- Maintains deterministic behavior for testing and development

Recommendations:
- Deploy vLLM service for enhanced AI capabilities
- Configure appropriate model for data testing domain
- Monitor service health for optimal performance"""
        
        logger.info(
            "Generated vLLM stub response",
            provider=self.provider,
            generation_id=prompt_hash,
            prompt_length=len(prompt),
            response_length=len(response)
        )
        
        return response
    
    async def compile_expression(self, request: CompileRequest) -> CompileResponse:
        """Compile expression using vLLM or fallback to parent implementation."""
        # If vLLM is available, we could enhance the compilation with actual AI
        # For now, use the parent's mock implementation but with vLLM-specific metadata
        response = await super().compile_expression(request)
        
        # Update metadata to reflect vLLM usage
        health_status = await self.health()
        if health_status["ok"]:
            response.confidence = 0.95  # Higher confidence with actual AI
            self.model_name = f"vllm:{self.model}"
        else:
            response.confidence = 0.78  # Lower confidence in stub mode
            self.model_name = f"vllm:{self.model}:stub"
            if not response.warnings:
                response.warnings = []
            response.warnings.append("Using stub mode - vLLM service not available")
        
        return response
    
    async def generate_batch(self, prompts: List[str], **kwargs) -> List[str]:
        """Generate responses for multiple prompts (vLLM-specific feature)."""
        if not prompts:
            return []
        
        if len(prompts) > 10:
            raise ValueError("Too many prompts in batch (max 10)")
        
        # Check if vLLM is available
        if self._is_available is None:
            health_result = await self.health()
            self._is_available = health_result["ok"]
        
        if self._is_available:
            try:
                return await self._generate_batch_with_vllm(prompts, **kwargs)
            except Exception as e:
                logger.warning("vLLM batch generation failed, falling back to individual stub calls", error=str(e))
                return [self._generate_stub(prompt, **kwargs) for prompt in prompts]
        else:
            logger.info("vLLM not available, using stub mode for batch generation")
            return [self._generate_stub(prompt, **kwargs) for prompt in prompts]
    
    async def _generate_batch_with_vllm(self, prompts: List[str], **kwargs) -> List[str]:
        """Generate batch responses using vLLM service."""
        # vLLM supports batch processing - for now, process sequentially
        # In a real implementation, this could use vLLM's batch API
        results = []
        for prompt in prompts:
            result = await self._generate_with_vllm(prompt, **kwargs)
            results.append(result)
        return results
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._client.aclose()
