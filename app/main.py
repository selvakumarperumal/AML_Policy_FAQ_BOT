from fastapi import FastAPI
from app.middleware.session_middleware import setup_middleware
from app.api.v1.rag_endpoints import router as rag_router
from app.celery_backend.app.database import init_db

app = FastAPI()
setup_middleware(app)

# @app.on_event("startup")
# async def startup_event():
#     await init_db()

app.include_router(rag_router, prefix="/api/v1")
