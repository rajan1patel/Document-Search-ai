import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.database.connection import get_db
from app.models.user import User

from app.schemas.chat import ChatRequest, ChatResponse, GroupedSource
from app.services.search_service import semantic_search
from app.services.dspy_service import dspy_service

logger = logging.getLogger(__name__)

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

    try:
        answer = await dspy_service.generate_answer(
            query=data.query,
            sources=results,
            history=history_dicts,
        )
    except Exception as e:
        logger.error("DSPy answer generation failed: %s", e, exc_info=True)
        # Fallback: return a helpful message when the LLM is unavailable
        answer = (
            "I found relevant documents but could not generate a response "
            "because the AI model is currently unavailable. "
            "Please check that your OpenRouter API key is valid and configured in the `.env` file.\n\n"
            "**Documents found:**\n" +
            "\n".join(
                f"- {r.get('filename', 'Unknown')} (score: {r.get('score', 0):.2f})"
                for r in results[:5]
            ) if results else "No relevant documents were found."
        )

    # 3. Group sources by file and return
    grouped_sources = dspy_service.group_sources_by_file(results)

    return ChatResponse(
        answer=answer,
        sources=results,
        grouped_sources=[GroupedSource(**g) for g in grouped_sources],
    )
