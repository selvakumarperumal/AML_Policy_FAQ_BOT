"""NVIDIA AI Embeddings for the AML Policy FAQ Bot."""

from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from app.core.config import init_settings


def get_embeddings() -> NVIDIAEmbeddings:
    """Get the configured NVIDIA embeddings instance."""
    settings = init_settings()
    if not settings.NVIDIA_API_KEY:
        raise ValueError("NVIDIA_API_KEY is required")
    return NVIDIAEmbeddings(
        model=settings.NVIDIA_EMBEDDING_MODEL_NAME,
        api_key=settings.NVIDIA_API_KEY.get_secret_value(),
    )
