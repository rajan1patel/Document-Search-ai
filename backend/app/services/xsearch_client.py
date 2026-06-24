"""
X-Search API Client

Calls the external Landscapes / X-Search API to fetch patent documents
for a given natural-language query.

Endpoint:
  POST /patent_search/xsearch
  Header: X-Gravitee-Api-Key
  Body: { nl_query: str, page: int, page_size: int }

Response:
  {
    xsearch_id: str,
    patent: { hits: [ ... ] }
  }
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

XSEARCH_TIMEOUT = 60.0  # seconds


class XSearchClient:
    """Client for the external patent search API."""

    def __init__(self):
        self.base_url: str = settings.XSEARCH_BASE_URL.rstrip("/")
        self.api_key: str = settings.XSEARCH_API_KEY

    # ──────────────────────────────────────────
    # Public
    # ──────────────────────────────────────────

    def search(
        self,
        nl_query: str,
        page: int = 1,
        page_size: int = 20,
        api_key_override: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Call the X-Search API and return the full JSON response.

        Returns:
            {
                "xsearch_id": "...",
                "patent": { "hits": [ ... ] }
            }

        Raises:
            RuntimeError: if no API key is configured or the request fails.
        """
        api_key = api_key_override or self.api_key
        if not api_key:
            raise RuntimeError(
                "XSEARCH_API_KEY is not set. "
                "Configure it in the .env file or pass xsearch_api_key in the request."
            )

        url = f"{self.base_url}/xsearch"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Gravitee-Api-Key": api_key,
        }
        payload = {
            "nl_query": nl_query,
            "page": page,
            "page_size": page_size,
        }

        logger.info(
            "X-Search request: url=%s | query='%s' | page=%d | page_size=%d",
            url, nl_query[:80], page, page_size,
        )

        try:
            with httpx.Client(timeout=XSEARCH_TIMEOUT) as client:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                hit_count = self._count_hits(data)
                logger.info(
                    "X-Search response: xsearch_id=%s | hits=%d",
                    data.get("xsearch_id", "?"), hit_count,
                )
                return data
        except httpx.HTTPStatusError as exc:
            logger.error(
                "X-Search HTTP error: %s — %s",
                exc, exc.response.text[:500],
            )
            raise RuntimeError(
                f"X-Search API returned {exc.response.status_code}: "
                f"{exc.response.text[:200]}"
            ) from exc
        except httpx.RequestError as exc:
            logger.error("X-Search request failed: %s", exc)
            raise RuntimeError(
                f"Could not reach X-Search API at {url}: {exc}"
            ) from exc

    # ──────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────

    def extract_hits(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Extract the list of patent documents (hits) from the X-Search response.

        Handles multiple possible response shapes:
          { patent: { hits: [...] } }
          { hits: [...] }
          or a top-level list
        """
        # Try { patent: { hits: [...] } }
        patent = data.get("patent")
        if isinstance(patent, dict):
            hits = patent.get("hits")
            if isinstance(hits, list):
                return hits

        # Try { hits: [...] }
        hits = data.get("hits")
        if isinstance(hits, list):
            return hits

        # If the whole response is a list
        if isinstance(data, list):
            return data

        logger.warning("Unexpected X-Search response shape: %s", list(data.keys()))
        return []

    def get_xsearch_id(self, data: dict[str, Any]) -> Optional[str]:
        """Extract the xsearch_id from the response."""
        return data.get("xsearch_id")

    @staticmethod
    def _count_hits(data: dict[str, Any]) -> int:
        """Count hits without extracting them (for logging)."""
        patent = data.get("patent")
        if isinstance(patent, dict):
            hits = patent.get("hits")
            if isinstance(hits, list):
                return len(hits)
        hits = data.get("hits")
        if isinstance(hits, list):
            return len(hits)
        return 0


# Singleton
xsearch_client = XSearchClient()
