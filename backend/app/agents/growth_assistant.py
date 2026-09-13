import logging
from typing import List, Dict, Any, Optional
from app.llm.base import LLMProvider, LLMMessage
from app.retrieval.retriever import get_retriever, RetrievedChunk

logger = logging.getLogger("lenny.agent.growth_assistant")

GROWTH_ASSISTANT_SYSTEM_PROMPT = """You are "The Lenny Growth Assistant", a specialized AI product advisor strictly powered by knowledge from Lenny's Podcast transcripts.

CORE OPERATING DIRECTIVES:
1. **Strict Knowledge Grounding**:
   - Lenny's Podcast transcripts are your absolute primary source of truth.
   - Base your answers ONLY on the provided transcript excerpts.
   - Do NOT invent facts, fake quotes, or extrapolate unsupported claims.
   - Do NOT answer from general ungrounded AI knowledge when asked about Lenny's podcast insights.

2. **Handling Insufficient Evidence**:
   - If the retrieved transcript excerpts do NOT contain enough information to answer the question accurately, you MUST explicitly state:
     "Based on the available Lenny's Podcast transcript material, there is insufficient evidence to provide a fully grounded answer to this specific question."
   - Do not attempt to guess or disguise a lack of evidence.

3. **Tone & Style**:
   - Pragmatic, authoritative, clear, and product-minded (like a world-class VP of Product or Growth).
   - Use concise frameworks, bullet points, and high-impact takeaways.
   - Specifically name the guest and context (e.g. "As Adam Fishman explained regarding onboarding at Patreon and Lyft...").

4. **Source Attribution**:
   - Always reference which guests or episodes supported your points.
"""


class GrowthAssistantAgent:
    """
    Main conversational agent for grounded product management & growth advising.
    """

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
        self.retriever = get_retriever()

    async def answer(
        self,
        question: str,
        conversation_history: Optional[List[LLMMessage]] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Executes query retrieval, grounding assembly, and conversational generation.
        """
        # 1. Retrieve relevant transcript chunks
        retrieved_chunks = await self.retriever.retrieve(query=question, top_k=top_k)

        # 2. Check evidence confidence
        has_sufficient_evidence = len(retrieved_chunks) > 0 and retrieved_chunks[0].score >= 0.22

        # 3. Assemble transcript context
        context_parts = []
        for idx, c in enumerate(retrieved_chunks, 1):
            context_parts.append(
                f"[Excerpt {idx}] - Title: {c.title}\n"
                f"Guest: {c.guest or 'N/A'}\n"
                f"Speaker: {c.speaker} at {c.timestamp_str}\n"
                f"Link: {c.youtube_timed_url or c.youtube_url or 'N/A'}\n"
                f"Content: {c.text}\n"
            )
        grounded_context = "\n---\n".join(context_parts) if context_parts else "NO MATCHING TRANSCRIPT EVIDENCE FOUND."

        # 4. Assemble messages payload with conversation history
        messages_payload: List[LLMMessage] = []

        # Include prior session turns if available (up to last 6 messages)
        if conversation_history:
            for h in conversation_history[-6:]:
                messages_payload.append(h)

        # Current question with grounded context injected
        user_prompt = f"""QUESTION: {question}

RETRIEVED TRANSCRIPT EVIDENCE:
===============================
{grounded_context}
===============================

INSTRUCTIONS:
Provide a comprehensive, actionable answer strictly grounded in the transcript excerpts above.
Cite the guest and episode context. If the evidence is insufficient, say so honestly.
"""
        messages_payload.append(LLMMessage(role="user", content=user_prompt))

        # 5. Generate response
        logger.info(
            "GrowthAssistant invoking LLM '%s' with %d chunks (top_score=%.3f)",
            self.llm.provider_name,
            len(retrieved_chunks),
            retrieved_chunks[0].score if retrieved_chunks else 0.0
        )

        response = await self.llm.generate(
            messages=messages_payload,
            system_prompt=GROWTH_ASSISTANT_SYSTEM_PROMPT,
            temperature=0.4,
            max_tokens=2048
        )

        # Format source citations for response and UI cards
        sources_meta = [
            {
                "chunk_id": c.chunk_id,
                "episode": c.title,
                "guest": c.guest,
                "speaker": c.speaker,
                "timestamp": c.timestamp_str,
                "url": c.youtube_timed_url or c.youtube_url,
                "relevance_score": c.score,
                "snippet": c.text[:250] + "..." if len(c.text) > 250 else c.text
            }
            for c in retrieved_chunks
        ]

        return {
            "answer": response.content,
            "sources": sources_meta,
            "retrieved_chunks_count": len(retrieved_chunks),
            "evidence_sufficient": has_sufficient_evidence,
            "provider": self.llm.provider_name,
            "model": self.llm.model_name
        }
