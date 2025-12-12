"""
File parsing utilities for the AML Policy FAQ Bot.

This module handles reading and parsing various document formats
(PDF, DOCX, TXT, etc.) for ingestion into the vector store.
"""

import os
from tempfile import NamedTemporaryFile
import shutil
from typing import Optional

from fastapi import UploadFile
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredHTMLLoader,
    CSVLoader,
)


# Mapping of file extensions to their loaders
LOADER_MAPPING = {
    '.txt': TextLoader,
    '.pdf': PyPDFLoader,
    '.docx': UnstructuredWordDocumentLoader,
    '.doc': UnstructuredWordDocumentLoader,
    '.md': TextLoader,
    '.html': UnstructuredHTMLLoader,
    '.htm': UnstructuredHTMLLoader,
    '.csv': CSVLoader,
    '.rst': TextLoader,
    '.log': TextLoader,
}


def get_file_extension(filename: str) -> str:
    """Get the lowercase file extension."""
    return os.path.splitext(filename)[1].lower()


async def parse_uploaded_file(
    file: UploadFile,
    metadata: Optional[dict] = None
) -> list[Document]:
    """
    Parse an uploaded file into LangChain Documents.
    
    Args:
        file: The uploaded file from FastAPI.
        metadata: Optional metadata to attach to documents.
    
    Returns:
        List of Document objects.
    
    Raises:
        ValueError: If file format is not supported.
    """
    filename = file.filename or "unknown"
    extension = get_file_extension(filename)
    
    if extension not in LOADER_MAPPING:
        raise ValueError(f"Unsupported file format: {extension}")
    
    # Save to temporary file
    suffix = extension
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    
    try:
        # Load using appropriate loader
        loader_class = LOADER_MAPPING[extension]
        loader = loader_class(tmp_path)
        documents = loader.load()
        
        # Add metadata to each document
        base_metadata = {
            "filename": filename,
            "source": filename,
            **(metadata or {})
        }
        
        for doc in documents:
            doc.metadata.update(base_metadata)
        
        return documents
        
    finally:
        # Clean up temporary file
        try:
            os.remove(tmp_path)
        except Exception:
            pass


async def parse_multiple_files(
    files: list[UploadFile],
    shared_metadata: Optional[dict] = None
) -> tuple[list[Document], list[str]]:
    """
    Parse multiple uploaded files.
    
    Args:
        files: List of uploaded files.
        shared_metadata: Metadata to apply to all documents.
    
    Returns:
        Tuple of (list of Documents, list of error messages).
    """
    all_documents: list[Document] = []
    errors: list[str] = []
    
    for file in files:
        try:
            docs = await parse_uploaded_file(file, shared_metadata)
            all_documents.extend(docs)
        except ValueError as e:
            errors.append(f"{file.filename}: {str(e)}")
        except Exception as e:
            errors.append(f"{file.filename}: Failed to parse - {str(e)}")
    
    return all_documents, errors


def get_supported_extensions() -> list[str]:
    """Get list of supported file extensions."""
    return list(LOADER_MAPPING.keys())
