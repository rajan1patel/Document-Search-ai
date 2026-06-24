"""
Step 4: Embedding Layer

Creates text representations for expert profiles and computes semantic
similarity with the user query using in-memory embeddings.

No vector database — everything in memory.

Input:  list[EnrichedExpertProfile], query: str
Output: list[EmbeddingScore]  (one per expert with technical_match_score)
"""
from __future__ import annotations

import logging
import math

from app.pipeline.schemas import EmbeddingScore, EnrichedExpertProfile
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Text representation builder
# ──────────────────────────────────────────────

def _build_expert_text(profile: EnrichedExpertProfile) -> str:
    """
    Build a text representation of the expert for embedding similarity.

    Format:
    "{name} is an expert in {skill1}, {skill2}.
     Relevant works: {title1}, {title2}"
    """
    parts: list[str] = []

    # Name and expertise
    if profile.expertise:
        skills_text = ", ".join(profile.expertise[:10])  # top 10 skills
        parts.append(f"{profile.name} is an expert in {skills_text}.")
    else:
        parts.append(f"{profile.name}.")

    # Domains
    if profile.domains:
        parts.append(f"Domains: {', '.join(profile.domains)}.")

    # Document titles
    titles = [ref.title for ref in profile.documents if ref.title]
    if titles:
        titles_text = ", ".join(titles[:5])  # top 5 titles
        parts.append(f"Relevant works: {titles_text}.")

    return " ".join(parts)


# ──────────────────────────────────────────────
# Cosine similarity
# ──────────────────────────────────────────────

def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ──────────────────────────────────────────────
# Main scoring function
# ──────────────────────────────────────────────

def compute_technical_match(
    experts: list[EnrichedExpertProfile],
    query: str,
) -> list[EmbeddingScore]:
    """
    Compute technical match scores between the user query and each expert.

    Steps:
    1. Build text representation for each expert
    2. Create embedding for the query
    3. Create embedding for each expert text
    4. Compute cosine similarity
    """
    if not experts or not query.strip():
        return [
            EmbeddingScore(expert_name=e.name, technical_match_score=0.0)
            for e in experts
        ]

    # Build expert texts
    expert_texts = [_build_expert_text(expert) for expert in experts]

    # Create embeddings (in memory)
    try:
        query_embedding = embedding_service.create_embedding(query)
        expert_embeddings = embedding_service.create_many(expert_texts)

        scores: list[EmbeddingScore] = []
        for i, expert in enumerate(experts):
            # If embedding creation failed for this text, use zero vector
            if i < len(expert_embeddings) and expert_embeddings[i]:
                sim = _cosine_similarity(query_embedding, expert_embeddings[i])
            else:
                sim = 0.0

            scores.append(EmbeddingScore(
                expert_name=expert.name,
                technical_match_score=round(sim, 4),
                text_representation=expert_texts[i],
            ))

        return scores

    except Exception as exc:
        logger.error("Embedding computation failed: %s", exc, exc_info=True)
        return [
            EmbeddingScore(expert_name=e.name, technical_match_score=0.0)
            for e in experts
        ]
