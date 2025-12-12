"""
API endpoints for the AML Policy FAQ Bot.

This module provides:
- WebSocket endpoint for streaming Q&A
- HTTP endpoints for document ingestion
- Health check endpoint
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse

from app.schemas import (
    QueryRequest,
    QueryResponse,
    IngestResponse,
    HealthResponse,
    StreamChunk,
    DocumentMetadata,
)
from app.agents.rag_agent import RAGAgent
from app.embeddings.vecstore import get_vector_store, add_documents_to_store
from app.utils.file_parser import parse_multiple_files, get_supported_extensions
from app.core.config import settings


logger = logging.getLogger(__name__)
router = APIRouter()


# ============== Health Check ==============

@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Check the health status of the API."""
    vector_store_ok = True
    llm_ok = True
    
    # Check vector store (works with both OpenSearch and Chroma)
    try:
        vector_store = get_vector_store()
        # Use similarity_search - works with all vector stores
        _ = vector_store.similarity_search("health check", k=1)
    except Exception as e:
        logger.error(f"Vector store health check failed: {e}")
        vector_store_ok = False
    
    return HealthResponse(
        status="healthy" if (vector_store_ok and llm_ok) else "degraded",
        vector_store_available=vector_store_ok,
        llm_available=llm_ok
    )


# ============== Document Ingestion ==============

@router.post("/ingest", response_model=IngestResponse, tags=["Ingestion"])
async def ingest_documents(
    files: list[UploadFile] = File(..., description="Policy documents to ingest"),
    policy_name: Optional[str] = Form(default=None, description="Policy name for metadata"),
    jurisdiction: Optional[str] = Form(default=None, description="Jurisdiction for metadata"),
    version: Optional[str] = Form(default=None, description="Document version"),
) -> IngestResponse:
    """Ingest policy documents into the vector store."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    metadata = {}
    if policy_name:
        metadata["policy_name"] = policy_name
    if jurisdiction:
        metadata["jurisdiction"] = jurisdiction
    if version:
        metadata["version"] = version
    
    documents, errors = await parse_multiple_files(files, metadata)
    
    if errors:
        logger.warning(f"File parsing errors: {errors}")
    
    if not documents:
        raise HTTPException(
            status_code=400,
            detail=f"No documents could be parsed. Errors: {errors}"
        )
    
    try:
        chunks_created = await add_documents_to_store(documents)
    except Exception as e:
        logger.error(f"Failed to add documents to vector store: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store documents: {str(e)}"
        )
    
    message = f"Successfully processed {len(documents)} document(s)"
    if errors:
        message += f". Warnings: {len(errors)} file(s) had issues"
    
    return IngestResponse(
        message=message,
        documents_processed=len(files) - len(errors),
        chunks_created=chunks_created
    )


@router.get("/supported-formats", tags=["Ingestion"])
async def get_supported_formats() -> dict:
    """Get list of supported file formats for ingestion."""
    return {"formats": get_supported_extensions()}


# ============== Query Endpoints ==============

@router.post("/query", response_model=QueryResponse, tags=["Query"])
async def query_sync(request: QueryRequest) -> QueryResponse:
    """Submit a question and receive a complete answer."""
    try:
        vector_store = get_vector_store()
        agent = RAGAgent(vector_store)
        
        result = await agent.query(
            question=request.question,
            jurisdiction=request.jurisdiction,
            policy_filter=request.policy_filter
        )
        
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            escalate=result["escalate"]
        )
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )


# ============== WebSocket Streaming ==============

@router.websocket("/ws/query")
async def query_websocket(websocket: WebSocket):
    """WebSocket endpoint for streaming Q&A."""
    await websocket.accept()
    
    try:
        vector_store = get_vector_store()
        agent = RAGAgent(vector_store)
        
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "content": "Invalid JSON format"})
                continue
            
            if message.get("type") == "close":
                break
            
            question = message.get("question")
            if not question:
                await websocket.send_json({"type": "error", "content": "Missing 'question' field"})
                continue
            
            jurisdiction = message.get("jurisdiction")
            policy_filter = message.get("policy_filter")
            
            try:
                async for chunk in agent.stream_query(
                    question=question,
                    jurisdiction=jurisdiction,
                    policy_filter=policy_filter
                ):
                    await websocket.send_json(chunk.model_dump())
                    
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                await websocket.send_json({"type": "error", "content": f"Error: {str(e)}"})
    
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except Exception:
            pass
