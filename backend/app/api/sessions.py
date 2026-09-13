from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.repositories import SessionRepository, MessageRepository, ArtifactRepository

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])


class SessionCreateRequest(BaseModel):
    title: Optional[str] = "New Conversation"
    user_metadata: Optional[Dict[str, Any]] = None


class SessionSummary(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    user_metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class MessageItem(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    sources: Optional[list] = []
    intent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ArtifactSummary(BaseModel):
    id: str
    session_id: str
    title: str
    type: str
    created_at: datetime

    class Config:
        from_attributes = True


class SessionDetail(SessionSummary):
    messages: List[MessageItem] = []
    artifacts: List[ArtifactSummary] = []


@router.post("", response_model=SessionSummary, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    repo = SessionRepository(db)
    session = await repo.create_session(
        title=payload.title or "New Conversation",
        user_metadata=payload.user_metadata
    )
    return session


@router.get("", response_model=List[SessionSummary])
async def list_sessions(
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    repo = SessionRepository(db)
    return await repo.list_sessions(limit=limit)


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    session_repo = SessionRepository(db)
    msg_repo = MessageRepository(db)
    art_repo = ArtifactRepository(db)

    session = await session_repo.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found."
        )

    messages = await msg_repo.get_session_messages(session_id)
    artifacts = await art_repo.get_session_artifacts(session_id)

    return SessionDetail(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        user_metadata=session.user_metadata,
        messages=messages,
        artifacts=artifacts
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    repo = SessionRepository(db)
    deleted = await repo.delete_session(session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found."
        )
    return None
