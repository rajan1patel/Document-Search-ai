"""
Layer 2: Research Retrieval

Fetches relevant research papers using X-Search API (NPL corpus only —
non-patent literature = journal papers, conference papers, preprints).

Groups evidence under a unique query_id (UUID) for in-memory tracking.
"""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Optional

from app.pipeline.schemas import ResearchWorkAuthor, ResearchWorkSchema
from app.services.xsearch_client import xsearch_client

logger = logging.getLogger(__name__)


def retrieve_works(
    query: str,
    page: int = 1,
    page_size: int = 10 ,
    api_key_override: Optional[str] = None,
) -> dict[str, Any]:
    """
    Fetch research works via X-Search API.

    Returns a dict with:
      - query_id: str (UUID for this retrieval session)
      - works: list[ResearchWorkSchema]
      - xsearch_id: Optional[str]
      - total: int (total documents found)
    """
    query_id = str(uuid.uuid4())

    logger.info("[L2][query_id=%s] Research retrieval: query='%s' | page=%d | page_size=%d", query_id, query[:80], page, page_size)



    # ── Call X-Search API (search only NPL = research papers) ──
    try:
        xsearch_response = xsearch_client.search(
            nl_query=query,
            corpora=["npl"],
            page=page,
            page_size=page_size,
            api_key_override=api_key_override,
        )
    except RuntimeError as exc:
        logger.error("[L2] X-Search failed: %s", exc)
        return {"query_id": query_id, "works": [], "xsearch_id": None, "total": 0}





    logger.info(xsearch_response)
    xsearch_id = xsearch_client.get_xsearch_id(xsearch_response)
    raw_docs = xsearch_client.extract_hits(xsearch_response)

    if not raw_docs:
        logger.warning("[L2] X-Search returned no hits for query: %s", query[:80])
        return {"query_id": query_id, "works": [], "xsearch_id": xsearch_id, "total": 0}

    logger.info(
        "[L2] X-Search returned %d NPL (research paper) docs (xsearch_id=%s)",
        len(raw_docs), xsearch_id,
    )

    # ── Log raw X-Search response for validation ──
    logger.info("[L2] RAW X-SEARCH RESPONSE: %s", json.dumps(xsearch_response, indent=2, default=str))

    # ── Parse raw docs into ResearchWorkSchema ──
    works = _parse_xsearch_works(raw_docs)
    logger.info("[L2] Parsed %d works from X-Search response", len(works))

    return {
        "query_id": query_id,
        "works": works,
        "xsearch_id": xsearch_id,
        "total": len(works),
    }


def _parse_xsearch_works(raw_docs: list[dict]) -> list[ResearchWorkSchema]:
    """
    Parse raw X-Search NPL response into ResearchWorkSchema.

    Actual NPL response format (verified 2026-06-25):
      {
        "_id": "W2304077091",
        "_source": {
          "id": "W2304077091",
          "display_name": "...",              ← title
          "authorships": [{                   ← primary author source
            "author": {"id": "https://openalex.org/A...", "display_name": "..."},
            "author_position": null,          ← null! inferred from index
            "is_corresponding": true/false,
            "institutions": [{"display_name": "..."}]
          }],
          "cited_by_count": 0,
          "doi": "https://doi.org/...",
          "publication_date": "2014-04-01",
          "abstract": "...",
          "type": "article"
        }
      }

    Only extracts: work_id, title, authors (id + name + position from index).
    All enrichment data (h-index, topics, institution) comes from OpenAlex.
    """
    works = []

    for raw in raw_docs:
        source = raw.get("_source") or raw.get("source") or {}
        doc_id = raw.get("_id", source.get("id", ""))

        # Actual field name in NPL response is "display_name", not "title"
        title = source.get("display_name", raw.get("display_name", ""))

        # Extract authors from 'authorships' array (primary NPL format)
        authors = _extract_authors_from_npl(source)

        if not authors:
            # Fallback: 'authors' field (older format with null positions)
            authors = _extract_authors_fallback(source)

        work = ResearchWorkSchema(
            work_id=doc_id,
            title=title,
            authors=authors,
        )
        works.append(work)

    return works


def _extract_authors_from_npl(source: dict) -> list[ResearchWorkAuthor]:
    """
    Extract authors from NPL 'authorships' array.

    Actual format:
      "authorships": [{
        "author": {"id": "https://openalex.org/A...", "display_name": "..."},
        "author_position": null,     ← always null in X-Search NPL
        "is_corresponding": true,
        "institutions": [{"display_name": "University of Calgary"}],
        "raw_author_name": "..."
      }]

    Since author_position is null, we infer from array index:
      - index 0 → "first"
      - last index → "last"
      - everything else → "middle"
    """
    authors: list[ResearchWorkAuthor] = []
    authorships = source.get("authorships", [])

    if not authorships or not isinstance(authorships, list):
        return authors

    total = len(authorships)
    for i, entry in enumerate(authorships):
        if not isinstance(entry, dict):
            continue

        author_obj = entry.get("author") or {}
        author_id = author_obj.get("id", "")
        author_name = author_obj.get("display_name", entry.get("raw_author_name", ""))

        if not author_id and not author_name:
            continue

        # Infer position from index (X-Search returns null for author_position)
        if i == 0:
            position = "first"
        elif i == total - 1:
            position = "last"
        else:
            position = "middle"

        authors.append(ResearchWorkAuthor(
            author_id=author_id,
            name=author_name,
            position=position,
        ))

    return authors


def _extract_authors_fallback(source: dict) -> list[ResearchWorkAuthor]:
    """
    Fallback: extract from 'authors' array (older format).

    Actual format:
      "authors": [{
        "id": "https://openalex.org/A...",
        "display_name": "...",
        "author_position": null    ← also null
      }]
    """
    authors: list[ResearchWorkAuthor] = []
    raw_authors = source.get("authors", [])

    if not raw_authors or not isinstance(raw_authors, list):
        return authors

    total = len(raw_authors)
    for i, a in enumerate(raw_authors):
        if not isinstance(a, dict):
            continue

        author_id = a.get("id", "")
        author_name = a.get("display_name", "")

        if not author_id and not author_name:
            continue

        # Infer position from index
        position = "first" if i == 0 else ("last" if i == total - 1 else "middle")

        authors.append(ResearchWorkAuthor(
            author_id=author_id,
            name=author_name,
            position=position,
        ))

    return authors
