# This code is part of a utility module for creating and managing embeddings for documents.
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma.vectorstores import Chroma  # Ensure Chroma is correctly imported
from app.core.config import settings
from app.embeddings.embedder import mistral_embedder
from app.utils.read_files import store_and_process_files
import os
from typing import List, Dict
from fastapi import UploadFile
from pathlib import Path
from fastapi import Request, HTTPException

async def create_and_save_vector_db(session_id: str, documents: str) -> str:
    """
    Creates a vector store from the provided documents using the specified embedder.
    If the vector database already exists, it will be appended to the existing one.

    Args:
        session_id (str): Unique session identifier for the DB.
        documents (str): Full document text to embed.

    Returns:
        str: Path where the vector DB is saved.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )

    chunks = text_splitter.split_text(documents)

    persist_dir = os.path.join(settings.UPLOAD_DIRECTORY, session_id)
    Path(persist_dir).mkdir(parents=True, exist_ok=True)

    if os.path.exists(persist_dir):
        # Load existing vector DB and append
        existing_vector_db = Chroma(
            persist_directory=persist_dir,
            embedding_function=mistral_embedder
        )
        existing_vector_db.add_texts(chunks)
        # existing_vector_db.persist()

        message: str = f"Appended to existing vector DB at: {persist_dir}"
    else:
        # Create new vector DB
        Chroma.from_texts(
            texts=chunks,
            embedding=mistral_embedder,
            persist_directory=persist_dir
        )
        # vector_db.persist()
        message: str = f"Created and saved new vector DB at: {persist_dir}"

    return message

async def process_and_create_embeddings(session_id: str, files: List[UploadFile]) -> Dict[str, str]:
    """
    Processes a list of uploaded files and creates embeddings for their content.

    Args:
        session_id (str): The session ID used to identify the vector database.
        files (List[UploadFile]): The list of uploaded files to process.

    Returns:
        str: The file path of the saved vector database.
    """
    file_contents = await store_and_process_files(files)
    await create_and_save_vector_db(session_id=session_id, documents=file_contents)

    return {"message": "Files processed successfully"}

def load_vector_db(request: Request) -> Chroma:
    """
    Loads the vector database from a specified file path.

    Args:
        session_id (str): The session ID used to identify the vector database.

    Returns:
        Chroma: The loaded vector database.
    """
    session_id = request.cookies.get("session_id") or "default_session_id"

    persist_dir = os.path.join(settings.UPLOAD_DIRECTORY, session_id)
    if not os.path.exists(persist_dir):
        raise FileNotFoundError(f"Vector database for session {session_id} not found at {persist_dir}")

    vector_db = Chroma(
        persist_directory=persist_dir,
        embedding_function=mistral_embedder
    )

    if not vector_db:
        raise HTTPException(status_code=404, detail="Vector database not found or is empty. Please upload files to refer and answer questions.")

    return vector_db

