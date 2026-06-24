"""
Step 5: Expert Ranking Engine

Ranks experts using an explainable weighted scoring formula.

Scoring formula:
  final_score = 0.50 × technical_match_score
              + 0.25 × expertise_strength
              + 0.15 × role_score
              + 0.10 × recency_score

Each component is normalized to [0, 1] range.

Input:  list[EnrichedExpertProfile], list[EmbeddingScore], list[ParsedDocument]
Output: list[RankedExpert]  (sorted descending by score)
"""
from __future__ import annotations

import logging
from datetime import date, datetime

from app.pipeline.schemas import (
    EmbeddingScore,
    EnrichedExpertProfile,
    EvidenceDocument,
    ParsedDocument,
    RankedExpert,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Weights
# ──────────────────────────────────────────────

W_TECHNICAL = 0.50
W_EXPERTISE = 0.25
W_ROLE = 0.15
W_RECENCY = 0.10


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _normalize_expertise_strength(
    strengths: list[int],
) -> dict[str, float]:
    """
    Normalize document counts to [0, 1].
    """
    if not strengths:
        return {}
    max_strength = max(strengths)
    if max_strength == 0:
        return {}
    # Map name -> normalized score
    return {}


def _compute_recency_score(
    expert: EnrichedExpertProfile,
    documents: list[ParsedDocument],
) -> float:
    """
    Compute recency score based on the most recent publication date
    among the expert's documents.

    Score decays linearly: documents from 2024+ get 1.0,
    documents from 2000 get 0.0.
    """
    # Build a lookup for document dates
    doc_dates: dict[str, date | None] = {}
    for doc in documents:
        doc_dates[doc.document_id] = doc.publication_date

    # Find the most recent date among this expert's documents
    most_recent: date | None = None
    for ref in expert.documents:
        pub_date = doc_dates.get(ref.document_id)
        if pub_date and (most_recent is None or pub_date > most_recent):
            most_recent = pub_date

    if most_recent is None:
        return 0.5  # neutral when no date available

    # Reference year: 2025 is "very recent" (score=1.0), 2000 is "old" (score=0.0)
    ref_year = 2025
    old_year = 2000
    doc_year = most_recent.year

    if doc_year >= ref_year:
        return 1.0
    if doc_year <= old_year:
        return 0.0

    return round((doc_year - old_year) / (ref_year - old_year), 4)


# ──────────────────────────────────────────────
# Main ranking function
# ──────────────────────────────────────────────

def rank_experts(
    enriched_experts: list[EnrichedExpertProfile],
    embedding_scores: list[EmbeddingScore],
    documents: list[ParsedDocument],
    top_k: int = 5,
) -> list[RankedExpert]:
    """
    Rank experts using the weighted scoring formula.

    Returns top_k ranked experts sorted by score descending,
    each with an explainable reasoning string.
    """
    if not enriched_experts:
        return []

    # Build a lookup: expert name -> embedding score
    score_map: dict[str, EmbeddingScore] = {}
    for es in embedding_scores:
        score_map[es.expert_name] = es

    # Compute expertise_strength normalization
    strengths = [e.expertise_strength for e in enriched_experts]
    max_strength = max(strengths) if strengths else 1
    max_strength = max(max_strength, 1)  # avoid division by zero

    # Score each expert
    ranked: list[tuple[float, EnrichedExpertProfile, EmbeddingScore | None]] = []

    for expert in enriched_experts:
        emb_score = score_map.get(expert.name)

        # 1. Technical match (0-1)
        technical_match = emb_score.technical_match_score if emb_score else 0.0

        # 2. Expertise strength (0-1) — normalized document count
        expertise_strength = round(expert.expertise_strength / max_strength, 4)

        # 3. Role score (already 0-1 from extractor)
        role_score = expert.role_score

        # 4. Recency score (0-1)
        recency_score = _compute_recency_score(expert, documents)

        # Final score
        final_score = (
            W_TECHNICAL * technical_match
            + W_EXPERTISE * expertise_strength
            + W_ROLE * role_score
            + W_RECENCY * recency_score
        )
        final_score = round(final_score, 4)

        ranked.append((final_score, expert, emb_score))

    # Sort descending by score
    ranked.sort(key=lambda x: x[0], reverse=True)

    # Build output
    result: list[RankedExpert] = []
    for i, (score, expert, emb_score) in enumerate(ranked[:top_k]):
        # Build reasoning
        reasoning = _build_reasoning(
            expert, score, emb_score,
            documents,
        )

        # Build evidence
        evidence = [
            EvidenceDocument(
                title=ref.title,
                patent_id=ref.document_id,
                role=ref.role,
            )
            for ref in expert.documents
        ]

        result.append(RankedExpert(
            rank=i + 1,
            name=expert.name,
            score=score,
            expertise=expert.expertise,
            reasoning=reasoning,
            evidence=evidence,
        ))

    return result


# ──────────────────────────────────────────────
# Explainable reasoning
# ──────────────────────────────────────────────

def _build_reasoning(
    expert: EnrichedExpertProfile,
    final_score: float,
    emb_score: EmbeddingScore | None,
    documents: list[ParsedDocument],
) -> str:
    """Build a human-readable explanation of the ranking score."""
    parts: list[str] = []

    parts.append(f"Ranked #{1} with overall score {final_score:.3f}.")

    # Technical match
    if emb_score:
        parts.append(
            f"Technical match score: {emb_score.technical_match_score:.3f} "
            f"(weight: {W_TECHNICAL:.0%})."
        )

    # Expertise strength
    parts.append(
        f"Expertise strength: {expert.expertise_strength} relevant document(s) "
        f"(weight: {W_EXPERTISE:.0%})."
    )

    # Role
    parts.append(
        f"Role: {expert.primary_role} (score: {expert.role_score:.1f}, "
        f"weight: {W_ROLE:.0%})."
    )

    # Skills
    if expert.expertise:
        skills_str = ", ".join(expert.expertise[:5])
        parts.append(f"Key expertise areas: {skills_str}.")

    return " ".join(parts)
