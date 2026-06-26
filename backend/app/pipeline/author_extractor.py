"""
Layer 3: Author Extraction

Extract ALL authors from research works (or paper evidence records).

Key rule from the plan:
  "Do not rank authors from the paper. Do not remove authors early.
   If a paper has 10 authors, all 10 enter the author pool."

Extracts:
  - author_id (unique identity)
  - name
  - matched works (work IDs, titles)
  - Position tracking (first/last/middle counts)
  - Total citations across matched works
  - Leadership score: (first*1.0 + last*0.8 + middle*0.3) / total_works
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.pipeline.schemas import AuthorEvidence, PaperEvidenceRecord

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Result of the author extraction process."""
    authors: dict[str, AuthorEvidence] = field(default_factory=dict)
    total_works: int = 0
    total_authors: int = 0


def extract_authors_from_works(works: list) -> ExtractionResult:
    """
    Extract ALL authors from a list of ResearchWorkSchema objects.

    This is the primary extraction path — called directly after retrieval.
    No pre-filtering: every author from every work enters the pool.
    """
    authors: dict[str, AuthorEvidence] = {}
    total_works = len(works)

    logger.info(
        "[L3] Extracting authors from %d works...", total_works,
    )

    for w in works:
        work_id = w.work_id if hasattr(w, "work_id") else w.get("work_id", "")
        title = w.title if hasattr(w, "title") else w.get("title", "")
        raw_authors = w.authors if hasattr(w, "authors") else w.get("authors", [])

        for a in raw_authors:
            author_id = a.author_id if hasattr(a, "author_id") else a.get("author_id", "")
            name = a.name if hasattr(a, "name") else a.get("name", "")

            # Skip authors with no OpenAlex ID — can't enrich their profile
            if not author_id:
                continue

            if author_id not in authors:
                authors[author_id] = AuthorEvidence(
                    author_id=author_id,
                    name=name,
                )

            entry = authors[author_id]
            position = a.position if hasattr(a, "position") else a.get("position", "middle")

            if work_id not in entry.matched_works:
                entry.matched_works.append(work_id)
                entry.matched_titles.append(title)

            entry.positions.append(position)
            if position == "first":
                entry.first_author_count += 1
            elif position == "last":
                entry.last_author_count += 1
            else:
                entry.middle_author_count += 1

    total_authors = len(authors)
    logger.info(
        "[L3] Extracted %d unique authors from %d works",
        total_authors, total_works,
    )

    return ExtractionResult(
        authors=authors,
        total_works=total_works,
        total_authors=total_authors,
    )


def extract_authors_from_evidence(
    records: list[PaperEvidenceRecord],
) -> ExtractionResult:
    """
    Alternative extraction path: from stored PaperEvidenceRecord objects.
    Useful when re-processing stored evidence.
    """
    authors: dict[str, AuthorEvidence] = {}
    total_works = len(records)

    logger.info(
        "[L3] Extracting authors from %d evidence records...", total_works,
    )

    for rec in records:
        for i, aid in enumerate(rec.author_ids):
            name = rec.author_names[i] if i < len(rec.author_names) else aid
            position = rec.author_positions.get(aid, "middle")

            if aid not in authors:
                authors[aid] = AuthorEvidence(
                    author_id=aid,
                    name=name,
                )

            entry = authors[aid]

            if rec.work_id not in entry.matched_works:
                entry.matched_works.append(rec.work_id)
                entry.matched_titles.append(rec.title)
                entry.total_citations += rec.citations

            entry.positions.append(position)
            if position == "first":
                entry.first_author_count += 1
            elif position == "last":
                entry.last_author_count += 1
            else:
                entry.middle_author_count += 1

    total_authors = len(authors)
    logger.info(
        "[L3] Extracted %d unique authors from %d evidence records",
        total_authors, total_works,
    )

    return ExtractionResult(
        authors=authors,
        total_works=total_works,
        total_authors=total_authors,
    )


def compute_leadership_score(entry: AuthorEvidence) -> float:
    """
    Compute research leadership score based on author position.

    Formula:
      leadership = (first_count * 1.0 + last_count * 0.8 + middle_count * 0.3)
                   / total_works
    """
    total = len(entry.matched_works)
    if total == 0:
        return 0.0

    score = (
        entry.first_author_count * 1.0
        + entry.last_author_count * 0.8
        + entry.middle_author_count * 0.3
    ) / total

    return round(score, 4)
