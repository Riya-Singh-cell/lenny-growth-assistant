import pytest
from app.db.repositories import SessionRepository, MessageRepository, ArtifactRepository


@pytest.mark.asyncio
async def test_session_creation_and_isolation(db_session):
    session_repo = SessionRepository(db_session)
    msg_repo = MessageRepository(db_session)

    # 1. Create Session A and Session B
    session_a = await session_repo.create_session(title="Chat A")
    session_b = await session_repo.create_session(title="Chat B")

    assert session_a.id != session_b.id

    # 2. Add messages to Session A
    await msg_repo.add_message(
        session_id=session_a.id,
        role="user",
        content="Secret message for Session A"
    )
    await msg_repo.add_message(
        session_id=session_a.id,
        role="assistant",
        content="Answer for Session A"
    )

    # 3. Add message to Session B
    await msg_repo.add_message(
        session_id=session_b.id,
        role="user",
        content="Message for Session B"
    )

    # 4. Strict session isolation check
    messages_a = await msg_repo.get_session_messages(session_a.id)
    messages_b = await msg_repo.get_session_messages(session_b.id)

    assert len(messages_a) == 2
    assert len(messages_b) == 1
    assert all("Session A" in m.content for m in messages_a)
    assert all("Session B" in m.content for m in messages_b)
    # Chat B NEVER sees Chat A
    assert not any("Secret message for Session A" in m.content for m in messages_b)


@pytest.mark.asyncio
async def test_artifact_persistence(db_session):
    session_repo = SessionRepository(db_session)
    art_repo = ArtifactRepository(db_session)

    session = await session_repo.create_session(title="Framework Session")

    artifact = await art_repo.create_artifact(
        session_id=session.id,
        type="markdown",
        title="B2B Growth Engine",
        content="# B2B Growth Engine\nActionable steps...",
        sanitized_content="# B2B Growth Engine\nActionable steps..."
    )

    assert artifact.id is not None
    assert artifact.session_id == session.id

    fetched = await art_repo.get_artifact(artifact.id)
    assert fetched is not None
    assert fetched.title == "B2B Growth Engine"

    session_arts = await art_repo.get_session_artifacts(session.id)
    assert len(session_arts) == 1
