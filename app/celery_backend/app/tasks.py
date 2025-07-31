from app.celery_backend.app.celery_app import celery_app
from app.celery_backend.app.crud import delete_expired_sessions
from sqlalchemy.ext.asyncio import async_sessionmaker
from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
import os
import logging
from asgiref.sync import async_to_sync
logging.basicConfig(level=logging.WARNING)

async_engine = create_async_engine(settings.DATABASE_URL, echo=True, future=True)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=True,
    autoflush=True,
)

@celery_app.task(name="cleanup_expired_sessions")
def cleanup_expired_sessions():
    async_to_sync(_cleanup_expired_sessions)()

async def _cleanup_expired_sessions():

    async with AsyncSessionLocal() as db:
        expired_ids = await delete_expired_sessions(db)
        vector_directory = settings.UPLOAD_DIRECTORY
        for session_id in expired_ids:
            vector_file_path = f"{vector_directory}/{session_id}"
            try:
                print(f"Deleting expired session file: {vector_file_path}")
                os.remove(vector_file_path)
            except FileNotFoundError:
                continue
        print("Expired sessions cleanup completed.")