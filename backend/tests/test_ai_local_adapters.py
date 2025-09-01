"""Tests for local AI adapters (Ollama and vLLM)."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from dto_api.services.local_ollama import LocalOllamaAdapter
from dto_api.services.vllm_adapter import VLLMAdapter
from dto_api.models.tests import CompileRequest


class TestLocalOllamaAdapter:
    """Test cases for LocalOllamaAdapter."""
    
    @pytest.fixture
    def ollama_adapter(self):
        """Create Ollama adapter instance."""
        return LocalOllamaAdapter(base_url="http://localhost:11434", model="llama2")
    
    @pytest.mark.asyncio
    async def test_health_service_available(self, ollama_adapter):
        """Test health check when Ollama service is available."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama2:latest"},
                {"name": "codellama:7b"}
            ]
        }
        
        with patch.object(ollama_adapter._client, 'get', return_value=mock_response):
            health = await ollama_adapter.health()
            
            assert health["ok"] is True
            assert health["provider"] == "ollama"
            assert "llama2" in health["detail"]
            assert "models" in health
            assert health["base_url"] == "http://localhost:11434"
    
    @pytest.mark.asyncio
    async def test_health_service_unavailable(self, ollama_adapter):
        """Test health check when Ollama service is unavailable."""
        with patch.object(ollama_adapter._client, 'get', side_effect=httpx.ConnectError("Connection failed")):
            health = await ollama_adapter.health()
            
            assert health["ok"] is False
            assert health["provider"] == "ollama"
            assert "Cannot connect" in health["detail"]
            assert health["base_url"] == "http://localhost:11434"
    
    @pytest.mark.asyncio
    async def test_health_model_not_found(self, ollama_adapter):
        """Test health check when model is not available."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "different-model:latest"}
            ]
        }
        
        with patch.object(ollama_adapter._client, 'get', return_value=mock_response):
            health = await ollama_adapter.health()
            
            assert health["ok"] is False
            assert health["provider"] == "ollama"
            assert "not found" in health["detail"]
            assert "different-model" in health["detail"]
    
    @pytest.mark.asyncio
    async def test_generate_with_ollama_success(self, ollama_adapter):
        """Test successful generation with Ollama service."""
        # Mock health check
        ollama_adapter._is_available = True
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "This is a test response from Ollama"
        }
        
        with patch.object(ollama_adapter._client, 'post', return_value=mock_response):
            result = await ollama_adapter.generate("Test prompt")
            
            assert result == "This is a test response from Ollama"
    
    @pytest.mark.asyncio
    async def test_generate_stub_mode(self, ollama_adapter):
        """Test generation in stub mode when Ollama is unavailable."""
        ollama_adapter._is_available = False
        
        result = await ollama_adapter.generate("Test prompt for SQL generation")
        
        assert "stub mode" in result.lower()
        assert "sql" in result.lower()
        assert len(result) > 0
        
        # Test deterministic behavior
        result2 = await ollama_adapter.generate("Test prompt for SQL generation")
        assert result == result2  # Should be identical
    
    @pytest.mark.asyncio
    async def test_generate_stub_different_prompts(self, ollama_adapter):
        """Test that different prompts generate different stub responses."""
        ollama_adapter._is_available = False
        
        sql_result = await ollama_adapter.generate("Generate SQL for uniqueness test")
        json_result = await ollama_adapter.generate("Validate JSON structure")
        explain_result = await ollama_adapter.generate("Explain test failure")
        
        # All should be different
        assert sql_result != json_result
        assert json_result != explain_result
        assert sql_result != explain_result
        
        # But should contain appropriate keywords
        assert "sql" in sql_result.lower()
        assert "json" in json_result.lower()
        assert "failure" in explain_result.lower()
    
    @pytest.mark.asyncio
    async def test_generate_empty_prompt(self, ollama_adapter):
        """Test error handling for empty prompt."""
        with pytest.raises(ValueError, match="Prompt cannot be empty"):
            await ollama_adapter.generate("")
    
    @pytest.mark.asyncio
    async def test_generate_prompt_too_long(self, ollama_adapter):
        """Test error handling for overly long prompt."""
        long_prompt = "x" * 10001
        with pytest.raises(ValueError, match="Prompt too long"):
            await ollama_adapter.generate(long_prompt)
    
    @pytest.mark.asyncio
    async def test_generate_with_custom_parameters(self, ollama_adapter):
        """Test generation with custom parameters."""
        ollama_adapter._is_available = False
        
        result = await ollama_adapter.generate(
            "Test prompt",
            temperature=0.8,
            max_tokens=500,
            seed=123
        )
        
        # Should be deterministic based on seed
        result2 = await ollama_adapter.generate(
            "Test prompt",
            temperature=0.8,
            max_tokens=500,
            seed=123
        )
        assert result == result2
        
        # Different seed should give different result
        result3 = await ollama_adapter.generate(
            "Test prompt",
            temperature=0.8,
            max_tokens=500,
            seed=456
        )
        assert result != result3
    
    @pytest.mark.asyncio
    async def test_compile_expression_with_ollama_available(self, ollama_adapter):
        """Test compile_expression when Ollama is available."""
        ollama_adapter._is_available = True
        
        # Mock health check
        mock_health = {
            "ok": True,
            "provider": "ollama",
            "detail": "Service healthy"
        }
        
        with patch.object(ollama_adapter, 'health', return_value=mock_health):
            request = CompileRequest(
                expression="Check for unique order IDs",
                dataset="orders",
                test_type="uniqueness"
            )
            
            response = await ollama_adapter.compile_expression(request)
            
            assert response.confidence == 0.92  # Higher confidence with AI
            assert "ollama:llama2" in ollama_adapter.model_name
            assert "stub" not in ollama_adapter.model_name
    
    @pytest.mark.asyncio
    async def test_compile_expression_stub_mode(self, ollama_adapter):
        """Test compile_expression in stub mode."""
        ollama_adapter._is_available = False
        
        # Mock health check
        mock_health = {
            "ok": False,
            "provider": "ollama",
            "detail": "Service unavailable"
        }
        
        with patch.object(ollama_adapter, 'health', return_value=mock_health):
            request = CompileRequest(
                expression="Check for unique order IDs",
                dataset="orders",
                test_type="uniqueness"
            )
            
            response = await ollama_adapter.compile_expression(request)
            
            assert response.confidence == 0.75  # Lower confidence in stub mode
            assert "stub" in ollama_adapter.model_name
            assert any("stub mode" in warning for warning in response.warnings)


class TestVLLMAdapter:
    """Test cases for VLLMAdapter."""
    
    @pytest.fixture
    def vllm_adapter(self):
        """Create vLLM adapter instance."""
        return VLLMAdapter(base_url="http://localhost:8000", model="microsoft/DialoGPT-medium")
    
    @pytest.mark.asyncio
    async def test_health_service_available(self, vllm_adapter):
        """Test health check when vLLM service is available."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "microsoft/DialoGPT-medium"},
                {"id": "facebook/opt-1.3b"}
            ]
        }
        
        with patch.object(vllm_adapter._client, 'get', return_value=mock_response):
            health = await vllm_adapter.health()
            
            assert health["ok"] is True
            assert health["provider"] == "vllm"
            assert "DialoGPT-medium" in health["detail"]
            assert "models" in health
            assert health["base_url"] == "http://localhost:8000"
    
    @pytest.mark.asyncio
    async def test_health_service_unavailable(self, vllm_adapter):
        """Test health check when vLLM service is unavailable."""
        with patch.object(vllm_adapter._client, 'get', side_effect=httpx.ConnectError("Connection failed")):
            health = await vllm_adapter.health()
            
            assert health["ok"] is False
            assert health["provider"] == "vllm"
            assert "Cannot connect" in health["detail"]
    
    @pytest.mark.asyncio
    async def test_generate_with_vllm_success(self, vllm_adapter):
        """Test successful generation with vLLM service."""
        vllm_adapter._is_available = True
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is a test response from vLLM"
                    }
                }
            ],
            "usage": {"total_tokens": 50}
        }
        
        with patch.object(vllm_adapter._client, 'post', return_value=mock_response):
            result = await vllm_adapter.generate("Test prompt")
            
            assert result == "This is a test response from vLLM"
    
    @pytest.mark.asyncio
    async def test_generate_stub_mode_json(self, vllm_adapter):
        """Test JSON-specific stub generation."""
        vllm_adapter._is_available = False
        
        result = await vllm_adapter.generate("Validate JSON variant structure with flatten")
        
        assert "json" in result.lower()
        assert "flatten" in result.lower()
        assert "generation_id" in result
        # Should be valid JSON structure
        assert "{" in result and "}" in result
    
    @pytest.mark.asyncio
    async def test_generate_stub_mode_business_rule(self, vllm_adapter):
        """Test business rule specific stub generation."""
        vllm_adapter._is_available = False
        
        result = await vllm_adapter.generate("Create business rule validation for order totals")
        
        assert "business rule" in result.lower()
        assert "validation" in result.lower()
        assert "tolerance" in result.lower()
    
    @pytest.mark.asyncio
    async def test_generate_batch_stub_mode(self, vllm_adapter):
        """Test batch generation in stub mode."""
        vllm_adapter._is_available = False
        
        prompts = [
            "Generate SQL for uniqueness test",
            "Validate JSON structure",
            "Explain test failure"
        ]
        
        results = await vllm_adapter.generate_batch(prompts)
        
        assert len(results) == 3
        assert all(len(result) > 0 for result in results)
        assert all(result != other for i, result in enumerate(results) 
                  for j, other in enumerate(results) if i != j)
    
    @pytest.mark.asyncio
    async def test_generate_batch_too_many_prompts(self, vllm_adapter):
        """Test error handling for too many prompts in batch."""
        prompts = ["prompt"] * 11  # More than max of 10
        
        with pytest.raises(ValueError, match="Too many prompts in batch"):
            await vllm_adapter.generate_batch(prompts)
    
    @pytest.mark.asyncio
    async def test_generate_batch_empty_list(self, vllm_adapter):
        """Test batch generation with empty prompt list."""
        results = await vllm_adapter.generate_batch([])
        assert results == []
    
    @pytest.mark.asyncio
    async def test_vllm_error_handling(self, vllm_adapter):
        """Test error handling when vLLM returns error."""
        vllm_adapter._is_available = True
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        
        with patch.object(vllm_adapter._client, 'post', return_value=mock_response):
            # Should fall back to stub mode
            result = await vllm_adapter.generate("Test prompt")
            assert "stub mode" in result.lower()
    
    @pytest.mark.asyncio
    async def test_compile_expression_enhanced_confidence(self, vllm_adapter):
        """Test that vLLM provides higher confidence than base implementation."""
        vllm_adapter._is_available = True
        
        mock_health = {
            "ok": True,
            "provider": "vllm",
            "detail": "Service healthy"
        }
        
        with patch.object(vllm_adapter, 'health', return_value=mock_health):
            request = CompileRequest(
                expression="Check data freshness in orders table",
                dataset="orders",
                test_type="freshness"
            )
            
            response = await vllm_adapter.compile_expression(request)
            
            assert response.confidence == 0.95  # Higher confidence with vLLM
            assert "vllm:" in vllm_adapter.model_name


