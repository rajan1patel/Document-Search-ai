"""
Layer 2b: Paper Evidence Store

In-memory per-query evidence storage for research works.

Design:
  - Created per query_id, stored in a dict keyed by query_id
  - NOT persisted to any database
  - Supports: store_works(), get_by_query(), get_author_evidence()
  - Deduplicates works within the same query_id

This is a lightweight in-memory store for the MVP pipeline.
"""
from __future__ import annotations

import logging
from typing import Optional

from app.pipeline.schemas import PaperEvidenceRecord

logger = logging.getLogger(__name__)


# ── In-memory store (module-level dict, per query_id) ──
_evidence_store: dict[str, list[PaperEvidenceRecord]] = {}


class PaperEvidenceStore:
    """Per-query in-memory evidence store."""

    @staticmethod
    def store_works(query_id: str, records: list[PaperEvidenceRecord]) -> int:
        """
        Store evidence records for a query_id.
        Deduplicates by work_id within the same query_id.
        Returns the total count after dedup.
        """
        if query_id not in _evidence_store:
            _evidence_store[query_id] = []

        existing_ids = {r.work_id for r in _evidence_store[query_id]}
        added = 0
        for rec in records:
            if rec.work_id not in existing_ids:
                _evidence_store[query_id].append(rec)
                existing_ids.add(rec.work_id)
                added += 1

        logger.info(
            "[EvidenceStore] query_id=%s: stored %d new records (%d total, %d deduped)",
            query_id, added, len(_evidence_store[query_id]),
            len(records) - added,
        )
        return len(_evidence_store[query_id])

    @staticmethod
    def get_by_query(query_id: str) -> list[PaperEvidenceRecord]:
        """Get all evidence records for a query_id."""
        records = _evidence_store.get(query_id, [])
        logger.info(
            "[EvidenceStore] get_by_query: query_id=%s → %d records",
            query_id, len(records),
        )
        return records

    @staticmethod
    def get_author_evidence(
        query_id: str, author_id: str,
    ) -> list[PaperEvidenceRecord]:
        """
        Get evidence records where a specific author appears.
        Useful for per-author evidence aggregation.
        """
        records = _evidence_store.get(query_id, [])
        matched = [r for r in records if author_id in r.author_ids]
        logger.info(
            "[EvidenceStore] get_author_evidence: author_id=%s → %d records",
            author_id, len(matched),
        )
        return matched

    @staticmethod
    def get_all_authors(query_id: str) -> dict[str, dict]:
        """
        Get all unique authors across all evidence records for a query_id.
        Returns {author_id: {name, positions, work_count}}.
        """
        records = _evidence_store.get(query_id, [])
        authors: dict[str, dict] = {}

        for rec in records:
            for i, aid in enumerate(rec.author_ids):
                if aid not in authors:
                    authors[aid] = {
                        "name": rec.author_names[i] if i < len(rec.author_names) else aid,
                        "positions": [],
                        "work_count": 0,
                    }
                authors[aid]["positions"].append(
                    rec.author_positions.get(aid, "middle"),
                )
                authors[aid]["work_count"] += 1

        logger.info(
            "[EvidenceStore] get_all_authors: query_id=%s → %d unique authors",
            query_id, len(authors),
        )
        return authors

    @staticmethod
    def clear_query(query_id: str) -> None:
        """Remove evidence for a specific query_id."""
        if query_id in _evidence_store:
            del _evidence_store[query_id]
            logger.info(
                "[EvidenceStore] Cleared evidence for query_id=%s", query_id,
            )

    @staticmethod
    def clear_all() -> None:
        """Clear ALL evidence (for testing / cleanup)."""
        _evidence_store.clear()
        logger.info("[EvidenceStore] Cleared all evidence")


# Helper: Build evidence records from ResearchWorkSchema list

def build_evidence_records(
    works: list,
    query_id: str,
) -> list[PaperEvidenceRecord]:
    """
    Convert ResearchWorkSchema objects into PaperEvidenceRecord for storage.

    Only extracts: work_id, title, author_ids, author_names, author_positions.
    All enrichment data comes from OpenAlex (not from evidence store).
    """
    records = []
    for w in works:
        if hasattr(w, "work_id"):
            # ResearchWorkSchema object
            record = PaperEvidenceRecord(
                work_id=w.work_id,
                title=w.title,
                author_ids=[a.author_id for a in w.authors],
                author_names=[a.name for a in w.authors],
                author_positions={
                    a.author_id: a.position for a in w.authors
                },
            )
        else:
            # Dict fallback
            authors = w.get("authors", [])
            record = PaperEvidenceRecord(
                work_id=w.get("work_id", ""),
                title=w.get("title", ""),
                author_ids=[a.get("author_id", "") for a in authors],
                author_names=[a.get("name", "") for a in authors],
                author_positions={
                    a.get("author_id", ""): a.get("position", "middle")
                    for a in authors
                },
            )
        records.append(record)

    return records
