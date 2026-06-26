"""
API Route for Research Expert Discovery Engine.

POST /experts/search

Takes a natural language query and returns ranked experts with
OpenAlex enrichment, LLM-validated topic relevance, and explainable scoring.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.pipeline.research_orchestrator import run_expert_pipeline
from app.pipeline.schemas import (
    ResearchExpertRequest,
    ResearchExpertResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/experts/search",
    response_model=ResearchExpertResponse,
    summary="Discover and rank research experts",
    description=(
        "Takes a natural language query about a research problem and returns "
        "ranked list of expert researchers.\n\n"
        "Pipeline:\n"
        "1. Research Retrieval — fetch relevant works via X-Search API\n"
        "2. Author Extraction — extract ALL authors (no pre-filtering)\n"
        "3. Profile Building — enrich via OpenAlex (h-index, topics, etc.)\n"
        "4. LLM Topic Validation — validate topic relevance to the problem\n"
        "5. Expert Ranking — weighted scoring + explainable reasoning\n\n"
        "All evidence is stored in-memory per query — nothing persists to DB."
    ),
)
async def search_experts(
    request: ResearchExpertRequest,
) -> ResearchExpertResponse:
    """
    Research Expert Discovery endpoint.

    The client sends a natural language query describing their research problem.
    The system returns a ranked list of expert researchers in that domain.
    """
    # logger.info(
    #     "→ POST /experts/search: query='%s' | top_k=%d",
    #     request.query[:80], request.top_k,
    # )

    try:
        result = run_expert_pipeline(request)
        logger.info(
            "← POST /experts/search: %d works, %d authors, %d experts returned",
            result.total_works_found,
            result.total_authors_extracted,
            len(result.experts),
        )
        return result
    except Exception as exc:
        logger.error(
            "Research expert pipeline failed: %s", exc, exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Research expert discovery failed: {exc}",
        )
