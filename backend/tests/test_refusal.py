import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from typing import List

from app.llm.base import LLMProvider, LLMResponse, LLMMessage
from app.retrieval.retriever import RetrievedChunk
from app.agents.growth_assistant import GrowthAssistantAgent


class MockLLM(LLMProvider):
    def __init__(self, should_fail_if_called: bool = False):
        self.should_fail_if_called = should_fail_if_called
        self.call_count = 0
        self.last_messages = []

    @property
    def provider_name(self) -> str:
        return "mock_provider"

    @property
    def model_name(self) -> str:
        return "mock_model"

    async def generate(self, messages: List[LLMMessage], system_prompt: str = None, **kwargs) -> LLMResponse:
        self.call_count += 1
        self.last_messages = messages
        if self.should_fail_if_called:
            raise AssertionError("LLM should NOT have been invoked when retrieval evidence is insufficient!")
        return LLMResponse(
            content="This is a grounded answer from the mock LLM.",
            provider="mock_provider",
            model="mock_model"
        )

    async def check_health(self):
        return MagicMock(is_available=True, provider="mock_provider", model="mock_model")


def make_chunk(chunk_id: str, title: str, guest: str, score: float, text: str = "Evidence text") -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        episode_slug="test-slug",
        title=title,
        guest=guest,
        speaker=guest,
        timestamp_str="00:05:00",
        timestamp_seconds=300,
        text=text,
        youtube_url="https://youtube.com/watch?v=12345",
        youtube_timed_url="https://youtube.com/watch?v=12345&t=300s",
        score=score
    )


@pytest.mark.asyncio
async def test_zero_retrieval_bypasses_llm():
    """Requirement 1: Zero retrieval returns deterministic refusal and does NOT call LLM."""
    mock_llm = MockLLM(should_fail_if_called=True)
    agent = GrowthAssistantAgent(mock_llm)

    with patch.object(agent.retriever, "retrieve", new_callable=AsyncMock) as mock_retrieve:
        mock_retrieve.return_value = []

        result = await agent.answer(question="What is the quantum flux of hypergrowth?", threshold=0.25)

        assert result["evidence_sufficient"] is False
        assert result["sources"] == []
        assert "insufficient evidence" in result["answer"].lower()
        assert mock_llm.call_count == 0


@pytest.mark.asyncio
async def test_below_threshold_retrieval_bypasses_llm():
    """Requirement 2: Below-threshold similarity score returns deterministic refusal and does NOT call LLM."""
    mock_llm = MockLLM(should_fail_if_called=True)
    agent = GrowthAssistantAgent(mock_llm)

    low_score_chunk = make_chunk("chunk_1", "Mastering Loops", "Test Guest", score=0.12)

    with patch.object(agent.retriever, "retrieve", new_callable=AsyncMock) as mock_retrieve:
        mock_retrieve.return_value = [low_score_chunk]

        # Configured threshold is 0.25, top chunk is only 0.12
        result = await agent.answer(question="How to build an interstellar product?", threshold=0.25)

        assert result["evidence_sufficient"] is False
        assert result["sources"] == []
        assert "insufficient evidence" in result["answer"].lower()
        assert mock_llm.call_count == 0


@pytest.mark.asyncio
async def test_sufficient_retrieval_invokes_llm():
    """Requirement 3: When retrieval returns chunks with score >= threshold, LLM is called."""
    mock_llm = MockLLM(should_fail_if_called=False)
    agent = GrowthAssistantAgent(mock_llm)

    good_chunk = make_chunk("chunk_2", "Onboarding Masterclass", "Adam Fishman", score=0.85, text="Activation is crucial.")

    with patch.object(agent.retriever, "retrieve", new_callable=AsyncMock) as mock_retrieve:
        mock_retrieve.return_value = [good_chunk]

        result = await agent.answer(question="What did Adam Fishman advise on onboarding?", threshold=0.25)

        assert result["evidence_sufficient"] is True
        assert len(result["sources"]) == 1
        assert mock_llm.call_count == 1
        assert result["answer"] == "This is a grounded answer from the mock LLM."


@pytest.mark.asyncio
async def test_sources_correspond_to_retrieved_evidence():
    """Requirement 4: Returned sources exactly match the retrieved chunks and metadata."""
    mock_llm = MockLLM(should_fail_if_called=False)
    agent = GrowthAssistantAgent(mock_llm)

    c1 = make_chunk("c1", "Episode 1", "Guest A", score=0.75, text="Tactic 1")
    c2 = make_chunk("c2", "Episode 2", "Guest B", score=0.65, text="Tactic 2")

    with patch.object(agent.retriever, "retrieve", new_callable=AsyncMock) as mock_retrieve:
        mock_retrieve.return_value = [c1, c2]

        result = await agent.answer(question="Compare Guest A and Guest B on growth", threshold=0.25)

        assert result["evidence_sufficient"] is True
        assert len(result["sources"]) == 2
        
        # Verify source metadata integrity
        source1 = result["sources"][0]
        assert source1["chunk_id"] == "c1"
        assert source1["episode"] == "Episode 1"
        assert source1["guest"] == "Guest A"
        assert source1["relevance_score"] == 0.75
        assert source1["url"] == "https://youtube.com/watch?v=12345&t=300s"

        source2 = result["sources"][1]
        assert source2["chunk_id"] == "c2"
        assert source2["episode"] == "Episode 2"
        assert source2["guest"] == "Guest B"
        assert source2["relevance_score"] == 0.65
