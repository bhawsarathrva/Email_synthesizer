import os
from typing import Optional, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://neondb_owner:npg_bdWvh97uAEmD@ep-summer-heart-b70gjut1-pooler.c-13.us-east-1.aws.neon.tech/OrangeData?sslmode=require"
    DATABASE_URL_DIRECT: Optional[str] = None

    # LLM Settings
    LLM_PROVIDER: Literal["ollama", "google", "openai", "anthropic"] = "ollama"
    MODEL_NAME: str = "gemma4:latest"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # API Keys for Cloud Providers (if switched)
    GOOGLE_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # LangSmith Tracing
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: Optional[str] = None

    # App Settings
    FRONTEND_URL: str = "http://localhost:5173"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
