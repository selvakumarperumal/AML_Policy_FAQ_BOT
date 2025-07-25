from fastapi import FastAPI, Request
from app.middleware.session_middleware import setup_middleware
from app.api.v1.rag_endpoints import router as rag_router

app = FastAPI()
setup_middleware(app)
app.include_router(rag_router, prefix="/api/v1")
