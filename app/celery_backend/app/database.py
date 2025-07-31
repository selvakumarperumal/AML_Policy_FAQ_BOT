from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from typing import AsyncGenerator
from app.core.config import settings
from sqlmodel import SQLModel

# Retrieve the database connection URL from the settings
DATABASE_URL = settings.DATABASE_URL

# Raise an error if the DATABASE_URL environment variable is not set
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set or is empty.")
        

"""Create an async engine for asynchronous database operations.
This engine is used for async operations, but the current setup does not support async sessions."""
async_engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    autoflush=False,
    class_=AsyncSession
)

# Define a function to provide an asynchronous database session generator
# This generator yields an AsyncSession object for interacting with the database.
# Generator[Session, None, None]:
# - Session: The generator will yield a Session object (from SQLModel or SQLAlchemy).
# - None: The generator does not accept values via .send() (a rare advanced feature).
# - None: The generator does not return a value when it finishes (i.e., no return x).
"""
def number_doubler():
    while True:
        num = yield
        print(f"Double: {num * 2}")

gen = number_doubler()
next(gen)        # Start the generator (runs up to the first yield)
gen.send(5)      # Sends 5, prints "Double: 10"
gen.send(10)     # Sends 10, prints "Double: 20"
"""

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    
    """
    This function is designed to manage the lifecycle of an asynchronous database session
    using SQLAlchemy's AsyncSession. It ensures that the session is properly created and
    closed after use, preventing resource leaks and maintaining efficient database connections.
    Usage:
        This function is typically used in dependency injection scenarios, such as with 
        FastAPI, where it can be called to provide a database session for handling 
        asynchronous database operations.
        AsyncSession: An instance of SQLAlchemy's asynchronous session, which can be used 
        to perform database queries and transactions.
    Cleanup:
        The session is automatically closed in the `finally` block to ensure proper cleanup 
        of resources, even if an exception occurs during the session's usage.
    """

    """
    Asynchronous generator function to provide a database session.
    
    Yields:
        AsyncSession: An asynchronous database session for performing operations.
    """
    async_db = AsyncSessionLocal()
    try:
        yield async_db
    finally:
        # Close the session after use
        await async_db.close()

# Initialize the database and create tables if they do not exist
async def init_db()-> str:
    """
    Initialize the database and create tables if they do not exist.
    
    Args:
        db (AsyncSession): The database session to use for the operation.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    return "Database initialized and tables created."

    
    