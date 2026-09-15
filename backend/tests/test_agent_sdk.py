from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.agents.core import LennyAgentEngine
from app.config import settings
from app.llm.base import LLMProvider


class AnthropicAgentProvider(LLMProvider):
    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def model_name(self) -> str:
        return "claude-test"

    async def generate(self, messages, system_prompt=None, **kwargs):
        raise AssertionError("Cloud execution must be driven by Claude Agent SDK")

    async def check_health(self):
        return None


class CapturingSDKClient:
    options = None

    def __init__(self, options=None):
        self.options = options
        CapturingSDKClient.options = options

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def query(self, prompt):
        self.prompt = prompt

    async def receive_response(self):
        if False:
            yield SimpleNamespace()


@pytest.mark.asyncio
async def test_claude_agent_sdk_registers_lenny_domain_tools():
    engine = LennyAgentEngine(AnthropicAgentProvider())
    with patch.object(settings, "ANTHROPIC_API_KEY", "test-key"), \
         patch("claude_agent_sdk.ClaudeSDKClient", CapturingSDKClient):
        result = await engine._run_claude_agent_sdk("Search onboarding advice")

    assert result.intent == "GROUNDED_QA"
    assert CapturingSDKClient.options is not None
    assert "lenny" in CapturingSDKClient.options.mcp_servers
    assert CapturingSDKClient.options.allowed_tools == [
        "mcp__lenny__search_lenny_transcripts",
        "mcp__lenny__generate_ship30_essay",
        "mcp__lenny__create_product_artifact",
    ]