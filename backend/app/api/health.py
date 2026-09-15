import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List
from app.config import settings
from app.llm.factory import get_llm_provider
from app.retrieval.retriever import get_retriever

logger = logging.getLogger("lenny.api.health")
router = APIRouter(tags=["Health & Diagnostics"])


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    environment: str


class ReadinessResponse(BaseModel):
    status: str  # "ready" or "degraded" or "not_ready"
    database: str
    llm_provider: Dict[str, Any]
    vector_store: Dict[str, Any]


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        app_name=settings.APP_NAME,
        version="1.0.0",
        environment=settings.APP_ENV
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check():
    # Check LLM provider
    provider = get_llm_provider()
    llm_health = await provider.check_health()

    # Check Vector store
    retriever = get_retriever()
    total_chunks = retriever.total_chunks

    # Check DB
    from app.db.database import get_engine, is_sqlite_fallback
    from sqlalchemy import text
    engine = get_engine()
    db_type = "SQLite fallback" if is_sqlite_fallback or "sqlite" in str(engine.url) else "PostgreSQL"
    db_status = f"connected ({db_type})"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    overall_status = "ready"
    if not llm_health.is_available or total_chunks == 0 or "error" in db_status:
        overall_status = "degraded"

    return ReadinessResponse(
        status=overall_status,
        database=db_status,
        llm_provider={
            "provider": llm_health.provider,
            "model": llm_health.model,
            "is_available": llm_health.is_available,
            "error": llm_health.error,
            "available_models": llm_health.available_models
        },
        vector_store={
            "total_chunks": total_chunks,
            "is_populated": total_chunks > 0,
            "store_path": retriever.store_dir
        }
    )