class TestAdapterComparison:
    """Test cases comparing both adapters."""
    
    @pytest.mark.asyncio
    async def test_deterministic_stub_responses(self):
        """Test that both adapters produce deterministic responses."""
        ollama = LocalOllamaAdapter()
        vllm = VLLMAdapter()
        
        # Both should be in stub mode
        ollama._is_available = False
        vllm._is_available = False
        
        prompt = "Generate SQL for uniqueness test with seed 42"
        
        # Test multiple calls with same prompt
        ollama_result1 = await ollama.generate(prompt, seed=42)
        ollama_result2 = await ollama.generate(prompt, seed=42)
        vllm_result1 = await vllm.generate(prompt, seed=42)
        vllm_result2 = await vllm.generate(prompt, seed=42)
        
        # Each adapter should be consistent with itself
        assert ollama_result1 == ollama_result2
        assert vllm_result1 == vllm_result2
        
        # But adapters should produce different results
        assert ollama_result1 != vllm_result1
    
    @pytest.mark.asyncio
    async def test_health_response_structure(self):
        """Test that both adapters return consistent health response structure."""
        ollama = LocalOllamaAdapter()
        vllm = VLLMAdapter()
        
        # Mock connection errors for both
        with patch.object(ollama._client, 'get', side_effect=httpx.ConnectError("Connection failed")):
            with patch.object(vllm._client, 'get', side_effect=httpx.ConnectError("Connection failed")):
                ollama_health = await ollama.health()
                vllm_health = await vllm.health()
                
                # Both should have same structure
                required_keys = {"ok", "provider", "detail", "base_url"}
                assert set(ollama_health.keys()).issuperset(required_keys)
                assert set(vllm_health.keys()).issuperset(required_keys)
                
                # Both should indicate failure
                assert ollama_health["ok"] is False
                assert vllm_health["ok"] is False
                
                # Providers should be different
                assert ollama_health["provider"] == "ollama"
                assert vllm_health["provider"] == "vllm"
    
    @pytest.mark.asyncio
    async def test_context_manager_support(self):
        """Test that both adapters support async context manager."""
        async with LocalOllamaAdapter() as ollama:
            assert ollama is not None
            health = await ollama.health()
            assert "provider" in health
        
        async with VLLMAdapter() as vllm:
            assert vllm is not None
            health = await vllm.health()
            assert "provider" in health


# Integration test markers
pytestmark = pytest.mark.asyncio
