"""
Vector store management for the AML Policy FAQ Bot.

Uses Qdrant Cloud for vector storage.
"""

from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from app.core.config import init_settings
from app.embeddings.embedder import get_embeddings

# NVIDIA embedding dimension (nv-embedqa-e5-v5 = 1024)
EMBEDDING_DIMENSION = 1024


def get_text_splitter() -> RecursiveCharacterTextSplitter:
    """Get the configured text splitter."""
    settings = init_settings()
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )


def _get_qdrant_client() -> QdrantClient:
    """Get Qdrant client configured for Qdrant Cloud."""
    settings = init_settings()
    
    if not settings.QDRANT_URL or not settings.QDRANT_API_KEY:
        raise ValueError("QDRANT_URL and QDRANT_API_KEY are required")
    
    return QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY.get_secret_value(),
        prefer_grpc=True,  # Better performance
    )


def _ensure_collection_exists(client: QdrantClient, collection_name: str):
    """Ensure the collection exists, create if not."""
    collections = client.get_collections().collections
    exists = any(c.name == collection_name for c in collections)
    
    if not exists:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=EMBEDDING_DIMENSION,
                distance=Distance.COSINE,
            ),
        )


def get_vector_store() -> QdrantVectorStore:
    """Get Qdrant vector store."""
    settings = init_settings()
    client = _get_qdrant_client()
    
    # Ensure collection exists
    _ensure_collection_exists(client, settings.QDRANT_COLLECTION_NAME)
    
    return QdrantVectorStore(
        client=client,
        collection_name=settings.QDRANT_COLLECTION_NAME,
        embedding=get_embeddings(),
    )


async def add_documents_to_store(documents: list[Document]) -> int:
    """Add documents to vector store."""
    vector_store = get_vector_store()
    text_splitter = get_text_splitter()
    chunks = text_splitter.split_documents(documents)
    
    if not chunks:
        return 0
    
    texts = [c.page_content for c in chunks]
    metadatas = [c.metadata for c in chunks]
    vector_store.add_texts(texts=texts, metadatas=metadatas)
    
    return len(chunks)


def get_retriever(k: int = 6):
    """Get retriever from vector store."""
    return get_vector_store().as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )
