from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user import User

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.search_service import semantic_search
from app.services.dspy_service import dspy_service


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post("", response_model=ChatResponse)
async def chat(
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Ask a question about your documents. The agent retrieves relevant
    chunks and generates an answer using DSPy + LLM."""

    # 1. Retrieve relevant document chunks
    results = await semantic_search(
        db,
        data.query,
        data.limit,
        user.id,
    )

    # 2. Generate answer via DSPy
    #    Convert Pydantic messages → plain dicts for the service
    history_dicts = [m.model_dump() for m in data.history]

    answer = await dspy_service.generate_answer(
        query=data.query,
        sources=results,
        history=history_dicts,
    )

    # 3. Return answer with sources
    return ChatResponse(
        answer=answer,
        sources=results,
    )
