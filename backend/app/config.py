import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    APP_NAME: str = "The Lenny Growth Assistant"
    APP_ENV: str = Field(default="development", env="APP_ENV")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./lenny_growth.db",
        env="DATABASE_URL"
    )

    # LLM Settings
    LLM_PROVIDER: str = Field(default="ollama", env="LLM_PROVIDER")
    
    # Ollama settings
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    OLLAMA_MODEL: str = Field(default="llama3.2", env="OLLAMA_MODEL")

    # Cloud LLM settings
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = Field(default="claude-3-5-sonnet-20241022", env="ANTHROPIC_MODEL")
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4o", env="OPENAI_MODEL")

    # Embeddings & Retrieval
    EMBEDDING_PROVIDER: str = Field(default="sentence_transformers", env="EMBEDDING_PROVIDER")
    EMBEDDING_MODEL: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    VECTOR_STORE_PATH: str = Field(default="./data/vector_store", env="VECTOR_STORE_PATH")
    TRANSCRIPTS_DATA_PATH: str = Field(default="./data/transcripts", env="TRANSCRIPTS_DATA_PATH")

    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173",
        env="CORS_ORIGINS"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
