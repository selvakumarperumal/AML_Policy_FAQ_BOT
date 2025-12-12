"""
AML Policy FAQ Bot - FastAPI Application.

A chatbot for answering compliance officers' questions on AML policies
using RAG (Retrieval-Augmented Generation) with LangChain and LangGraph.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import router as api_router
from app.core.config import init_settings


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler for startup and shutdown events.
    """
    # Startup
    logger.info("Starting AML Policy FAQ Bot...")
    settings = init_settings()
    logger.info(f"Vector store path: {settings.VECTOR_STORE_PATH}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AML Policy FAQ Bot...")


# Create FastAPI application
app = FastAPI(
    title="AML Policy FAQ Bot",
    description="Chatbot for answering compliance officers' questions on AML policies using RAG with LangChain and LangGraph.",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router (no tags here - endpoints have their own tags)
app.include_router(api_router, prefix="/api/v1")


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AML Policy FAQ Bot",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }
