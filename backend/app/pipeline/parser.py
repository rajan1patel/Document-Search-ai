"""
Step 1: Patent Document Parser

Converts raw patent JSON (from Landscapes API / X-Search) into a clean
internal ParsedDocument object.

Input:  Raw API JSON (list of dicts with _id, _source)
Output: list[ParsedDocument]

Key transformations:
  - Strips HTML tags from abstract, claims, descriptions
  - Concatenates title + abstract + claims → text_content (for LLM)
  - Parses date strings into date objects
"""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

from app.pipeline.schemas import ParsedDocument


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _strip_html(text: str) -> str:
    """Remove HTML/XML tags from a string."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parse_date(value: Any) -> date | None:
    """Parse a date string (YYYY-MM-DD) into a date object."""
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _safe_str_list(value: Any) -> list[str]:
    """Ensure the value is a list of strings."""
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(v) for v in value if v]
    return []


def _extract_claims(source: dict) -> list[str]:
    """Extract claims from the summary.claims.raw field."""
    summary = source.get("summary") or {}
    claims_raw = summary.get("claims.raw")
    if isinstance(claims_raw, list):
        return [_strip_html(c) for c in claims_raw if c]
    if isinstance(claims_raw, str):
        return [_strip_html(claims_raw)]
    return []


def _extract_abstract(source: dict) -> str:
    """Extract and clean the abstract — prefer top-level abstract, fallback to summary."""
    abstract = source.get("abstract") or ""
    if not abstract:
        summary = source.get("summary") or {}
        abstract_raw = summary.get("abstract.raw")
        if isinstance(abstract_raw, list) and abstract_raw:
            abstract = " ".join(abstract_raw)
        elif isinstance(abstract_raw, str):
            abstract = abstract_raw
    return _strip_html(abstract)


# ──────────────────────────────────────────────
# Main parse function
# ──────────────────────────────────────────────

def parse_document(raw: dict) -> ParsedDocument:
    """
    Parse a single raw patent JSON document into a ParsedDocument.
    """
    source = raw.get("_source") or {}
    doc_id = raw.get("_id", "")

    title = source.get("title", "")
    abstract = _extract_abstract(source)
    claims = _extract_claims(source)

    # Build text_content: title + abstract + claims
    claims_text = " ".join(claims) if claims else ""
    parts = [title, abstract, claims_text]
    text_content = "\n\n".join(p for p in parts if p)

    return ParsedDocument(
        document_id=doc_id,
        type="patent",
        title=title,
        abstract=abstract,
        claims=claims,
        inventors=_safe_str_list(source.get("inventors")),
        assignees=_safe_str_list(source.get("assignees")),
        applicants=_safe_str_list(source.get("applicants")),
        publication_date=_parse_date(source.get("publicationDate")),
        filing_date=_parse_date(source.get("filingDate")),
        priority_date=_parse_date(source.get("priorityDate")),
        text_content=text_content,
    )


def parse_documents(raw_documents: list[dict]) -> list[ParsedDocument]:
    """
    Parse a list of raw patent JSON documents.
    """
    return [parse_document(doc) for doc in raw_documents]
