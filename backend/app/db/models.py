import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SessionModel(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), default="New Conversation")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    user_metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    # Relationships
    messages: Mapped[List["MessageModel"]] = relationship(
        "MessageModel",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="MessageModel.created_at"
    )
    artifacts: Mapped[List["ArtifactModel"]] = relationship(
        "ArtifactModel",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ArtifactModel.created_at"
    )


class MessageModel(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(32))  # 'user', 'assistant', 'system'
    content: Mapped[str] = mapped_column(Text)
    sources: Mapped[Optional[list]] = mapped_column(JSON, default=list)  # transcript sources/citations
    intent: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # 'GROUNDED_QA', 'SHIP30_ESSAY', 'ARTIFACT_GEN'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    session: Mapped["SessionModel"] = relationship("SessionModel", back_populates="messages")


class ArtifactModel(Base):
    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255), default="Generated Artifact")
    type: Mapped[str] = mapped_column(String(32))  # 'markdown' or 'html'
    content: Mapped[str] = mapped_column(Text)  # raw content
    sanitized_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # security cleaned content
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    session: Mapped["SessionModel"] = relationship("SessionModel", back_populates="artifacts")
