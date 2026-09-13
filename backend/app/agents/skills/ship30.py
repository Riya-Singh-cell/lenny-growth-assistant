import logging
from typing import List, Dict, Any, Optional
from app.llm.base import LLMProvider, LLMMessage
from app.retrieval.retriever import RetrievedChunk

logger = logging.getLogger("lenny.skills.ship30")

SHIP30_SYSTEM_PROMPT = """You are an elite growth essayist and digital writer trained in the Ship 30 for 30 methodology (founded by Dickie Bush & Nicolas Cole) and product strategy frameworks from Lenny's Podcast.

Your objective is to produce a masterclass, high-impact, ~1,250-word atomic essay based STRICTLY on the retrieved transcript evidence provided.

CRITICAL PRINCIPLES OF THE SHIP 30 FOR 30 ESSAY STYLE:
1. **Target Word Count**: Approximately 1,250 words. Be thorough, substantive, and deeply practical without adding fluff.
2. **The Hook**: Open with a gripping, counter-intuitive insight or painful reality. Use the 1-3-1 rhythm (one sentence, three short sentences, one punchline).
3. **Skimmable Visual Architecture**:
   - Compelling Roman numeral or numbered section headings (e.g., `## I. The Fundamental Trap: ...`)
   - High-contrast formatting: Use **selective bold emphasis** on the first 3-5 words of key sentences to anchor reader scanning.
   - Bulleted breakdowns of actionable steps, tactical frameworks, and metrics.
4. **Strict Grounding in Lenny's Podcast Evidence**:
   - Every major claim, tactic, or framework MUST cite the guest and context from the retrieved transcripts.
   - If the transcript doesn't support an assertion, do not fabricate it.
   - Quote or attribute direct insights to the guests (e.g., "As Adam Fishman noted during his tenure scaling Lyft...").
5. **Concrete Actionable Takeaways**:
   - Close with an explicit "The Monday Morning Execution Checklist" with 3-5 tactical actions a product leader or founder can run immediately.
6. **Sources & Attribution**:
   - Append a clear "Sources & Episode Citations" section at the end.

STRUCTURE:
# [Gripping Headline: The Counter-Intuitive Truth About [Topic]]
*A 1,250-Word Deep Dive on How the World's Best Growth Leaders Master [Topic]*

[The Hook & The Context]
[Pillar I: The Diagnostic Framework]
[Pillar II: The Operational Engine]
[Pillar III: The Metrics That Actually Matter]
[Pillar IV: Common Failure Modes]
[The Monday Morning Execution Playbook]
[Sources & Episode Citations]
"""


class Ship30Skill:
    """
    Dedicated skill for generating publication-grade ~1,250 word essays
    structured with Ship 30 for 30 digital writing principles.
    """

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def generate_essay(
        self,
        topic_or_query: str,
        retrieved_chunks: List[RetrievedChunk],
        conversation_history: Optional[List[LLMMessage]] = None
    ) -> Dict[str, Any]:
        """
        Executes the three-phase transformation:
        Source Material -> Grounded Insights -> Ship 30 Transformation
        """
        # Step 1: Format grounded source evidence
        context_blocks = []
        for idx, chunk in enumerate(retrieved_chunks, 1):
            context_blocks.append(
                f"[Source {idx}] Episode: {chunk.title}\n"
                f"Guest: {chunk.guest or 'Guest'}\n"
                f"Speaker: {chunk.speaker} ({chunk.timestamp_str})\n"
                f"YouTube Link: {chunk.youtube_timed_url or chunk.youtube_url or 'N/A'}\n"
                f"Transcript Content:\n{chunk.text}\n"
            )

        grounded_context = "\n---\n".join(context_blocks) if context_blocks else "No direct transcript matches found."

        # Step 2: Assemble prompt
        user_prompt = f"""Write an in-depth ~1,250-word Ship 30 for 30 style essay on:
"{topic_or_query}"

GROUNDED TRANSCRIPT MATERIAL FROM LENNY'S PODCAST:
==================================================
{grounded_context}
==================================================

INSTRUCTIONS:
Transform the insights above into an authoritative, beautifully formatted, ~1,250-word essay following the Ship 30 for 30 visual architecture guidelines. Ground every recommendation in what the podcast guests shared.
"""

        messages = [
            LLMMessage(role="user", content=user_prompt)
        ]

        logger.info("Ship30Skill generating ~1,250-word essay with provider '%s' (chunks=%d)", self.llm.provider_name, len(retrieved_chunks))

        # Max tokens set to 3000 to comfortably support ~1,250 words
        response = await self.llm.generate(
            messages=messages,
            system_prompt=SHIP30_SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=3000
        )

        # Calculate word count for observability
        word_count = len(response.content.split())
        logger.info("Ship30Skill completed essay generation. Word count: %d", word_count)

        sources = [
            {
                "episode": c.title,
                "guest": c.guest,
                "speaker": c.speaker,
                "timestamp": c.timestamp_str,
                "url": c.youtube_timed_url or c.youtube_url
            }
            for c in retrieved_chunks
        ]

        return {
            "content": response.content,
            "word_count": word_count,
            "sources": sources,
            "provider": self.llm.provider_name,
            "model": self.llm.model_name
        }
