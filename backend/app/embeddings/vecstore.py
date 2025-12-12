"""
Vector store management for the AML Policy FAQ Bot.

Uses Chroma + S3 for persistence on Lambda.
"""

import os
from pathlib import Path

import boto3
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.embeddings.embedder import get_embeddings


def get_text_splitter() -> RecursiveCharacterTextSplitter:
    """Get the configured text splitter."""
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )


def _get_chroma_path() -> str:
    """Get Chroma storage path."""
    return settings.VECTOR_STORE_PATH


def _sync_from_s3():
    """Download Chroma DB from S3."""
    if not settings.S3_BUCKET:
        return
    
    local_path = _get_chroma_path()
    s3 = boto3.client('s3')
    
    try:
        response = s3.list_objects_v2(Bucket=settings.S3_BUCKET, Prefix="chroma_db/")
        if 'Contents' not in response:
            return
        
        Path(local_path).mkdir(parents=True, exist_ok=True)
        
        for obj in response['Contents']:
            key = obj['Key']
            if key.endswith('/'):
                continue
            local_file = os.path.join(local_path, key.replace("chroma_db/", ""))
            Path(local_file).parent.mkdir(parents=True, exist_ok=True)
            s3.download_file(settings.S3_BUCKET, key, local_file)
    except Exception as e:
        print(f"S3 sync error: {e}")


def _sync_to_s3():
    """Upload Chroma DB to S3."""
    if not settings.S3_BUCKET:
        return
    
    local_path = _get_chroma_path()
    if not os.path.exists(local_path):
        return
    
    s3 = boto3.client('s3')
    
    try:
        for root, _, files in os.walk(local_path):
            for file in files:
                local_file = os.path.join(root, file)
                s3_key = "chroma_db/" + os.path.relpath(local_file, local_path)
                s3.upload_file(local_file, settings.S3_BUCKET, s3_key)
    except Exception as e:
        print(f"S3 upload error: {e}")


def get_vector_store() -> Chroma:
    """Get Chroma vector store."""
    _sync_from_s3()
    
    local_path = _get_chroma_path()
    Path(local_path).mkdir(parents=True, exist_ok=True)
    
    return Chroma(
        persist_directory=local_path,
        embedding_function=get_embeddings(),
        collection_name="aml_policies"
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
    
    _sync_to_s3()
    return len(chunks)


def get_retriever(k: int = 6):
    """Get retriever from vector store."""
    return get_vector_store().as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )
