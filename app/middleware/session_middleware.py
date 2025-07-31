from fastapi import Request, FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from app.celery_backend.app.crud import create_user_session, update_user_session
from app.celery_backend.app.database import get_async_db

class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        session_id = request.cookies.get("session_id")
        response = await call_next(request)

        # Manually acquire DB session from async generator
        async for db in get_async_db():
            if not session_id:
                # Create a new session, store its ID in cookie
                session_id = await create_user_session(db)
                response.set_cookie(
                    key="session_id",
                    value=session_id,
                    httponly=True,
                    secure=True,
                    samesite="Lax",
                    max_age=2*60  # 2 minutes
                )
            else:
                # Update session timestamp
                updated_id = await update_user_session(session_id, db)
                response.set_cookie(
                    key="session_id",
                    value=updated_id or session_id,  # fallback to old if update fails
                    httponly=True,
                    secure=True,
                    samesite="Lax",
                    max_age=2*60  # 2 minutes
                )
            break  # Only need the first yielded db session

        return response

def setup_middleware(app: FastAPI):
    app.add_middleware(SessionMiddleware)