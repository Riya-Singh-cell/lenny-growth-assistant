import time
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db.database import init_db
from app.api.health import router as health_router
from app.api.sessions import router as sessions_router
from app.api.chat import router as chat_router
from app.api.artifacts import router as artifacts_router
from app.retrieval.retriever import get_retriever
from app.retrieval.ingestion import ingest_transcripts

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("lenny.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing The Lenny Growth Assistant backend...")
    
    # 1. Initialize DB tables
    try:
        await init_db()
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.warning("Database auto-init warning: %s", e)

    # 2. Check knowledge base vector store
    retriever = get_retriever()
    logger.info("Current vector store chunk count: %d", retriever.total_chunks)
    if retriever.total_chunks == 0:
        logger.info("Vector store is empty on startup. Triggering initial background ingestion...")
        try:
            # Seed with top episodes for immediate evaluator readiness
            await ingest_transcripts(limit=5)
            logger.info("Initial knowledge base seeded with %d chunks.", retriever.total_chunks)
        except Exception as e:
            logger.warning("Initial background ingestion deferred: %s", e)

    yield

    logger.info("Shutting down The Lenny Growth Assistant backend...")


app = FastAPI(
    title="The Lenny Growth Assistant API",
    description="Enterprise-grade AI product advisor strictly grounded in Lenny's Podcast transcripts.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_and_request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start_time = time.time()
    
    logger.info("[%s] Started %s %s", request_id, request.method, request.url.path)
    try:
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        logger.info("[%s] Completed %s %s with %d in %sms", request_id, request.method, request.url.path, response.status_code, duration_ms)
        return response
    except Exception as exc:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.exception("[%s] Unhandled exception processing %s: %s (took %sms)", request_id, request.url.path, exc, duration_ms)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": str(exc),
                "request_id": request_id
            },
            headers={"X-Request-ID": request_id}
        )


# Register API Routers
app.include_router(health_router)
app.include_router(sessions_router)
app.include_router(chat_router)
app.include_router(artifacts_router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to The Lenny Growth Assistant API",
        "docs": "/docs",
        "health": "/health",
        "readiness": "/ready"
    }
