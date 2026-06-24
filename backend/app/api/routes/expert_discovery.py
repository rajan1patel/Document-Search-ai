"""
API route for Expert Discovery Pipeline.

POST /discover-experts

Accepts a search query and patent documents, returns ranked experts.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.pipeline.schemas import (
    DiscoverExpertsRequest,
    DiscoverExpertsResponse,
)
from app.pipeline.orchestrator import discover_experts

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/discover-experts",
    response_model=DiscoverExpertsResponse,
    summary="Discover and rank experts from patent documents",
    description=(
        "Takes a natural language query, fetches relevant patents from the "
        "external X-Search API automatically, then:\n"
        "1. Parses documents into structured data\n"
        "2. Extracts and deduplicates expert profiles\n"
        "3. Uses LLM to extract technology expertise\n"
        "4. Computes semantic similarity via embeddings\n"
        "5. Ranks experts with an explainable scoring formula\n"
        "6. Enriches top experts with contact info (MVP: mocked)"
    ),
)
async def discover_experts_endpoint(
    request: DiscoverExpertsRequest,
) -> DiscoverExpertsResponse:
    """
    Expert Discovery endpoint.

    The client sends a natural language query.
    The backend fetches patents via X-Search and returns ranked experts.
    """
    try:
        result = discover_experts(request)
        return result
    except Exception as exc:
        logger.error(
            "Expert discovery pipeline failed: %s", exc, exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Expert discovery failed: {exc}",
        )
