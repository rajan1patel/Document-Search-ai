"""
Abstract Research Provider Interface.

Defines the contract that any research data provider must satisfy.
Currently implemented by OpenAlexProvider, but can be swapped for
any other provider (Semantic Scholar, Scopus, etc.) without changing
pipeline code.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ResearchWork:
    """A single research work (paper) from a provider."""
    work_id: str
    title: str
    abstract: str = ""
    year: Optional[int] = None
    citations: int = 0
    doi: str = ""
    source: str = ""
    topics: list[str] = field(default_factory=list)
    authors: list[dict] = field(default_factory=list)  # [{author_id, name, position, institution}]
    raw: dict = field(default_factory=dict)


@dataclass
class AuthorInfo:
    """Author profile from a provider (OpenAlex)."""
    author_id: str
    name: str
    works_count: int = 0
    cited_by_count: int = 0
    h_index: int = 0
    i10_index: int = 0
    counts_by_year: dict[str, int] = field(default_factory=dict)
    topics: list[dict] = field(default_factory=list)  # [{display_name, count, subfield}]
    institution: str = ""
    career_years: int = 0
    first_year: int = 0
    last_year: int = 0
    orcid: str = ""  # Normalized ORCID iD, e.g. "0000-0002-2192-9543"


@dataclass
class SearchResults:
    """Results from a research search."""
    query: str
    total: int = 0
    works: list[ResearchWork] = field(default_factory=list)
    xsearch_id: str = ""


class ResearchProvider(ABC):
    """Abstract base for research data providers."""

    @abstractmethod
    def search_works(self, query: str, limit: int = 20) -> SearchResults:
        """Search for research works matching the query."""
        ...

    @abstractmethod
    def get_author(self, author_id: str) -> Optional[AuthorInfo]:
        """Get detailed profile for a single author."""
        ...

    @abstractmethod
    def get_author_works(self, author_id: str, limit: int = 50) -> list[ResearchWork]:
        """Get recent works by an author (for activity/continuity analysis)."""
        ...
