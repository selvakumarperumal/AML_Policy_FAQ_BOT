from pydantic_settings import BaseSettings
from pydantic import SecretStr
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings - from environment variables."""
    
    # AWS (optional for local dev, set by Lambda environment)
    S3_BUCKET: Optional[str] = None
    
    # NVIDIA (required in production, optional for testing)
    NVIDIA_API_KEY: Optional[SecretStr] = None
    NVIDIA_MODEL_NAME: str = "meta/llama-3.1-70b-instruct"
    NVIDIA_EMBEDDING_MODEL_NAME: str = "nvidia/nv-embedqa-e5-v5"
    
    # Qdrant Cloud (required for vector store)
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[SecretStr] = None
    QDRANT_COLLECTION_NAME: str = "aml_policies"
    
    # LLM Settings (with defaults)
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 2048
    
    # Text Splitting
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Lazy-loaded settings - only accessed when needed, not at import time
settings: Settings = None  # type: ignore


def init_settings() -> Settings:
    """Initialize settings. Call this when you need settings."""
    global settings
    if settings is None:
        settings = get_settings()
    return settings
