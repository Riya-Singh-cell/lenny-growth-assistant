import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, model_validator


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _default_data_path(*parts: str) -> str:
    return str((PROJECT_ROOT / Path(*parts)).resolve())


class Settings(BaseSettings):
    APP_NAME: str = "The Lenny Growth Assistant"
    APP_ENV: str = Field(default="development", env="APP_ENV")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")

    # Canonical Evaluator Database: PostgreSQL
    # If PostgreSQL is not reachable, database.py automatically engages local SQLite compatibility mode.
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgrespassword@localhost:5432/lenny_growth",
        env="DATABASE_URL"
    )

    # LLM Settings
    LLM_PROVIDER: str = Field(default="ollama", env="LLM_PROVIDER")
    
    # Ollama settings (Mandatory local demo)
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    OLLAMA_MODEL: str = Field(default="qwen2.5:0.5b", env="OLLAMA_MODEL")
    OLLAMA_TIMEOUT_SECONDS: float = Field(default=180.0, env="OLLAMA_TIMEOUT_SECONDS")
    OLLAMA_MAX_TOKENS: int = Field(default=512, env="OLLAMA_MAX_TOKENS")

    # Cloud LLM settings
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = Field(default="claude-3-5-sonnet-20241022", env="ANTHROPIC_MODEL")
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4o", env="OPENAI_MODEL")

    # Embeddings & Retrieval
    EMBEDDING_PROVIDER: str = Field(default="sentence_transformers", env="EMBEDDING_PROVIDER")
    EMBEDDING_MODEL: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    VECTOR_STORE_PATH: str = Field(default=_default_data_path("data", "vector_store"), env="VECTOR_STORE_PATH")
    TRANSCRIPTS_DATA_PATH: str = Field(default=_default_data_path("data", "transcripts"), env="TRANSCRIPTS_DATA_PATH")
    
    # RAG Grounding & Refusal Threshold
    RAG_CONFIDENCE_THRESHOLD: float = Field(default=0.22, env="RAG_CONFIDENCE_THRESHOLD")

    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173",
        env="CORS_ORIGINS"
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_repo_relative_paths(cls, values):
        if isinstance(values, dict):
            for key in ("VECTOR_STORE_PATH", "TRANSCRIPTS_DATA_PATH"):
                value = values.get(key)
                if isinstance(value, str) and not os.path.isabs(value):
                    values[key] = str((PROJECT_ROOT / value).resolve())
        return values

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
