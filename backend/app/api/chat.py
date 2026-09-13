import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.repositories import SessionRepository, MessageRepository, ArtifactRepository
from app.llm.base import LLMMessage
from app.llm.factory import get_llm_provider
from app.agents.router import IntentRouter, AgentIntent
from app.agents.growth_assistant import GrowthAssistantAgent
from app.agents.skills.ship30 import Ship30Skill
from app.agents.skills.artifact_gen import ArtifactSkill
from app.retrieval.retriever import get_retriever

logger = logging.getLogger("lenny.api.chat")
router = APIRouter(prefix="/api/chat", tags=["Chat"])

intent_router = IntentRouter()


class ChatRequest(BaseModel):
    session_id: str
    message: str
    provider: Optional[str] = None
    model: Optional[str] = None


class ArtifactPayload(BaseModel):
    id: str
    session_id: str
    title: str
    type: str
    content: str
    sanitized_content: Optional[str] = None


class ChatResponse(BaseModel):
    message_id: str
    session_id: str
    role: str = "assistant"
    content: str
    intent: str
    sources: List[Dict[str, Any]] = []
    artifact: Optional[ArtifactPayload] = None
    provider: str
    model: str


@router.post("", response_model=ChatResponse)
async def chat_endpoint(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    session_repo = SessionRepository(db)
    msg_repo = MessageRepository(db)
    art_repo = ArtifactRepository(db)

    # 1. Verify session exists
    session = await session_repo.get_session(payload.session_id)
    if not session:
        # Auto-create if not present
        session = await session_repo.create_session(
            title=payload.message[:45] + ("..." if len(payload.message) > 45 else "")
        )

    # 2. Save user message
    await msg_repo.add_message(
        session_id=session.id,
        role="user",
        content=payload.message
    )

    # Update session title if first exchange
    if session.title == "New Conversation":
        new_title = payload.message.strip().split("\n")[0][:45]
        if len(payload.message) > 45:
            new_title += "..."
        await session_repo.update_session_title(session.id, new_title)

    # 3. Retrieve session conversation history (for follow-up context)
    past_messages = await msg_repo.get_session_messages(session.id, limit=10)
    history_messages = [
        LLMMessage(role=m.role, content=m.content)
        for m in past_messages[:-1]  # Exclude current message
    ]

    # 4. Resolve LLM provider
    llm_provider = get_llm_provider(
        provider_override=payload.provider,
        model_override=payload.model
    )

    # 5. Route intent
    detected_intent = intent_router.route(payload.message)

    assistant_content = ""
    sources_meta = []
    artifact_payload = None

    try:
        retriever = get_retriever()

        if detected_intent == AgentIntent.SHIP30_ESSAY:
            # Route to Ship 30 for 30 Skill
            chunks = await retriever.retrieve(query=payload.message, top_k=5)
            ship30 = Ship30Skill(llm_provider)
            result = await ship30.generate_essay(
                topic_or_query=payload.message,
                retrieved_chunks=chunks,
                conversation_history=history_messages
            )
            assistant_content = result["content"]
            sources_meta = result["sources"]

        elif detected_intent == AgentIntent.ARTIFACT_GEN:
            # Route to Artifact Generation Skill
            chunks = await retriever.retrieve(query=payload.message, top_k=4)
            artifact_skill = ArtifactSkill(llm_provider)
            art_result = await artifact_skill.generate_artifact(
                prompt=payload.message,
                retrieved_chunks=chunks
            )
            
            # Save artifact to database
            created_artifact = await art_repo.create_artifact(
                session_id=session.id,
                type=art_result["type"],
                title=art_result["title"],
                content=art_result["raw_content"],
                sanitized_content=art_result["sanitized_content"]
            )
            
            artifact_payload = ArtifactPayload(
                id=created_artifact.id,
                session_id=created_artifact.session_id,
                title=created_artifact.title,
                type=created_artifact.type,
                content=created_artifact.content,
                sanitized_content=created_artifact.sanitized_content
            )

            assistant_content = (
                f"I have generated the requested **{created_artifact.title}** ({created_artifact.type.upper()}). "
                f"It is now open in the **Artifact Viewer** to the right for live inspection and export."
            )
            sources_meta = [
                {
                    "episode": c.title,
                    "guest": c.guest,
                    "speaker": c.speaker,
                    "timestamp": c.timestamp_str,
                    "url": c.youtube_timed_url or c.youtube_url
                }
                for c in chunks
            ]

        else:
            # Default: Grounded Q&A via Growth Assistant
            growth_agent = GrowthAssistantAgent(llm_provider)
            result = await growth_agent.answer(
                question=payload.message,
                conversation_history=history_messages,
                top_k=5
            )
            assistant_content = result["answer"]
            sources_meta = result["sources"]

    except Exception as e:
        logger.exception("Error processing chat request: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )

    # 6. Save assistant response to DB
    saved_msg = await msg_repo.add_message(
        session_id=session.id,
        role="assistant",
        content=assistant_content,
        sources=sources_meta,
        intent=detected_intent.value
    )

    return ChatResponse(
        message_id=saved_msg.id,
        session_id=session.id,
        content=assistant_content,
        intent=detected_intent.value,
        sources=sources_meta,
        artifact=artifact_payload,
        provider=llm_provider.provider_name,
        model=llm_provider.model_name
    )
