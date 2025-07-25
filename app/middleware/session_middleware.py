from fastapi import Request, FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
import uuid


class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        session_id = request.cookies.get("session_id")
        response = await call_next(request)

        if not session_id:
            session_id = str(uuid.uuid4())
            response.set_cookie(
                key="session_id",
                value=session_id,
                httponly=True,
                secure=True,
                samesite="Lax",
                max_age=120*60  # Expiration time in seconds (15 minutes)
            )

        return response
    
def setup_middleware(app: FastAPI):
    app.add_middleware(SessionMiddleware)