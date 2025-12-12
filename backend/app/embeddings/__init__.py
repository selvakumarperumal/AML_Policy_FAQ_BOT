"""Embeddings module."""

from app.embeddings.embedder import get_embeddings
from app.embeddings.vecstore import (
    get_vector_store,
    add_documents_to_store,
    get_retriever,
)

__all__ = [
    "get_embeddings",
    "get_vector_store",
    "add_documents_to_store",
    "get_retriever",
]
