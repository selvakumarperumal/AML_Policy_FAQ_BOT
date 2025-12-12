from pydantic_settings import BaseSettings
from pydantic import SecretStr
from functools import lru_cache
from typing import Optional
from


class Settings(BaseSettings):
    """Application settings - from environment variables."""
    
    # AWS (optional for local dev, set by Secrets Manager on Lambda)
    S3_BUCKET: Optional[str] = None
    
    # NVIDIA (required)
    NVIDIA_API_KEY: SecretStr
    NVIDIA_MODEL_NAME: str
    NVIDIA_EMBEDDING_MODEL_NAME: str
    
    # LLM Settings (with defaults)
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 2048
    
    # Vector Store
    VECTOR_STORE_PATH: str = "vector_store"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
