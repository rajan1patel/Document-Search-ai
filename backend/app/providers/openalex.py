"""
OpenAlex Research Provider.

Implements ResearchProvider interface to fetch research works and
author profiles from the OpenAlex API (https://api.openalex.org).

API key is sent as ?api_key= param (free tier, 100k req/month).
"""
from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.core.config import settings
from app.providers.base import AuthorInfo, ResearchProvider, ResearchWork, SearchResults

logger = logging.getLogger(__name__)

OPENALEX_BASE = "https://api.openalex.org"
TIMEOUT = 30.0  # seconds


class OpenAlexProvider(ResearchProvider):
    """Provider for OpenAlex research data."""

    def __init__(self):
        self.api_key: str = settings.OPENALEX_APIKEY or ""
        self._http = httpx.Client(timeout=TIMEOUT)

    @staticmethod
    def _extract_id(author_id: str) -> str:
        """
        Extract bare OpenAlex author ID from various input formats.

        Handles:
          - "https://openalex.org/A5034008951"   ← X-Search returns this
          - "https://api.openalex.org/authors/A5034008951"
          - "A5034008951"  (bare ID)
        """
        aid = author_id.strip()
        # Handle: https://openalex.org/A... (X-Search format)
        if "/A" in aid and "openalex.org" in aid:
            return aid.rstrip("/").split("/")[-1]
        # Handle: https://api.openalex.org/authors/A... (API format)
        if "/authors/" in aid:
            return aid.split("/authors/")[-1].split("?")[0].split("/")[0]
        return aid

    def _url(self, path: str) -> str:
        """Build URL with API key if configured."""
        url = f"{OPENALEX_BASE}{path}"
        if self.api_key:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}api_key={self.api_key}"
        return url

    # ──────────────────────────────────────────
    # Search Works
    # ──────────────────────────────────────────

    def search_works(self, query: str, limit: int = 20) -> SearchResults:
        """
        Search OpenAlex works by title/abstract.

        Returns up to `limit` works with author data.
        """
        url = self._url(f"/works?search={query}&per_page={limit}&select=id,title,authorships,publication_year,cited_by_count,doi,primary_location,concepts,abstract_inverted_index")

        logger.info(
            "OpenAlex search_works: query='%s' | limit=%d | url=%s",
            query[:60], limit, url,
        )

        try:
            resp = self._http.get(url)
            resp.raise_for_status()
            data = resp.json()

            results = data.get("results", [])
            total = data.get("meta", {}).get("count", 0)
            logger.info(
                "  → OpenAlex found %d total works, returning %d",
                total, len(results),
            )

            works = []
            for r in results:
                work = self._parse_work(r)
                works.append(work)

            return SearchResults(query=query, total=total, works=works)

        except httpx.HTTPStatusError as exc:
            logger.error("OpenAlex HTTP error: %s — %s", exc, exc.response.text[:300])
            return SearchResults(query=query, total=0, works=[])
        except Exception as exc:
            logger.error("OpenAlex search failed: %s", exc, exc_info=True)
            return SearchResults(query=query, total=0, works=[])

    # ──────────────────────────────────────────
    # Get Author
    # ──────────────────────────────────────────

    def get_author(self, author_id: str) -> Optional[AuthorInfo]:
        """
        Fetch detailed author profile from OpenAlex.
        Handles multiple input formats via _extract_id().
        """
        aid = self._extract_id(author_id)

        url = self._url(f"/authors/{aid}")

        logger.info("OpenAlex get_author: author_id=%s | url=%s", aid, url)

        try:
            resp = self._http.get(url)
            resp.raise_for_status()
            data = resp.json()

            # Parse topics from the 'topics' array (has count + subfield data)
            topics = []
            for t in data.get("topics", []):
                topics.append({
                    "display_name": t.get("display_name", ""),
                    "count": t.get("count", 0),
                    "subfield": t.get("subfield", {}).get("display_name", ""),
                })

            # counts_by_year for activity analysis
            counts_by_year = {}
            for entry in data.get("counts_by_year", []):
                year = entry.get("year")
                count = entry.get("works_count", 0)
                if year:
                    counts_by_year[str(year)] = count

            # Institution – last_known_institutions can be null or []
            institution = ""
            last_inst = data.get("last_known_institutions")
            if last_inst and isinstance(last_inst, list) and len(last_inst) > 0:
                institution = last_inst[0].get("display_name", "")

            # Career years – compute from counts_by_year (no first_year/last_year field)
            years = [int(y) for y in counts_by_year.keys() if y.isdigit()]
            career_years = 0
            first_year = 0
            last_year = 0
            if years:
                first_year = min(years)
                last_year = max(years)
                career_years = last_year - first_year

            author = AuthorInfo(
                author_id=aid,
                name=data.get("display_name", ""),
                works_count=data.get("works_count", 0),
                cited_by_count=data.get("cited_by_count", 0),
                h_index=data.get("summary_stats", {}).get("h_index", 0),
                i10_index=data.get("summary_stats", {}).get("i10_index", 0),
                counts_by_year=counts_by_year,
                topics=topics,
                institution=institution,
                career_years=career_years,
                first_year=first_year,
                last_year=last_year,
            )

            logger.info(
                "  → Author: %s | works=%d | h_index=%d | topics=%d | institution=%s",
                author.name, author.works_count, author.h_index,
                len(topics), institution,
            )
            return author

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                logger.warning("OpenAlex author not found: %s", aid)
            else:
                logger.error("OpenAlex author HTTP error: %s — %s", exc, exc.response.text[:300])
            return None
        except Exception as exc:
            logger.error("OpenAlex get_author failed for %s: %s", aid, exc, exc_info=True)
            return None

    # ──────────────────────────────────────────
    # Get Author Works
    # ──────────────────────────────────────────

    def get_author_works(self, author_id: str, limit: int = 50) -> list[ResearchWork]:
        """
        Fetch recent works by an author.
        Used for research continuity and depth analysis.
        """
        aid = self._extract_id(author_id)

        url = self._url(f"/works?filter=authorships.author.id:{aid}&per_page={limit}&sort=publication_year:desc&select=id,title,authorships,publication_year,cited_by_count,doi,concepts")

        logger.info("OpenAlex get_author_works: author_id=%s | limit=%d", aid, limit)

        try:
            resp = self._http.get(url)
            resp.raise_for_status()
            data = resp.json()

            works = []
            for r in data.get("results", []):
                work = self._parse_work(r)
                works.append(work)

            logger.info("  → %d works returned for author %s", len(works), aid)
            return works

        except httpx.HTTPStatusError as exc:
            logger.error("OpenAlex author works HTTP error: %s", exc)
            return []
        except Exception as exc:
            logger.error("OpenAlex get_author_works failed: %s", exc, exc_info=True)
            return []

    # ──────────────────────────────────────────
    # Internal: Parse work from OpenAlex JSON
    # ──────────────────────────────────────────

    def _parse_work(self, raw: dict) -> ResearchWork:
        """Parse an OpenAlex work JSON into a ResearchWork dataclass."""
        work_id = raw.get("id", "")
        title = raw.get("title", "")
        year = raw.get("publication_year")
        citations = raw.get("cited_by_count", 0)
        doi = raw.get("doi", "")

        # Source / venue
        source = ""
        primary = raw.get("primary_location")
        if isinstance(primary, dict):
            source_obj = primary.get("source")
            if isinstance(source_obj, dict):
                source = source_obj.get("display_name", "")

        # Topics from concepts
        topics = []
        for concept in raw.get("concepts", []):
            if concept.get("level", 99) >= 1:
                topics.append(concept.get("display_name", ""))

        # Extract abstract from inverted index
        abstract = ""
        inv_index = raw.get("abstract_inverted_index")
        if inv_index:
            # Reconstruct abstract from inverted index
            word_positions = []
            for word, positions in inv_index.items():
                for pos in positions:
                    word_positions.append((pos, word))
            word_positions.sort()
            abstract = " ".join(w for _, w in word_positions)

        # Authors
        authors = []
        authorships = raw.get("authorships", [])
        for i, a in enumerate(authorships):
            author_obj = a.get("author", {})
            author_id = author_obj.get("id", "")
            author_name = author_obj.get("display_name", "")

            # Determine position
            position = a.get("author_position", "")
            if not position:
                if i == 0:
                    position = "first"
                elif i == len(authorships) - 1:
                    position = "last"
                else:
                    position = "middle"

            # Institution
            inst = ""
            insts = a.get("institutions", [])
            if insts:
                inst = insts[0].get("display_name", "")

            authors.append({
                "author_id": author_id,
                "name": author_name,
                "position": position,
                "institution": inst,
            })

        return ResearchWork(
            work_id=work_id,
            title=title,
            abstract=abstract,
            year=year,
            citations=citations,
            doi=doi,
            source=source,
            topics=topics,
            authors=authors,
            raw=raw,
        )


# Singleton
openalex_provider = OpenAlexProvider()
