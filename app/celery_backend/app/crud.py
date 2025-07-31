from app.celery_backend.app.models import UserSession, get_utc_now
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
from sqlmodel import delete
from typing import List

# Create User Session CRUD operations
async def create_user_session(db: AsyncSession) -> str:
    new_session = UserSession()
    db.add(new_session)
    await db.commit()
    await db.close()

    return new_session.id

# Update User Session by ID
async def update_user_session(session_id: str, db: AsyncSession) -> str | None:
    session = await db.get(UserSession, session_id)
    if not session:
        return None
    session.updated_at = get_utc_now()
    await db.commit()
    await db.close()
    return session.id

# Delete expired sessions
async def delete_expired_sessions(db: AsyncSession) -> List[str] | None:
    thirty_minutes_ago = get_utc_now() - timedelta(minutes=2)
    stmt = (
        delete(UserSession)
        .where(UserSession.updated_at < thirty_minutes_ago)
        .returning(UserSession.id)
    )
    result = await db.execute(stmt)
    await db.commit()
    deleted_ids = [str(row[0]) for row in result.fetchall()]
    return deleted_ids
