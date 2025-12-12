"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ============== Query Schemas ==============

class QueryRequest(BaseModel):
    """Request schema for querying the AML FAQ bot."""
    
    question: str = Field(
        ...,
        description="The compliance question to ask",
        min_length=1,
        max_length=2000,
        examples=["What is the KYC policy for high-risk customers?"]
    )
    jurisdiction: Optional[str] = Field(
        default=None,
        description="Filter by jurisdiction (e.g., 'India', 'USA')",
        examples=["India"]
    )
    policy_filter: Optional[list[str]] = Field(
        default=None,
        description="Filter by policy types (e.g., ['KYC', 'CDD'])",
        examples=[["KYC", "AML"]]
    )


class SourceDocument(BaseModel):
    """Source document referenced in the answer."""
    
    content: str = Field(
        ...,
        description="Relevant excerpt from the source document"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Document metadata (filename, page, etc.)"
    )


class QueryResponse(BaseModel):
    """Response schema for query results."""
    
    answer: str = Field(
        ...,
        description="The generated answer based on policy documents"
    )
    sources: list[SourceDocument] = Field(
        default_factory=list,
        description="Source documents used to generate the answer"
    )
    escalate: bool = Field(
        default=False,
        description="Whether this query should be escalated to a human"
    )


class StreamChunk(BaseModel):
    """Schema for streaming response chunks via WebSocket."""
    
    type: str = Field(
        ...,
        description="Type of chunk: 'token', 'source', 'done', 'error'"
    )
    content: str = Field(
        default="",
        description="Content of the chunk"
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="Additional metadata for the chunk"
    )


# ============== Document Ingestion Schemas ==============

class IngestResponse(BaseModel):
    """Response schema for document ingestion."""
    
    message: str = Field(
        ...,
        description="Status message"
    )
    documents_processed: int = Field(
        ...,
        description="Number of documents successfully processed"
    )
    chunks_created: int = Field(
        ...,
        description="Total number of text chunks created"
    )


class DocumentMetadata(BaseModel):
    """Metadata for ingested documents."""
    
    filename: str = Field(..., description="Original filename")
    policy_name: Optional[str] = Field(default=None, description="Policy name")
    jurisdiction: Optional[str] = Field(default=None, description="Applicable jurisdiction")
    version: Optional[str] = Field(default=None, description="Document version")
    effective_date: Optional[datetime] = Field(default=None, description="Policy effective date")


# ============== Health Check Schemas ==============

class HealthResponse(BaseModel):
    """Response schema for health check endpoint."""
    
    status: str = Field(
        default="healthy",
        description="Service health status"
    )
    vector_store_available: bool = Field(
        default=True,
        description="Whether vector store is accessible"
    )
    llm_available: bool = Field(
        default=True,
        description="Whether LLM service is accessible"
    )
