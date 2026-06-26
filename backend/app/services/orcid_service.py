"""
ORCID Public Profile Enrichment Service.

Fetches public contact data from the ORCID API for ranked experts.

Flow:
  1. Receive normalized ORCID iD (e.g. "0000-0002-2192-9543")
  2. Call GET https://pub.orcid.org/v3.0/{orcid_id}/person
  3. Extract ONLY public visibility emails and researcher URLs
  4. Return structured contact list

Rules:
  - Only public data is extracted
  - No guessing LinkedIn, Google Scholar, or other profiles
  - No web scraping beyond the ORCID API
  - All failures are silently handled — never affects expert ranking
"""
from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.pipeline.schemas import ContactEntry

logger = logging.getLogger(__name__)

ORCID_API_BASE = "https://pub.orcid.org/v3.0"
ORCID_API_TIMEOUT = 15.0  # seconds


def fetch_orcid_contacts(orcid_id: str) -> list[ContactEntry]:
    """
    Fetch public contact info from ORCID for a given ORCID iD.

    Args:
        orcid_id: Normalized ORCID iD, e.g. "0000-0002-2192-9543"

    Returns:
        List of ContactEntry with public emails and URLs.
        Empty list if ORCID is invalid, unreachable, or has no public data.
    """
    if not orcid_id or not _is_valid_orcid(orcid_id):
        logger.warning("[ORCID] Skipping invalid ORCID: '%s'", orcid_id)
        return []

    url = f"{ORCID_API_BASE}/{orcid_id}/person"
    headers = {"Accept": "application/json"}

    logger.info("[ORCID] Fetching public profile: %s", url)

    try:
        with httpx.Client(timeout=ORCID_API_TIMEOUT) as client:
            resp = client.get(url, headers=headers)

        if resp.status_code == 404:
            logger.warning("[ORCID] Profile not found (404): %s", orcid_id)
            return []
        if resp.status_code == 403:
            logger.warning("[ORCID] Access denied (403): %s", orcid_id)
            return []
        if resp.status_code == 410:
            logger.warning("[ORCID] Profile deactivated (410): %s", orcid_id)
            return []

        resp.raise_for_status()
        data = resp.json()

    except httpx.TimeoutException:
        logger.warning("[ORCID] Timeout fetching: %s", orcid_id)
        return []
    except httpx.HTTPStatusError as exc:
        logger.warning("[ORCID] HTTP error for %s: %s", orcid_id, exc)
        return []
    except Exception as exc:
        logger.warning("[ORCID] Unexpected error for %s: %s", orcid_id, exc)
        return []

    # ── Parse the response ──────────────────────
    contacts: list[ContactEntry] = []

    # Extract public emails
    try:
        emails_section = data.get("emails", {})
        email_list = emails_section.get("email", [])
        if isinstance(email_list, dict):
            email_list = [email_list]  # Single email returned as dict
        for entry in email_list:
            if isinstance(entry, dict) and entry.get("visibility") == "public":
                email_val = (entry.get("email") or "").strip()
                if email_val:
                    contacts.append(ContactEntry(
                        type="email",
                        value=email_val,
                        label="",
                        source="orcid",
                    ))
    except Exception as exc:
        logger.warning("[ORCID] Error parsing emails for %s: %s", orcid_id, exc)

    # Extract public researcher URLs
    try:
        urls_section = data.get("researcher-urls", {})
        url_list = urls_section.get("researcher-url", [])
        if isinstance(url_list, dict):
            url_list = [url_list]  # Single URL returned as dict
        for entry in url_list:
            if isinstance(entry, dict) and entry.get("visibility") == "public":
                url_val = (entry.get("url", {}) or {}).get("value", "").strip()
                url_name = (entry.get("url-name") or "").strip()
                if url_val:
                    contacts.append(ContactEntry(
                        type="url",
                        value=url_val,
                        label=url_name,
                        source="orcid",
                    ))
    except Exception as exc:
        logger.warning("[ORCID] Error parsing URLs for %s: %s", orcid_id, exc)

    logger.info(
        "[ORCID] %s: extracted %d contact(s) (%d email(s), %d URL(s))",
        orcid_id,
        len(contacts),
        sum(1 for c in contacts if c.type == "email"),
        sum(1 for c in contacts if c.type == "url"),
    )
    return contacts


def _is_valid_orcid(orcid_id: str) -> bool:
    """
    Basic validation of ORCID iD format.

    ORCID iDs are 16-digit numbers grouped in 4 blocks of 4,
    separated by hyphens: XXXX-XXXX-XXXX-XXXX
    The last digit is a checksum (0-9 or X).
    """
    import re
    pattern = r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$"
    return bool(re.match(pattern, orcid_id.strip()))
