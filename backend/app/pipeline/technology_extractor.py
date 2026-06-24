"""
Step 3: Technology / Expertise Extraction Layer

Uses LLM to extract structured technical knowledge from each document,
then attaches the extracted skills to the corresponding expert profiles.

Input:  list[ParsedDocument], list[ExpertProfile]
Output: list[EnrichedExpertProfile]

LLM extracts per document:
  - domain (e.g. "Pharmaceutical")
  - sub_domain (e.g. "Antiviral compounds")
  - skills (e.g. ["Drug formulation", "Polymorph chemistry"])
  - keywords (e.g. ["valomaciclovir", "polymorphs"])
  - research_area (e.g. "Crystallography of antiviral drugs")
"""
from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from app.pipeline.schemas import (
    EnrichedExpertProfile,
    ExpertDocumentRef,
    ExpertProfile,
    ParsedDocument,
    TechnologyExpertise,
)
from app.services.llm_client import llm_client

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# LLM System Prompt
# ──────────────────────────────────────────────

SYSTEM_PROMPT = """You are a technology extraction specialist. Your job is to analyze a patent document and extract structured information about its technical domain.

Return a JSON object with these fields:
- "domain": broad technology domain (e.g. "Pharmaceutical", "Battery Technology", "Semiconductor Manufacturing")
- "sub_domain": specific sub-domain (e.g. "Antiviral compounds", "Lithium battery cathodes")
- "skills": array of specific technical skills demonstrated (3-6 items, e.g. ["Drug formulation", "Polymorph chemistry"])
- "keywords": array of key technical terms from the document (4-8 items)
- "research_area": one-line description of the research area

Be precise and specific. Extract only what is evident from the document text."""


# ──────────────────────────────────────────────
# Extract technology from a single document
# ──────────────────────────────────────────────

def extract_technology_from_document(doc: ParsedDocument) -> TechnologyExpertise:
    """
    Use LLM to extract technology expertise from a single document.
    Falls back to empty values if LLM is unavailable.
    """
    # Build a concise text for the LLM
    text = doc.text_content
    if len(text) > 3000:
        text = text[:3000] + "..."

    user_prompt = f"""Analyze this patent document and return the requested JSON.

Title: {doc.title}

Abstract: {doc.abstract}

Document ID: {doc.document_id}"""

    try:
        result = llm_client.extract_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        return TechnologyExpertise(
            document_id=doc.document_id,
            domain=result.get("domain", ""),
            sub_domain=result.get("sub_domain", ""),
            skills=result.get("skills", []),
            keywords=result.get("keywords", []),
            research_area=result.get("research_area", ""),
        )
    except Exception as exc:
        logger.warning(
            "LLM extraction failed for doc %s: %s. Using fallback.",
            doc.document_id, exc,
        )
        # Fallback: extract from title/keywords using heuristics
        return TechnologyExpertise(
            document_id=doc.document_id,
            domain="",
            sub_domain="",
            skills=[],
            keywords=[],
            research_area="",
        )


# ──────────────────────────────────────────────
# Attach expertise to expert profiles
# ──────────────────────────────────────────────

def _normalize_name(name: str) -> str:
    return name.strip().lower()


def enrich_experts(
    documents: list[ParsedDocument],
    expert_profiles: list[ExpertProfile],
    technology_map: Optional[dict[str, TechnologyExpertise]] = None,
) -> list[EnrichedExpertProfile]:
    """
    Attach extracted technology skills to expert profiles.

    Steps:
    1. Extract technology from each document (if not pre-computed)
    2. For each expert, collect all skills from their documents
    3. Return enriched profiles
    """
    # Step 3a: Extract tech from all documents in parallel
    if technology_map is None:
        technology_map = {}
        # Run LLM calls in parallel — they're I/O-bound (network wait)
        max_workers = min(10, len(documents))  # cap to avoid rate limits
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(extract_technology_from_document, doc): doc
                for doc in documents
            }
            for future in as_completed(future_map):
                try:
                    tech = future.result()
                    technology_map[tech.document_id] = tech
                except Exception as exc:
                    doc = future_map[future]
                    logger.warning(
                        "LLM extraction failed for doc %s: %s", doc.document_id, exc,
                    )

    # Step 3b: Build a lookup doc_id → skills
    doc_skills: dict[str, list[str]] = {}
    doc_domains: dict[str, list[str]] = {}
    for doc in documents:
        tech = technology_map.get(doc.document_id)
        if tech:
            doc_skills[doc.document_id] = tech.skills
            if tech.domain:
                doc_domains[doc.document_id] = [tech.domain]
                if tech.sub_domain:
                    doc_domains[doc.document_id].append(tech.sub_domain)

    # Step 3c: Attach skills to experts
    enriched: list[EnrichedExpertProfile] = []
    for profile in expert_profiles:
        all_skills: list[str] = []
        all_domains: list[str] = []
        seen_skills: set[str] = set()

        for doc_ref in profile.documents:
            skills = doc_skills.get(doc_ref.document_id, [])
            for skill in skills:
                if skill.lower() not in seen_skills:
                    all_skills.append(skill)
                    seen_skills.add(skill.lower())

            domains = doc_domains.get(doc_ref.document_id, [])
            for domain in domains:
                if domain not in all_domains:
                    all_domains.append(domain)

        enriched.append(EnrichedExpertProfile(
            name=profile.name,
            normalized_name=profile.normalized_name,
            expertise=all_skills,
            domains=all_domains,
            documents=profile.documents,
            primary_role=profile.primary_role,
            organizations=profile.organizations,
            expertise_strength=len(profile.documents),
            role_score=_role_to_score(profile.primary_role),
        ))

    return enriched


def _role_to_score(role: str) -> float:
    """Convert role string to numeric score."""
    scores = {
        "inventor": 1.0,
        "author": 0.9,
        "applicant": 0.7,
        "assignee": 0.5,
    }
    return scores.get(role, 0.3)
