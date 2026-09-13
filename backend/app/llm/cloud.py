import logging
from typing import List, Optional
from app.llm.base import LLMProvider, LLMMessage, LLMResponse, ProviderStatus

logger = logging.getLogger("lenny.llm.cloud")


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022", timeout: float = 60.0):
        self.api_key = api_key
        self._model = model
        self.timeout = timeout
        self._client = None
        if self.api_key:
            try:
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=self.api_key, timeout=self.timeout)
            except Exception as e:
                logger.warning("Could not initialize AsyncAnthropic: %s", e)

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def model_name(self) -> str:
        return self._model

    async def check_health(self) -> ProviderStatus:
        if not self.api_key:
            return ProviderStatus(
                is_available=False,
                provider=self.provider_name,
                model=self._model,
                error="ANTHROPIC_API_KEY is not configured in environment."
            )
        return ProviderStatus(
            is_available=True,
            provider=self.provider_name,
            model=self._model,
            available_models=[self._model, "claude-3-haiku-20240307", "claude-3-5-sonnet-20241022"]
        )

    async def generate(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        if not self.api_key or not self._client:
            raise RuntimeError(
                "Anthropic API key is not configured. Set ANTHROPIC_API_KEY or switch LLM_PROVIDER=ollama."
            )

        # Separate system messages for Anthropic API
        formatted_messages = []
        for msg in messages:
            if msg.role == "system":
                if not system_prompt:
                    system_prompt = msg.content
                else:
                    system_prompt += f"\n\n{msg.content}"
            else:
                formatted_messages.append({"role": msg.role, "content": msg.content})

        try:
            kwargs = {
                "model": self._model,
                "messages": formatted_messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            if system_prompt:
                kwargs["system"] = system_prompt

            response = await self._client.messages.create(**kwargs)
            text_content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text_content += block.text

            return LLMResponse(
                content=text_content,
                model=self._model,
                provider=self.provider_name,
                usage={
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                },
                finish_reason=response.stop_reason
            )
        except Exception as e:
            logger.error("Anthropic completion error: %s", e)
            raise RuntimeError(f"Anthropic Claude call failed: {str(e)}")


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o", timeout: float = 60.0):
        self.api_key = api_key
        self._model = model
        self.timeout = timeout
        self._client = None
        if self.api_key:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key, timeout=self.timeout)
            except Exception as e:
                logger.warning("Could not initialize AsyncOpenAI: %s", e)

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model

    async def check_health(self) -> ProviderStatus:
        if not self.api_key:
            return ProviderStatus(
                is_available=False,
                provider=self.provider_name,
                model=self._model,
                error="OPENAI_API_KEY is not configured in environment."
            )
        return ProviderStatus(
            is_available=True,
            provider=self.provider_name,
            model=self._model,
            available_models=[self._model, "gpt-4o-mini", "gpt-4-turbo"]
        )

    async def generate(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        if not self.api_key or not self._client:
            raise RuntimeError(
                "OpenAI API key is not configured. Set OPENAI_API_KEY or switch LLM_PROVIDER=ollama."
            )

        payload_messages = []
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})
        for msg in messages:
            payload_messages.append({"role": msg.role, "content": msg.content})

        try:
            res = await self._client.chat.completions.create(
                model=self._model,
                messages=payload_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            choice = res.choices[0]
            return LLMResponse(
                content=choice.message.content or "",
                model=self._model,
                provider=self.provider_name,
                usage={
                    "prompt_tokens": res.usage.prompt_tokens if res.usage else 0,
                    "completion_tokens": res.usage.completion_tokens if res.usage else 0,
                },
                finish_reason=choice.finish_reason
            )
        except Exception as e:
            logger.error("OpenAI completion error: %s", e)
            raise RuntimeError(f"OpenAI call failed: {str(e)}")
