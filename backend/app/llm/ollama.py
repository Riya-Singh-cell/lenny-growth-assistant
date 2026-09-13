import logging
from typing import List, Optional
import httpx
from app.llm.base import LLMProvider, LLMMessage, LLMResponse, ProviderStatus

logger = logging.getLogger("lenny.llm.ollama")


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2", timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self._model = model
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model

    async def check_health(self) -> ProviderStatus:
        """Pings Ollama server to inspect connection and available models."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
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
                "num_predict": max_tokens
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                if response.status_code != 200:
                    error_detail = response.text
                    logger.error("Ollama API error (%d): %s", response.status_code, error_detail)
                    raise RuntimeError(
                        f"Ollama call failed with status {response.status_code}: {error_detail}. "
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
