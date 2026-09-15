import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock

from app.llm.base import LLMResponse, LLMProvider, LLMMessage
from app.retrieval.retriever import RetrievedChunk
from app.agents.core import LennyAgentEngine


class TestLLM(LLMProvider):
    @property
    def provider_name(self) -> str:
        return "test_provider"

    @property
    def model_name(self) -> str:
        return "test_model"

    async def generate(self, messages, system_prompt=None, **kwargs) -> LLMResponse:
        return LLMResponse(
            content="According to Adam Fishman, onboarding must deliver immediate value.",
            provider="test_provider",
            model="test_model"
        )

    async def check_health(self):
        return None


def get_mock_chunk():
    return RetrievedChunk(
        chunk_id="c_test_1",
        episode_slug="adam-fishman",
        title="Adam Fishman on Product",
        guest="Adam Fishman",
        speaker="Adam Fishman",
        timestamp_str="00:04:12",
        timestamp_seconds=252,
        text="Onboarding must establish rapid time-to-value.",
        youtube_url="https://youtube.com/watch?v=mock",
        youtube_timed_url="https://youtube.com/watch?v=mock&t=252s",
        score=0.88
    )


@pytest.mark.asyncio
async def test_chat_endpoint_e2e_grounded_response(test_app):
    """End-to-end test: user message -> agent -> retriever -> LLM -> DB persistence -> sources."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Create a new session
        sess_res = await ac.post("/api/sessions", json={"title": "Test Chat Session"})
        assert sess_res.status_code == 201
        session_id = sess_res.json()["id"]

        # 2. Post a chat message with mocked retrieval & LLM
        with patch("app.agents.core.get_retriever") as mock_get_retriever, \
             patch("app.agents.growth_assistant.get_retriever") as mock_get_ga_retriever, \
             patch("app.api.chat.get_llm_provider") as mock_get_llm:

            mock_retriever = AsyncMock()
            mock_retriever.retrieve.return_value = [get_mock_chunk()]
            mock_get_retriever.return_value = mock_retriever
            mock_get_ga_retriever.return_value = mock_retriever
            mock_get_llm.return_value = TestLLM()

            chat_payload = {
                "session_id": session_id,
                "message": "What did Adam Fishman recommend regarding onboarding?",
                "provider": "ollama"
            }
            chat_res = await ac.post("/api/chat", json=chat_payload)

            assert chat_res.status_code == 200
            data = chat_res.json()

            # Verify response schema and contents
            assert data["session_id"] == session_id
            assert data["role"] == "assistant"
            assert "Adam Fishman" in data["content"]
            assert data["evidence_sufficient"] is True
            assert len(data["sources"]) == 1
            assert data["sources"][0]["guest"] == "Adam Fishman"
            assert data["sources"][0]["timestamp"] == "00:04:12"
            assert "search_lenny_transcripts" in data["tool_calls"]

        # 3. Verify session history persisted
        hist_res = await ac.get(f"/api/sessions/{session_id}")
        assert hist_res.status_code == 200
        messages = hist_res.json()["messages"]
        assert len(messages) == 2  # user + assistant


@pytest.mark.asyncio
async def test_artifact_persistence_and_retrieval(test_app):
    """Verifies that generated artifacts are persisted in DB and retrievable via /api/artifacts."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        sess_res = await ac.post("/api/sessions", json={"title": "Artifact Session"})
        session_id = sess_res.json()["id"]

        class ArtifactLLM(LLMProvider):
            @property
            def provider_name(self) -> str:
                return "test"
            @property
            def model_name(self) -> str:
                return "test"
            async def generate(self, messages, system_prompt=None, **kwargs) -> LLMResponse:
                return LLMResponse(
                    content="```html\n<div class='card'><h1>Activation Framework</h1><p>Test</p></div>\n```",
                    provider="test",
                    model="test"
                )
            async def check_health(self):
                return None

        with patch("app.agents.core.get_retriever") as mock_get_retriever, \
             patch("app.api.chat.get_llm_provider") as mock_get_llm:

            mock_retriever = AsyncMock()
            mock_retriever.retrieve.return_value = [get_mock_chunk()]
            mock_get_retriever.return_value = mock_retriever
            mock_get_llm.return_value = ArtifactLLM()

            chat_payload = {
                "session_id": session_id,
                "message": "Create an html artifact card for activation framework"
            }
            chat_res = await ac.post("/api/chat", json=chat_payload)
            assert chat_res.status_code == 200
            data = chat_res.json()

            assert data["artifact"] is not None
            artifact_id = data["artifact"]["id"]

        # Retrieve artifact directly from /api/artifacts/{id}
        art_res = await ac.get(f"/api/artifacts/{artifact_id}")
        assert art_res.status_code == 200
        art_data = art_res.json()
        assert art_data["id"] == artifact_id
        assert art_data["type"] == "html"
        assert "Activation Framework" in art_data["content"]


@pytest.mark.asyncio
async def test_provider_routing_and_tool_invocation():
    """Directly tests LennyAgentEngine tool execution and provider handling."""
    llm = TestLLM()
    engine = LennyAgentEngine(llm)

    with patch.object(engine.retriever, "retrieve", new_callable=AsyncMock) as mock_ret:
        mock_ret.return_value = [get_mock_chunk()]

        result = await engine.run("What did Adam Fishman say about growth?")
        assert result.intent == "GROUNDED_QA"
        assert result.evidence_sufficient is True
        assert len(result.sources) == 1
        assert "search_lenny_transcripts" in result.tool_calls
