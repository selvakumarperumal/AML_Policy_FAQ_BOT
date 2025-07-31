from fastapi import Request, APIRouter, Response
from fastapi import UploadFile, File
from typing import List
from app.embeddings.vecstore import process_and_create_embeddings, load_vector_db
from fastapi import Depends
from app.retrieval.qa_chain import answer_question
from langchain_chroma.vectorstores import Chroma
from typing import Dict, List
from app.celery_backend.app.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.celery_backend.app.models import UserSession
from app.celery_backend.app.crud import create_user_session

router = APIRouter()

@router.post("/process-input")
async def process_input(
    request: Request,
    files: List[UploadFile] = File(...),
):
    """Processes uploaded files and returns their combined content. And saves the vector database."""

    session_id = request.cookies.get("session_id") or "default_session_id"

    await process_and_create_embeddings(session_id, files)

    return {"message": "Files Processed Successfully"}

@router.post("/answer-question")
async def answer_query(
    question: str,
    vector_db: Chroma = Depends(load_vector_db)
) -> Dict[str, str]:
    """Answers a question using the vector database."""

    retriever = vector_db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}  # Adjust the number of documents to retrieve
    )
    if not retriever:
        return {"message": "No relevant documents found."}
    response = await answer_question(question, retriever)
    return {"answer": response}
