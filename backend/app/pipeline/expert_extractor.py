"""
Step 2: Expert Extraction Layer

Extracts people (inventors, applicants, assignees) from parsed documents
and merges duplicate experts across documents.

Input:  list[ParsedDocument]
Output: list[ExpertProfile]  (deduplicated, with role priority)

Role priority (highest first):
  inventor (1.0) > author (0.9) > applicant (0.7) > assignee (0.5)
"""
from __future__ import annotations

from app.pipeline.schemas import ExpertDocumentRef, ExpertProfile, ParsedDocument


# ──────────────────────────────────────────────
# Role definitions
# ──────────────────────────────────────────────

ROLE_PRIORITY: dict[str, float] = {
    "inventor": 1.0,
    "author": 0.9,
    "applicant": 0.7,
    "assignee": 0.5,
}


def _normalize_name(name: str) -> str:
    """Normalize a person's name for deduplication."""
    return name.strip().lower()


def _better_role(current: str, candidate: str) -> str:
    """Return the role with higher priority."""
    if ROLE_PRIORITY.get(candidate, 0) > ROLE_PRIORITY.get(current, 0):
        return candidate
    return current


# ──────────────────────────────────────────────
# Extraction
# ──────────────────────────────────────────────

def extract_experts(documents: list[ParsedDocument]) -> list[ExpertProfile]:
    """
    Extract expert profiles from parsed documents.

    1. Iterate over all documents
    2. For each person found (inventor, applicant, assignee), create/update profile
    3. Deduplicate by normalized name
    4. Assign highest-priority role
    """
    profiles: dict[str, ExpertProfile] = {}

    for doc in documents:
        doc_id = doc.document_id
        title = doc.title

        # --- Inventors (highest priority) ---
        for name in doc.inventors:
            normalized = _normalize_name(name)
            if normalized not in profiles:
                profiles[normalized] = ExpertProfile(
                    name=name,
                    normalized_name=normalized,
                )
            profile = profiles[normalized]
            profile.roles.append("inventor")
            profile.primary_role = _better_role(profile.primary_role, "inventor")
            profile.documents.append(
                ExpertDocumentRef(document_id=doc_id, title=title, role="inventor")
            )

        # --- Applicants ---
        for name in doc.applicants:
            normalized = _normalize_name(name)
            if normalized not in profiles:
                profiles[normalized] = ExpertProfile(
                    name=name,
                    normalized_name=normalized,
                )
            profile = profiles[normalized]
            profile.roles.append("applicant")
            profile.primary_role = _better_role(profile.primary_role, "applicant")
            profile.documents.append(
                ExpertDocumentRef(document_id=doc_id, title=title, role="applicant")
            )

        # --- Assignees (lowest priority) ---
        for name in doc.assignees:
            normalized = _normalize_name(name)
            if normalized not in profiles:
                profiles[normalized] = ExpertProfile(
                    name=name,
                    normalized_name=normalized,
                )
            profile = profiles[normalized]
            profile.roles.append("assignee")
            profile.primary_role = _better_role(profile.primary_role, "assignee")
            profile.documents.append(
                ExpertDocumentRef(document_id=doc_id, title=title, role="assignee")
            )

    return list(profiles.values())
