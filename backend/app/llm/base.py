from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class LLMMessage(BaseModel):
    role: str  # 'system', 'user', 'assistant'
    content: str


class LLMResponse(BaseModel):
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None


class ProviderStatus(BaseModel):
    is_available: bool
    provider: str
    model: str
    error: Optional[str] = None
    available_models: List[str] = []


class LLMProvider(ABC):
    """
    Abstract interface for LLM backends (Ollama, Anthropic Claude, OpenAI).
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the canonical provider name, e.g. 'ollama', 'anthropic', 'openai'."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Returns current model identifier."""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Generates completion given list of conversational messages."""
        pass

    @abstractmethod
    async def check_health(self) -> ProviderStatus:
        """Verifies if the provider service is operational and reachable."""
        pass
