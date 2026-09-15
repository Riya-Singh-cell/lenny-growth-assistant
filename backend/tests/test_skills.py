import pytest
from unittest.mock import AsyncMock
from app.llm.base import LLMProvider, LLMResponse, LLMMessage
from app.retrieval.retriever import RetrievedChunk
from app.agents.skills.ship30 import Ship30Skill
from app.agents.skills.artifact_gen import ArtifactSkill


class MockShip30LLM(LLMProvider):
    @property
    def provider_name(self) -> str:
        return "mock_ship30"

    @property
    def model_name(self) -> str:
        return "mock_model"

    async def generate(self, messages, system_prompt=None, **kwargs) -> LLMResponse:
        # Realistic Ship 30 formatted essay with ~1,250 words, 1-3-1 hook, Roman numerals, and Monday checklist
        paragraphs = [
            "# The Counter-Intuitive Truth About Product-Led Onboarding",
            "*A 1,250-Word Deep Dive on How the World's Best Growth Leaders Master Onboarding*",
            "",
            "Most founders think onboarding is an educational walkthrough.",
            "It is not. It is an emotional race against user abandonment. Every extra click drops conversion by twenty percent.",
            "The best products don't teach. They deliver value.",
            "",
            "## I. The Fundamental Trap: The Feature Tour",
            "**Never tour features** when you can show immediate outcomes. As Adam Fishman observed scaling Patreon and Lyft, users do not sign up to admire your interface architecture. They sign up to solve an acute personal or organizational pain point. When you delay their time-to-value with multi-step carousel walkthroughs, you trigger cognitive fatigue. The winning playbook is reducing the distance between signup and the core aha moment to under sixty seconds.",
            "",
            "## II. The Operational Engine: Reverse Funnel Architecture",
            "**Map backwards from retention** rather than forwards from registration. Elena Verna demonstrates that high-retention cohorts exhibit distinct milestone behaviors in week one. If your activation metric requires creating a project, invite team members during onboarding rather than post-activation. Friction that qualifies high-intent users is healthy; friction that delays progress is toxic.",
            "",
            "## III. The Metrics That Actually Matter",
            "**Track Time to Value (TTV)** with militant discipline. Leading growth teams discard vanity registration metrics in favor of setup completion rates. Measure the percentage of signups reaching the core product loop within twenty-four hours. Instrument every step of the setup flow to pinpoint abandonment drop-offs.",
            "",
            "## IV. Common Failure Modes",
            "**Avoid mandatory profile completion** prior to experiencing the product value. Requiring users to configure preferences, avatars, or billing information before experiencing the first magical moment destroys activation momentum. Progressive profiling allows you to collect data incrementally over the user lifecycle.",
            "",
            "## The Monday Morning Execution Checklist",
            "- [ ] Audit your current onboarding flow and delete at least three non-essential steps.",
            "- [ ] Measure your exact median Time to Value (TTV) from signup to first aha moment.",
            "- [ ] Replace generic tooltips with an actionable empty-state template.",
            "- [ ] Implement personalized onboarding paths based on user role and intent.",
            "",
            "## Sources & Episode Citations",
            "- Adam Fishman: Scaling Onboarding at Patreon & Lyft",
            "- Elena Verna: Product-Led Growth & Retention Loops"
        ]
        
        # Expand word count to realistic ~1,200 words for word count validation
        expansion = " Growth strategy requires disciplined execution, continuous experimentation, rigorous cohort analysis, and relentless user focus." * 75
        paragraphs.insert(10, expansion)

        content = "\n\n".join(paragraphs)
        return LLMResponse(content=content, provider="mock_ship30", model="mock_model")

    async def check_health(self):
        return None


def make_chunk():
    return RetrievedChunk(
        chunk_id="chk_1",
        episode_slug="adam-fishman",
        title="Adam Fishman on Onboarding",
        guest="Adam Fishman",
        speaker="Adam Fishman",
        timestamp_str="00:10:00",
        timestamp_seconds=600,
        text="Onboarding is about time to value.",
        youtube_url="https://youtube.com/watch?v=12345",
        youtube_timed_url="https://youtube.com/watch?v=12345&t=600s",
        score=0.9
    )


@pytest.mark.asyncio
async def test_ship30_word_count_and_structure_validation():
    """Validates Ship 30 for 30 essay word count and visual digital architecture."""
    llm = MockShip30LLM()
    skill = Ship30Skill(llm)

    result = await skill.generate_essay("Mastering Onboarding", [make_chunk()])
    content = result["content"]

    # 1. Word Count Validation: Should be approximately ~1,250 words (allow realistic +/- range)
    words = content.split()
    word_count = len(words)
    assert 1000 <= word_count <= 1500, f"Expected ~1,250 words, got {word_count}"

    # 2. Structure Validation: Ship 30 Digital Writing Architecture
    assert "## I." in content, "Missing Roman numeral Pillar I"
    assert "## II." in content, "Missing Roman numeral Pillar II"
    assert "The Monday Morning Execution Checklist" in content, "Missing execution checklist"
    assert "Sources & Episode Citations" in content, "Missing source citations"
    assert "**" in content, "Missing bold lead-in sentence anchors"


@pytest.mark.asyncio
async def test_artifact_skill_html_generation_and_sanitization():
    """Validates ArtifactSkill generates and sanitizes styled HTML artifacts."""
    class MockArtifactLLM(LLMProvider):
        @property
        def provider_name(self) -> str:
            return "mock_art"
        @property
        def model_name(self) -> str:
            return "mock_model"
        async def generate(self, messages, system_prompt=None, **kwargs) -> LLMResponse:
            raw_html = """```html
<div class="growth-card">
  <h2>The Retention Engine</h2>
  <script>alert('xss');</script>
  <p style="color: #2563eb;">Core retention loops compounds cohort value over time.</p>
</div>
```"""
            return LLMResponse(content=raw_html, provider="mock_art", model="mock_model")
        async def check_health(self):
            return None

    skill = ArtifactSkill(MockArtifactLLM())
    result = await skill.generate_artifact(
        prompt="Create a retention engine visual card",
        retrieved_chunks=[make_chunk()],
        target_type="html"
    )

    assert result["type"] == "html"
    assert "The Retention Engine" in result["title"] or "Retention" in result["raw_content"]
    # Verify script was stripped by sanitizer
    assert "<script>" not in result["sanitized_content"]
    assert "alert('xss')" not in result["sanitized_content"]
    assert "color: #2563eb;" in result["sanitized_content"]
