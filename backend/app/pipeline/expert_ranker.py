"""
Layer 6: Expert Ranking Engine

Ranks validated authors using a weighted scoring formula.

Scoring formula:
  expert_score =
    0.45 * problem_topic_match
  + 0.25 * topic_depth
  + 0.15 * research_continuity
  + 0.10 * research_ownership
  + 0.05 * impact

Component definitions:
  - problem_topic_match: Raw count of how many distinct topics matched the query
    (normalized across the candidate pool — rewards breadth of relevance)
  - topic_depth:         Ratio of matched topics to total author topics
    (higher = more focused, a larger share of their work is relevant)
  - research_continuity: Career span in years (capped at 30)
  - research_ownership:  Leadership score from first/last author positions
  - impact:              h-index (capped at 80)

Steps:
  1. Pool normalization — each component is normalized across candidates
  2. Weighted formula application
  3. Tiebreakers: final_score → problem_match → h_index
  4. Explainable reasoning generation
  5. 0-100 scale for readability
"""
from __future__ import annotations

import logging
from typing import Optional

from app.pipeline.schemas import (
    AuthorProfileSchema,
    ComponentScores,
    RankedExpertSchema,
    TopicValidationResult,
)

logger = logging.getLogger(__name__)


def rank_experts(
    profiles: list[AuthorProfileSchema],
    validations: dict[str, TopicValidationResult],
    problem: str = "",
    top_k: int = 5,
) -> list[RankedExpertSchema]:
    """
    Rank validated author profiles using weighted formula.

    Args:
        profiles: List of AuthorProfileSchema (already validated)
        validations: Dict of author_id → TopicValidationResult
        problem: Original user problem query
        top_k: Number of top experts to return

    Returns:
        List of RankedExpertSchema sorted by expert_score descending
    """
    logger.info(
        "[L6] Ranking %d profiles (top_k=%d)...", len(profiles), top_k,
    )

    if not profiles:
        return []

    # ── Step 1: Compute raw scores for each candidate ──
    candidates = []
    for profile in profiles:
        validation = validations.get(profile.author_id)
        scores = _compute_component_scores(profile, validation, problem)
        candidates.append({
            "profile": profile,
            "scores": scores,
            "validation": validation,
        })

    # ── Step 2: Pool normalization ──
    _normalize_scores(candidates)

    # ── Step 3: Apply weights & compute final score ──
    WEIGHTS = {
        "problem_topic_match": 0.45,
        "topic_depth": 0.25,
        "research_continuity": 0.15,
        "research_ownership": 0.10,
        "impact": 0.05,
    }

    for c in candidates:
        s = c["scores"]
        final = (
            WEIGHTS["problem_topic_match"] * s.problem_topic_match
            + WEIGHTS["topic_depth"] * s.topic_depth
            + WEIGHTS["research_continuity"] * s.research_continuity
            + WEIGHTS["research_ownership"] * s.research_ownership
            + WEIGHTS["impact"] * s.impact
        )
        c["final_score"] = round(final, 4)

    # ── Step 4: Sort with tiebreakers ──
    candidates.sort(
        key=lambda c: (
            c["final_score"],
            c["scores"].problem_topic_match,
            c["profile"].h_index,
        ),
        reverse=True,
    )

    # ── Step 5: Build ranked output ──
    ranked = []
    for rank, c in enumerate(candidates[:top_k], start=1):
        profile = c["profile"]
        scores = c["scores"]
        validation = c["validation"]

        # Find the top contributor for reasoning
        contributor, contrib_value = _find_top_contributor(scores, WEIGHTS)

        # Build reasoning
        reasoning = _build_reasoning(
            rank, c["final_score"], profile, scores, contributor, contrib_value, validation,
        )

        # Build matched_topic info
        matched_topic = None
        if validation and validation.match == "yes" and validation.matched_topics:
            best = max(validation.matched_topics, key=lambda t: t.get("count", 0))
            matched_topic = {
                "topic_name": best.get("topic_name", ""),
                "topic_count": best.get("count", 0),
            }

        # All topics
        all_topics = [
            {
                "topic_name": t.topic_name,
                "count": t.count,
                "subfield": t.subfield,
            }
            for t in profile.topics[:10]  # top 10 topics
        ]

        ranked.append(RankedExpertSchema(
            author_id=profile.author_id,
            name=profile.name,
            expert_score=round(c["final_score"] * 100, 1),  # 0-100 scale
            metrics={
                "works_count": profile.works_count,
                "citations": profile.cited_by_count,
                "h_index": profile.h_index,
            },
            matched_topic=matched_topic,
            all_topics=all_topics,
            score_breakdown=scores,
            reasoning=reasoning,
            institution=profile.institution,
            first_year=profile.first_year,
            last_year=profile.last_year,
        ))

    logger.info(
        "[L6] Ranking complete: top expert=%s (score=%.1f)",
        ranked[0].name if ranked else "N/A",
        ranked[0].expert_score if ranked else 0,
    )
    return ranked


# ──────────────────────────────────────────────
# Scoring Components
# ──────────────────────────────────────────────

