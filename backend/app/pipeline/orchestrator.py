"""
Expert Discovery Pipeline Orchestrator

Wires all pipeline steps together into a single flow:

  User Query → X-Search API → Parser → Expert Extractor
  → Tech Extractor (LLM) → Embedding → Ranking Engine
  → Contact Enrichment → Response

Each step is independently testable.
"""
from __future__ import annotations

import logging

from app.pipeline.schemas import (
    DiscoverExpertsRequest,
    DiscoverExpertsResponse,
    EmbeddingScore,
    EnrichedExpertProfile,
    ExpertOutput,
    ExpertProfile,
    ParsedDocument,
    RankedExpert,
)
from app.pipeline.parser import parse_documents
from app.pipeline.expert_extractor import extract_experts
from app.pipeline.technology_extractor import enrich_experts
from app.pipeline.embedding_service import compute_technical_match
from app.pipeline.ranking_engine import rank_experts
from app.pipeline.enrichment_service import enrich_contacts
from app.services.xsearch_client import xsearch_client

logger = logging.getLogger(__name__)


def discover_experts(
    request: DiscoverExpertsRequest,
) -> DiscoverExpertsResponse:
    """
    Run the full expert discovery pipeline.

    Steps:
    0. Call X-Search API to fetch relevant patent documents
    1. Parse raw documents → ParsedDocument list
    2. Extract experts → ExpertProfile list (deduplicated)
    3. Extract technology via LLM → EnrichedExpertProfile list
    4. Compute embeddings → EmbeddingScore list
    5. Rank experts → RankedExpert list
    6. Enrich contacts → RankedExpert list (with contact info)
    7. Build response
    """
    query = request.query
    top_k = request.top_k

    logger.info(
        "Pipeline start: query='%s' | top_k=%d",
        query[:80], top_k,
    )

    # ── Step 0: Fetch documents via X-Search ─
    logger.info("Step 0: Fetching documents from X-Search API...")
    try:
        xsearch_response = xsearch_client.search(
            nl_query=query,
            page=request.page,
            page_size=request.page_size,
            api_key_override=request.xsearch_api_key,
        )
    except RuntimeError as exc:
        logger.error("X-Search failed: %s", exc)
        return DiscoverExpertsResponse(
            query=query,
            total_documents_found=0,
            experts=[],
        )

    xsearch_id = xsearch_client.get_xsearch_id(xsearch_response)
    raw_docs = xsearch_client.extract_hits(xsearch_response)

    if not raw_docs:
        logger.warning("X-Search returned no hits for query: %s", query[:80])
        return DiscoverExpertsResponse(
            query=query,
            xsearch_id=xsearch_id,
            total_documents_found=0,
            experts=[],
        )

    logger.info(
        "  → X-Search returned %d documents (xsearch_id=%s)",
        len(raw_docs), xsearch_id,
    )

    # ── Step 1: Parse documents ─────────────
    logger.info("Step 1: Parsing %d documents...", len(raw_docs))
    parsed_docs: list[ParsedDocument] = parse_documents(raw_docs)
    logger.info("  → %d documents parsed", len(parsed_docs))

    # ── Step 2: Extract experts ─────────────
    logger.info("Step 2: Extracting experts...")
    expert_profiles: list[ExpertProfile] = extract_experts(parsed_docs)
    logger.info("  → %d unique expert profiles", len(expert_profiles))

    if not expert_profiles:
        return DiscoverExpertsResponse(
            query=query,
            total_documents_found=len(parsed_docs),
            experts=[],
        )

    # ── Step 3: Extract technology via LLM ───
    logger.info("Step 3: Extracting technology expertise via LLM...")
    enriched_experts: list[EnrichedExpertProfile] = enrich_experts(
        documents=parsed_docs,
        expert_profiles=expert_profiles,
    )
    logger.info("  → %d enriched profiles", len(enriched_experts))

    # ── Step 4: Compute embeddings ──────────
    logger.info("Step 4: Computing technical match via embeddings...")
    embedding_scores: list[EmbeddingScore] = compute_technical_match(
        experts=enriched_experts,
        query=query,
    )
    logger.info("  → %d embedding scores computed", len(embedding_scores))

    # ── Step 5: Rank experts ────────────────
    logger.info("Step 5: Ranking experts...")
    ranked: list[RankedExpert] = rank_experts(
        enriched_experts=enriched_experts,
        embedding_scores=embedding_scores,
        documents=parsed_docs,
        top_k=top_k,
    )
    logger.info("  → %d experts ranked", len(ranked))

    # ── Step 6: Enrich contacts ─────────────
    logger.info("Step 6: Enriching contacts...")
    # Build org lookup from parsed docs
    org_lookup: dict[str, list[str]] = {}
    for doc in parsed_docs:
        for inv in doc.inventors:
            if inv not in org_lookup:
                org_lookup[inv] = []
            org_lookup[inv].extend(doc.assignees)
    for name in org_lookup:
        org_lookup[name] = list(set(org_lookup[name]))

    ranked = enrich_contacts(ranked, organizations=org_lookup)
    logger.info("  → contacts enriched")

    # ── Step 7: Build response ──────────────
    logger.info("Step 7: Building response...")
    expert_outputs = [
        ExpertOutput(
            rank=e.rank,
            name=e.name,
            score=e.score,
            expertise=e.expertise,
            reasoning=e.reasoning,
            evidence=e.evidence,
            contact=e.contact,
        )
        for e in ranked
    ]

    return DiscoverExpertsResponse(
        query=query,
        xsearch_id=xsearch_id,
        total_documents_found=len(parsed_docs),
        raw_documents=raw_docs,
        experts=expert_outputs,
    )
