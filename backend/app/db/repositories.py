import logging
from typing import List, Optional
from sqlalchemy import select, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import SessionModel, MessageModel, ArtifactModel

logger = logging.getLogger("lenny.repository")


class SessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, title: str = "New Conversation", user_metadata: Optional[dict] = None) -> SessionModel:
        session = SessionModel(title=title, user_metadata=user_metadata or {})
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_session(self, session_id: str) -> Optional[SessionModel]:
        stmt = select(SessionModel).where(SessionModel.id == session_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_sessions(self, limit: int = 50) -> List[SessionModel]:
        stmt = select(SessionModel).order_by(desc(SessionModel.updated_at)).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_session_title(self, session_id: str, title: str) -> Optional[SessionModel]:
        session = await self.get_session(session_id)
        if session:
            session.title = title
            await self.db.commit()
            await self.db.refresh(session)
        return session

    async def delete_session(self, session_id: str) -> bool:
        stmt = delete(SessionModel).where(SessionModel.id == session_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0


class MessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[list] = None,
        intent: Optional[str] = None
    ) -> MessageModel:
        message = MessageModel(
            session_id=session_id,
            role=role,
            content=content,
            sources=sources or [],
            intent=intent
        )
        self.db.add(message)
        
        # Touch session updated_at
        session_stmt = select(SessionModel).where(SessionModel.id == session_id)
        res = await self.db.execute(session_stmt)
        session = res.scalar_one_or_none()
        if session:
            from app.db.models import utc_now
            session.updated_at = utc_now()

        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_session_messages(self, session_id: str, limit: int = 100) -> List[MessageModel]:
        # Strict session isolation: always filter by session_id
        stmt = (
            select(MessageModel)
            .where(MessageModel.session_id == session_id)
            .order_by(MessageModel.created_at.asc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class ArtifactRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_artifact(
        self,
        session_id: str,
        type: str,
        title: str,
        content: str,
        sanitized_content: Optional[str] = None
    ) -> ArtifactModel:
        artifact = ArtifactModel(
            session_id=session_id,
            type=type,
            title=title,
            content=content,
            sanitized_content=sanitized_content
        )
        self.db.add(artifact)
        await self.db.commit()
        await self.db.refresh(artifact)
        return artifact

    async def get_artifact(self, artifact_id: str) -> Optional[ArtifactModel]:
        stmt = select(ArtifactModel).where(ArtifactModel.id == artifact_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_session_artifacts(self, session_id: str) -> List[ArtifactModel]:
        stmt = (
            select(ArtifactModel)
            .where(ArtifactModel.session_id == session_id)
            .order_by(desc(ArtifactModel.created_at))
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
