"""
Research Expert Discovery Pipeline Orchestrator

Wires all layers together into a single flow:

  User Query
    → [L1] Research Retrieval (X-Search API)
    → [L2] Paper Evidence Store (in-memory)
    → [L3] Author Extraction (ALL authors, no filtering)
    → [L4] Author Profile Builder (OpenAlex enrichment)
    → [L5] LLM Topic Validation
    → [L6] Expert Ranking Engine
    → Response

Every step has detailed logging for debugging.
"""
from __future__ import annotations

import json
import logging

from app.pipeline.author_extractor import (
    ExtractionResult,
    extract_authors_from_works,
)
from app.pipeline.author_profile_builder import build_profiles
from app.pipeline.expert_ranker import rank_experts, _update_ownership_scores
from app.pipeline.llm_topic_validator import batch_validate
from app.pipeline.paper_evidence import (
    PaperEvidenceStore,
    build_evidence_records,
)
from app.pipeline.research_retrieval import retrieve_works
from app.pipeline.schemas import (
    ResearchExpertOutput,
    ResearchExpertRequest,
    ResearchExpertResponse,
    TopicValidationResult,
)

logger = logging.getLogger(__name__)


def run_expert_pipeline(
    request: ResearchExpertRequest,
) -> ResearchExpertResponse:
    """
    Run the full research expert discovery pipeline.

    Args:
        request: ResearchExpertRequest with query and top_k

    Returns:
        ResearchExpertResponse with ranked experts
    """
    query = request.query
    top_k = request.top_k

    logger.info("=" * 60)
    logger.info("PIPELINE START: query='%s' | top_k=%d", query[:80], top_k)
    logger.info("=" * 60)

    # ── [L1] Research Retrieval ────────────────

    logger.info("[L1] Research Retrieval: fetching works...")
    retrieval_result = retrieve_works(query=query)
    
    # ── [L1] Research Retrieval ────────────────

    query_id = retrieval_result["query_id"]
    works = retrieval_result["works"]
    xsearch_id = retrieval_result["xsearch_id"]

    logger.info(
        json.dumps({
            "event": "research_retrieval",
            "query_id": query_id,
            "xsearch_id": xsearch_id,
            "works_found": len(works),
            "query": query[:80],
        })
    )

    if not works:
        logger.warning("[PIPELINE] No works retrieved. Returning empty result.")
        return ResearchExpertResponse(
            query=query,
            total_works_found=0,
            total_authors_extracted=0,
            experts=[],
        )

    # ── [L2] Paper Evidence Store (in-memory) ──
    logger.info("[L2] Storing evidence in-memory...")
    evidence_records = build_evidence_records(works, query_id)
    stored = PaperEvidenceStore.store_works(query_id, evidence_records)
    logger.info(
        json.dumps({
            "event": "paper_evidence",
            "query_id": query_id,
            "records_stored": stored,
            "sample_works": [
                {"id": r.work_id, "title": r.title[:60], "authors": len(r.author_ids)}
                for r in evidence_records[:3]
            ],
        })
    )

    # ── [L3] Author Extraction (ALL authors) ────
    logger.info("[L3] Extracting ALL authors from works...")
    extraction: ExtractionResult = extract_authors_from_works(works)
    total_authors = extraction.total_authors

    logger.info(
        json.dumps({
            "event": "author_extraction",
            "query_id": query_id,
            "total_works": extraction.total_works,
            "total_authors": total_authors,
            "sample_authors": [
                {"id": aid, "name": e.name, "matched_works": len(e.matched_works)}
                for aid, e in list(extraction.authors.items())[:5]
            ],
        })
    )

    if total_authors == 0:
        logger.warning("[PIPELINE] No authors extracted. Returning empty result.")
        return ResearchExpertResponse(
            query=query,
            total_works_found=len(works),
            total_authors_extracted=0,
            experts=[],
        )

    # ── [L4] Author Profile Builder ────────────
    logger.info("[L4] Building author profiles via OpenAlex...")
    profiles = build_profiles(
        authors=extraction.authors,
        problem_domain=query,
    )
    logger.info(
        json.dumps({
            "event": "author_profiles",
            "query_id": query_id,
            "profiles_built": len(profiles),
            "sample_profiles": [
                {
                    "name": p.name,
                    "h_index": p.h_index,
                    "topics_count": len(p.topics),
                    "institution": p.institution,
                    "works_count": p.works_count,
                    "first_year": p.first_year,
                    "last_year": p.last_year,
                }
                for p in profiles[:5]
            ],
        })
    )

    if not profiles:
        logger.warning("[PIPELINE] No profiles built. Returning empty result.")
        return ResearchExpertResponse(
            query=query,
            total_works_found=len(works),
            total_authors_extracted=total_authors,
            experts=[],
        )

    # ── [L5] LLM Topic Validation ──────────────
    logger.info("[L5] Validating author topics against problem...")
    validation_results = batch_validate(problem=query, profiles=profiles)

    # Build validation dict and filter profiles
    validations: dict[str, TopicValidationResult] = {}
    validated_profiles = []

    for profile, validation in validation_results:
        validations[profile.author_id] = validation
        # Only keep authors with match="yes"
        if validation.match == "yes":
            validated_profiles.append(profile)

    logger.info(
        json.dumps({
            "event": "llm_validation",
            "query_id": query_id,
            "total_profiles": len(profiles),
            "matched": len(validated_profiles),
            "filtered_out": len(profiles) - len(validated_profiles),
            "decisions": [
                {
                    "name": p.name,
                    "match": validations.get(p.author_id, TopicValidationResult()).match,
                    "matched_topics": [
                        t.get("topic_name") for t in
                        (validations.get(p.author_id, TopicValidationResult()).matched_topics or [])
                    ],
                }
                for p in profiles[:8]
            ],
        })
    )

    if not validated_profiles:
        logger.warning("[PIPELINE] No validated experts. Returning empty result.")
        return ResearchExpertResponse(
            query=query,
            total_works_found=len(works),
            total_authors_extracted=total_authors,
            experts=[],
        )

    # ── [L6] Expert Ranking Engine ─────────────
    logger.info("[L6] Ranking validated experts...")

    # Extract author evidence for ownership scoring
    author_evidence = {}
    for aid, evidence in extraction.authors.items():
        author_evidence[aid] = {
            "positions": evidence.positions,
        }

    ranked = rank_experts(
        profiles=validated_profiles,
        validations=validations,
        problem=query,
        top_k=top_k,
    )

    if ranked:
        _update_ownership_scores(
            [{"profile": r, "scores": r.score_breakdown} for r in ranked],
            author_evidence,
        )

    logger.info(
        json.dumps({
            "event": "expert_ranking",
            "query_id": query_id,
            "ranked_count": len(ranked),
            "top_experts": [
                {
                    "rank": i + 1,
                    "name": r.name,
                    "score": r.expert_score,
                    "h_index": r.metrics.get("h_index", 0),
                    "institution": r.institution,
                    "matched_topic": r.matched_topic.get("topic_name") if r.matched_topic else None,
                    "score_breakdown": {
                        k: round(v, 3) for k, v in r.score_breakdown.__dict__.items()
                    },
                }
                for i, r in enumerate(ranked[:top_k])
            ],
        })
    )

    # ── Build Response ─────────────────────────
    experts = []
    for r in ranked:
        experts.append(ResearchExpertOutput(
            author_id=r.author_id,
            author=r.name,
            score=r.expert_score,
            metrics=r.metrics,
            matched_topic=r.matched_topic,
            all_topics=r.all_topics,
            why=r.reasoning,
            institution=r.institution,
            first_year=r.first_year,
            last_year=r.last_year,
            openalex_url=f"https://openalex.org/authors/{r.author_id}",
        ))

    logger.info(
        json.dumps({
            "event": "pipeline_complete",
            "query_id": query_id,
            "query": query[:80],
            "total_works": len(works),
            "total_authors": total_authors,
            "experts_returned": len(experts),
            "final_experts": [
                {
                    "rank": i + 1,
                    "author": e.author,
                    "score": e.score,
                    "institution": e.institution,
                    "h_index": e.metrics.get("h_index", 0),
                }
                for i, e in enumerate(experts)
            ],
        })
    )

    return ResearchExpertResponse(
        query=query,
        total_works_found=len(works),
        total_authors_extracted=total_authors,
        experts=experts,
    )
