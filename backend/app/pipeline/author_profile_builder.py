"""
Layer 4: Author Profile Builder

Enriches extracted authors with detailed profiles from OpenAlex.

For each author:
  1. Fetch OpenAlex profile (works_count, h_index, topics, etc.)
  2. Attach matched work evidence from the retrieval step
  3. Compute topic overlap with the user's problem

Uses OpenAlexProvider to fetch author details with ThreadPoolExecutor
for concurrent API calls.
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from app.providers.openalex import openalex_provider
from app.pipeline.schemas import AuthorEvidence, AuthorProfileSchema, AuthorTopic

logger = logging.getLogger(__name__)


def build_author_profile(
    evidence: AuthorEvidence,
    problem_domain: str = "",
) -> Optional[AuthorProfileSchema]:
    """
    Build a full author profile by fetching OpenAlex data.

    Args:
        evidence: AuthorEvidence extracted from works
        problem_domain: The user's problem domain (for topic matching)

    Returns:
        AuthorProfileSchema with OpenAlex data + evidence, or None if fetch fails
    """
    logger.info(
        "[L4] Building profile: author=%s | id=%s",
        evidence.name, evidence.author_id,
    )

    # Fetch OpenAlex profile
    author_info = openalex_provider.get_author(evidence.author_id)

    if author_info is None:
        logger.warning(
            "[L4] OpenAlex fetch failed for %s (%s). Building minimal profile.",
            evidence.name, evidence.author_id,
        )
        # Build a minimal profile from evidence alone
        return AuthorProfileSchema(
            author_id=evidence.author_id,
            name=evidence.name,
            works_count=len(evidence.matched_works),
            cited_by_count=evidence.total_citations,
        )

    # Convert topics to AuthorTopic format
    topics = []
    for t in author_info.topics:
        topic = AuthorTopic(
            topic_name=t.get("display_name", ""),
            count=t.get("count", 0),
            subfield=t.get("subfield", ""),
        )
        topics.append(topic)

    # Extract subfields
    subfields = list(set(
        t.subfield for t in topics if t.subfield
    ))

    profile = AuthorProfileSchema(
        author_id=author_info.author_id,
        name=author_info.name,
        works_count=author_info.works_count,
        cited_by_count=author_info.cited_by_count,
        h_index=author_info.h_index,
        i10_index=author_info.i10_index,
        counts_by_year=author_info.counts_by_year,
        topics=topics,
        subfields=subfields,
        institution=author_info.institution,
        career_years=author_info.career_years,
        first_year=author_info.first_year,
        last_year=author_info.last_year,
        orcid=author_info.orcid,
    )

    logger.info(
        "[L4] Profile built: %s | h_index=%d | topics=%d | institution=%s",
        profile.name, profile.h_index, len(profile.topics), profile.institution,
    )
    return profile


def build_profiles(
    authors: dict[str, AuthorEvidence],
    problem_domain: str = "",
) -> list[AuthorProfileSchema]:
    """
    Build profiles for ALL extracted authors.

    Args:
        authors: Dict of author_id → AuthorEvidence
        problem_domain: User's problem description for topic matching

    Returns:
        List of AuthorProfileSchema with OpenAlex enrichment
    """
    author_list = list(authors.values())
    total = len(author_list)

    logger.info(
        "[L4] Building profiles for %d authors (concurrent, max_workers=5)...",
        len(author_list),
    )

    profiles = []
    failed = 0
    max_workers = 5  # limit concurrent OpenAlex calls

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_map = {
            executor.submit(build_author_profile, evidence, problem_domain): evidence
            for evidence in author_list
        }

        # Collect results as they complete
        for i, future in enumerate(as_completed(future_map), start=1):
            try:
                profile = future.result()
                if profile:
                    profiles.append(profile)
                else:
                    failed += 1
            except Exception as exc:
                evidence = future_map[future]
                logger.warning(
                    "[L4] Profile failed for %s: %s", evidence.name, exc,
                )
                failed += 1

            if i % 10 == 0 or i == len(author_list):
                logger.info(
                    "[L4] Progress: %d/%d profiles processed", i, len(author_list),
                )

    logger.info(
        "[L4] Done: %d profiles built, %d failed (concurrent)",
        len(profiles), failed,
    )
    return profiles
