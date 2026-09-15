import logging
from typing import Optional
from app.config import settings
from app.llm.base import LLMProvider
from app.llm.ollama import OllamaProvider
from app.llm.cloud import AnthropicProvider, OpenAIProvider

logger = logging.getLogger("lenny.llm.factory")


def get_llm_provider(provider_override: Optional[str] = None, model_override: Optional[str] = None) -> LLMProvider:
    """
    Factory function to get the requested or default configured LLMProvider.
    Allows switching providers without code modification.
    """
    provider_name = (provider_override or settings.LLM_PROVIDER).lower().strip()

    if provider_name == "ollama":
        model = model_override or settings.OLLAMA_MODEL
        return OllamaProvider(
            base_url=settings.OLLAMA_BASE_URL,
            model=model,
            timeout=settings.OLLAMA_TIMEOUT_SECONDS,
            max_tokens=settings.OLLAMA_MAX_TOKENS,
        )

    elif provider_name == "anthropic":
        model = model_override or settings.ANTHROPIC_MODEL
        return AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY, model=model)

    elif provider_name == "openai":
        model = model_override or settings.OPENAI_MODEL
        return OpenAIProvider(api_key=settings.OPENAI_API_KEY, model=model)

    else:
        logger.warning("Unrecognized provider '%s', defaulting to Ollama.", provider_name)
        return OllamaProvider(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            timeout=settings.OLLAMA_TIMEOUT_SECONDS,
            max_tokens=settings.OLLAMA_MAX_TOKENS,
        )
