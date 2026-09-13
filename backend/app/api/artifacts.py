from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.repositories import ArtifactRepository
from app.security.sanitizer import sanitize_html

router = APIRouter(prefix="/api/artifacts", tags=["Artifacts"])


class ArtifactCreateRequest(BaseModel):
    session_id: str
    type: str  # 'markdown' or 'html'
    title: Optional[str] = "Generated Artifact"
    content: str


class ArtifactResponse(BaseModel):
    id: str
    session_id: str
    title: str
    type: str
    content: str
    sanitized_content: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
async def create_artifact(
    payload: ArtifactCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    repo = ArtifactRepository(db)
    sanitized = None
    if payload.type.lower() == "html":
        sanitized = sanitize_html(payload.content)
    else:
        sanitized = payload.content

    artifact = await repo.create_artifact(
        session_id=payload.session_id,
        type=payload.type,
        title=payload.title or "Generated Artifact",
        content=payload.content,
        sanitized_content=sanitized
    )
    return artifact


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: str,
    db: AsyncSession = Depends(get_db)
):
    repo = ArtifactRepository(db)
    artifact = await repo.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact '{artifact_id}' not found."
        )
    return artifact


@router.get("/session/{session_id}", response_model=List[ArtifactResponse])
async def list_session_artifacts(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    repo = ArtifactRepository(db)
    return await repo.get_session_artifacts(session_id)
