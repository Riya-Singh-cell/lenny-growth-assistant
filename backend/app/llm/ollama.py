import logging
from typing import List, Optional
import httpx
from app.config import settings
from app.llm.base import LLMProvider, LLMMessage, LLMResponse, ProviderStatus

logger = logging.getLogger("lenny.llm.ollama")


def classify_ollama_error(status_code: int, detail: str) -> str:
    detail_lower = detail.lower()
    if status_code == 404 or "model" in detail_lower and "not found" in detail_lower:
        return "model_missing"
    if "memory" in detail_lower or "out of memory" in detail_lower:
        return "memory_failure"
    return "unavailable" if status_code >= 500 else "request_failure"


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2", timeout: float = 60.0, max_tokens: int = 2048):
        self.base_url = base_url.rstrip("/")
        self._model = model
        self.timeout = timeout
        self.max_tokens = max_tokens

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model

    async def check_health(self) -> ProviderStatus:
        """Pings Ollama server to inspect connection and available models."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    # Auto-adapt to installed model if configured model is missing
                    if models and self._model not in models and f"{self._model}:latest" not in models:
                        logger.info("Configured model '%s' not found. Auto-selecting installed Ollama model '%s'.", self._model, models[0])
                        self._model = models[0]

                    return ProviderStatus(
                        is_available=True,
                        provider=self.provider_name,
                        model=self._model,
                        available_models=models,
                        error=None
                    )
                return ProviderStatus(
                    is_available=False,
                    provider=self.provider_name,
                    model=self._model,
                    error=f"Ollama returned HTTP {res.status_code}"
                )
        except httpx.ConnectError:
            return ProviderStatus(
                is_available=False,
                provider=self.provider_name,
                model=self._model,
                error=f"Cannot connect to Ollama at {self.base_url}. Please run 'ollama serve'."
            )
        except Exception as e:
            return ProviderStatus(
                is_available=False,
                provider=self.provider_name,
                model=self._model,
                error=f"Ollama health check error: {str(e)}"
            )

    async def generate(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        payload_messages = []
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})
        for msg in messages:
            payload_messages.append({"role": msg.role, "content": msg.content})

        payload = {
            "model": self._model,
            "messages": payload_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": min(max_tokens, self.max_tokens)
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                if response.status_code != 200:
                    error_detail = response.text
                    error_kind = classify_ollama_error(response.status_code, error_detail)
                    logger.error("Ollama API error (%d): %s", response.status_code, error_detail)
                    raise RuntimeError(
                        f"Ollama {error_kind}: status {response.status_code}: {error_detail}. "
                        f"Ensure model '{self._model}' is pulled with 'ollama pull {self._model}'."
                    )
                
                data = response.json()
                message_content = data.get("message", {}).get("content", "")
                
                return LLMResponse(
                    content=message_content,
                    model=self._model,
                    provider=self.provider_name,
                    usage={
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                    },
                    finish_reason="stop" if data.get("done") else None
                )
        except httpx.ConnectError as e:
            logger.error("Failed to connect to Ollama at %s: %s", self.base_url, e)
            raise RuntimeError(
                f"Ollama is unreachable at {self.base_url}. "
                f"Please start Ollama with 'ollama serve' or check your OLLAMA_BASE_URL configuration."
            )
        except httpx.TimeoutException:
            logger.error("Ollama request timed out after %s seconds", self.timeout)
            raise RuntimeError(
                f"Ollama request timed out after {self.timeout}s. The model may still be loading or generating."
            )
