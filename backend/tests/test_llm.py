import pytest
from app.llm.factory import get_llm_provider
from app.llm.ollama import OllamaProvider, classify_ollama_error
from app.llm.cloud import AnthropicProvider, OpenAIProvider


def test_factory_returns_ollama_provider():
    provider = get_llm_provider(provider_override="ollama")
    assert isinstance(provider, OllamaProvider)
    assert provider.provider_name == "ollama"


def test_factory_returns_cloud_provider():
    provider = get_llm_provider(provider_override="anthropic")
    assert isinstance(provider, AnthropicProvider)
    assert provider.provider_name == "anthropic"


def test_ollama_error_classification_distinguishes_runtime_failures():
    assert classify_ollama_error(404, '{"error":"model not found"}') == "model_missing"
    assert classify_ollama_error(500, "model requires more system memory") == "memory_failure"
    assert classify_ollama_error(503, "service unavailable") == "unavailable"


@pytest.mark.asyncio
async def test_ollama_graceful_health_check_when_down():
    # Points to a non-existent port to simulate offline Ollama
    offline_provider = OllamaProvider(base_url="http://localhost:59999", model="llama3.2")
    status = await offline_provider.check_health()
    assert status.is_available is False
    assert "Cannot connect" in status.error or "error" in status.error.lower()


@pytest.mark.asyncio
async def test_anthropic_graceful_health_check_without_key():
    provider = AnthropicProvider(api_key=None)
    status = await provider.check_health()
    assert status.is_available is False
    assert "ANTHROPIC_API_KEY is not configured" in status.error