def _compute_component_scores(
    profile: AuthorProfileSchema,
    validation: Optional[TopicValidationResult],
    problem: str,
) -> ComponentScores:
    """Compute all 5 scoring components for a single candidate."""

    # 1. Problem Topic Match (0.45 weight)
    # Raw count of how many distinct topics matched the user query.
    # Pool normalization will scale this relative to the best candidate.
    if validation and validation.match == "yes":
        matched_count = len(validation.matched_topics)
        problem_topic_match = float(matched_count)
    else:
        problem_topic_match = 0.0

    # 2. Topic Depth (0.25 weight)
    # What fraction of the author's total research topics overlap with the query.
    # Higher ratio = more focused expertise in the problem domain.
    if validation and validation.match == "yes":
        matched_count = len(validation.matched_topics)
        total_topics = len(profile.topics)
        topic_depth = matched_count / max(total_topics, 1)
    else:
        topic_depth = 0.0

    # 3. Research Continuity (0.15 weight)
    # How many years has the author been active?
    if profile.career_years > 0:
        research_continuity = min(1.0, profile.career_years / 30)  # 30+ years = max
    else:
        research_continuity = 0.0


# //this is something to look into it ---------------------------
    # 4. Research Ownership (0.10 weight)
    # Did the author lead the research? Based on first/last author counts
    # We don't have per-author work positions from OpenAlex directly,
    # but the evidence from the extracted works gives us signal
    ownership = 0.0
    if profile.works_count > 0:
        # Use the evidence from author_extractor
        # first + last author count vs total matched works
        pass  # Will be filled from evidence data

    # 5. Impact (0.05 weight)
    # Based on h_index and citations
    impact = 0.0
    if profile.h_index > 0:
        impact = min(1.0, profile.h_index / 80)  # h-index 80+ = max impact
    elif profile.cited_by_count > 0:
        impact = min(1.0, profile.cited_by_count / 10000)

    return ComponentScores(
        problem_topic_match=round(problem_topic_match, 4),
        topic_depth=round(topic_depth, 4),
        research_continuity=round(research_continuity, 4),
        research_ownership=0.0,  # Will be updated with evidence
        impact=round(impact, 4),
    )


def _update_ownership_scores(
    candidates: list[dict],
    author_evidence: dict[str, dict],
) -> None:
    """
    Update research_ownership scores using author extraction evidence.
    Called after pool normalization.

    Uses first/last author counts from the extraction step.
    """
    for c in candidates:
        profile = c["profile"]
        evidence = author_evidence.get(profile.author_id, {})

        positions = evidence.get("positions", [])
        total_positions = len(positions)
        if total_positions == 0:
            continue

        first_count = sum(1 for p in positions if p == "first")
        last_count = sum(1 for p in positions if p == "last")

        # Leadership score: first=1.0, last=0.8, middle=0.3
        ownership = (
            first_count * 1.0 + last_count * 0.8 + (total_positions - first_count - last_count) * 0.3
        ) / total_positions

        c["scores"].research_ownership = round(ownership, 4)


# ──────────────────────────────────────────────
# Pool Normalization
# ──────────────────────────────────────────────

def _normalize_scores(candidates: list[dict]) -> None:
    """
    Normalize each scoring component across all candidates.

    Each component is scaled so that the max value = 1.0.
    """
    if not candidates:
        return

    components = [
        "problem_topic_match",
        "topic_depth",
        "research_continuity",
        "research_ownership",
        "impact",
    ]

    for comp in components:
        values = [c["scores"].__dict__[comp] for c in candidates]
        max_val = max(values) if values else 1.0
        max_val = max(max_val, 0.001)  # avoid division by zero

        for c in candidates:
            setattr(c["scores"], comp, round(c["scores"].__dict__[comp] / max_val, 4))


# ──────────────────────────────────────────────
# Reasoning
# ──────────────────────────────────────────────

def _find_top_contributor(
    scores: ComponentScores,
    weights: dict[str, float],
) -> tuple[str, float]:
    """Find the scoring component that contributes the most to the final score."""
    contributions = {
        name: getattr(scores, name) * weight
        for name, weight in weights.items()
    }
    top = max(contributions, key=contributions.get)
    return top, contributions[top]


def _build_reasoning(
    rank: int,
    final_score: float,
    profile: AuthorProfileSchema,
    scores: ComponentScores,
    top_contributor: str,
    top_contrib_value: float,
    validation: Optional[TopicValidationResult],
) -> list[str]:
    """Generate human-readable reasoning for why this expert was ranked."""
    reasons = [
        f"Ranked #{rank} with overall score {final_score:.3f}",
        f"Strongest dimension: {_format_component_name(top_contributor)}",
    ]

    # Add matched topic info
    if validation and validation.match == "yes" and validation.matched_topics:
        for mt in validation.matched_topics[:2]:
            topic_name = mt.get("topic_name", "")
            count = mt.get("count", 0)
            if topic_name:
                reasons.append(
                    f"{count} publications directly relevant to {topic_name}"
                )

    # Add institution if available
    if profile.institution:
        reasons.append(f"Affiliated with {profile.institution}")

    # Add h-index
    if profile.h_index > 0:
        reasons.append(f"h-index: {profile.h_index}")

    return reasons


def _format_component_name(name: str) -> str:
    """Convert snake_case component name to readable format."""
    mapping = {
        "problem_topic_match": "Problem Match",
        "topic_depth": "Topic Depth",
        "research_continuity": "Research Continuity",
        "research_ownership": "Research Ownership",
        "impact": "Impact",
    }
    return mapping.get(name, name.replace("_", " ").title()
                       )
