"""
Step 6: Contact Enrichment Layer (placeholder)

For now, only attaches the real organization name from patent assignee data.
Email and profile_url require a real provider integration (RocketReach,
Lusha, LinkedIn API, etc.) and are left as null.

Input:  list[RankedExpert]
Output: list[RankedExpert]  (with contact populated only from real data)
"""
from __future__ import annotations

import logging
from typing import Optional

from app.pipeline.schemas import RankedExpert

logger = logging.getLogger(__name__)


def enrich_contacts(
    ranked_experts: list[RankedExpert],
    organizations: Optional[dict[str, list[str]]] = None,
) -> list[RankedExpert]:
    """
    Attach real organization data from patents to expert contacts.

    Email and profile_url are null until a real provider is integrated.
    """
    for expert in ranked_experts:
        org = None
        if organizations and expert.name in organizations:
            orgs = organizations[expert.name]
            if orgs:
                org = orgs[0]

        expert.contact = {"organization": org} if org else None

    return ranked_experts
