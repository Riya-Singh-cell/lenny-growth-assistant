import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from app.config import settings

logger = logging.getLogger("lenny.database")

Base = declarative_base()

# Active engine & session maker
engine = None
async_session_factory = None
is_sqlite_fallback = False


def _switch_to_sqlite():
    global engine, async_session_factory, is_sqlite_fallback
    fallback_url = "sqlite+aiosqlite:///./lenny_growth.db"
    engine = create_async_engine(
        fallback_url,
        echo=(settings.LOG_LEVEL == "DEBUG"),
        connect_args={"check_same_thread": False}
    )
    async_session_factory = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession
    )
    is_sqlite_fallback = True
    logger.warning("[FALLBACK] PostgreSQL unreachable. Operating in local SQLite compatibility mode.")


def get_engine():
    global engine, async_session_factory, is_sqlite_fallback
    if engine is None:
        db_url = settings.DATABASE_URL
        if db_url.startswith("sqlite:///"):
            db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")
            is_sqlite_fallback = True

        connect_args = {}
        if "sqlite" in db_url:
            connect_args = {"check_same_thread": False}
            is_sqlite_fallback = True

        try:
            engine = create_async_engine(
                db_url,
                echo=(settings.LOG_LEVEL == "DEBUG"),
                connect_args=connect_args,
                pool_pre_ping=True
            )
            async_session_factory = async_sessionmaker(
                bind=engine,
                expire_on_commit=False,
                class_=AsyncSession
            )
            logger.info("Database engine initialized with %s", db_url.split("@")[-1] if "@" in db_url else db_url)
        except Exception as e:
            logger.warning("Failed to initialize primary database URL (%s): %s", db_url, e)
            _switch_to_sqlite()
    return engine


async def init_db():
    get_engine()
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified/created successfully on %s.", "SQLite" if is_sqlite_fallback else "PostgreSQL")
    except Exception as e:
        logger.warning("Primary database connection error on startup: %s", e)
        _switch_to_sqlite()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully on fallback SQLite engine.")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    get_engine()
    try:
        async with async_session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    except Exception as e:
        if not is_sqlite_fallback and "sqlite" not in settings.DATABASE_URL:
            _switch_to_sqlite()
            async with async_session_factory() as session:
                try:
                    yield session
                except Exception:
                    await session.rollback()
                    raise
                finally:
                    await session.close()
        else:
            raise
