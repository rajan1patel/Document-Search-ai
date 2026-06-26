"""
Pipeline data models for the Expert Discovery Pipeline.

Every pipeline step has explicit input/output schemas.
This keeps steps independent and verifiable.
"""
from __future__ import annotations

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Step 1: Parsed Document
# ──────────────────────────────────────────────

class ParsedDocument(BaseModel):
    """Clean internal document object from raw patent JSON."""
    document_id: str = Field(..., description="Patent publication ID, e.g. AU2008305666B2")
    type: str = Field(default="patent", description="Document type")
    title: str = Field(default="", description="Patent title")
    abstract: str = Field(default="", description="Patent abstract (cleaned)")
    claims: list[str] = Field(default_factory=list, description="Patent claims")
    inventors: list[str] = Field(default_factory=list, description="Inventor names")
    assignees: list[str] = Field(default_factory=list, description="Assignee organizations")
    applicants: list[str] = Field(default_factory=list, description="Applicant names/orgs")
    publication_date: Optional[date] = Field(default=None, description="Publication date")
    filing_date: Optional[date] = Field(default=None, description="Filing date")
    priority_date: Optional[date] = Field(default=None, description="Priority date")
    text_content: str = Field(default="", description="Combined title + abstract + claims for AI processing")


# ──────────────────────────────────────────────
# Step 2: Expert Profile
# ──────────────────────────────────────────────

class ExpertDocumentRef(BaseModel):
    """A document reference attached to an expert."""
    document_id: str
    title: str
    role: str  # inventor, applicant, assignee


class ExpertProfile(BaseModel):
    """Merged profile of a single expert extracted from documents."""
    name: str
    normalized_name: str = Field(default="", description="Lowercase stripped version for dedup")
    documents: list[ExpertDocumentRef] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    primary_role: str = Field(default="inventor", description="Highest-priority role")
    organizations: list[str] = Field(default_factory=list)


# ──────────────────────────────────────────────
# Step 3: Technology / Expertise
# ──────────────────────────────────────────────

class TechnologyExpertise(BaseModel):
    """Technology expertise extracted from a single document via LLM."""
    document_id: str
    domain: str = Field(default="", description="Technology domain, e.g. Pharmaceutical")
    sub_domain: str = Field(default="", description="Sub-domain, e.g. Antiviral compounds")
    skills: list[str] = Field(default_factory=list, description="Specific skills")
    keywords: list[str] = Field(default_factory=list, description="Key terms")
    research_area: str = Field(default="", description="Broad research area")


class EnrichedExpertProfile(BaseModel):
    """Expert profile with attached technology expertise."""
    name: str
    normalized_name: str = ""
    expertise: list[str] = Field(default_factory=list, description="Aggregated skills across all documents")
    domains: list[str] = Field(default_factory=list)
    documents: list[ExpertDocumentRef] = Field(default_factory=list)
    primary_role: str = "inventor"
    organizations: list[str] = Field(default_factory=list)
    expertise_strength: int = Field(default=0, description="Number of documents linked to this expert")
    role_score: float = Field(default=0.0, description="Score based on role priority")


# ──────────────────────────────────────────────
# Step 4: Embedding Scores
# ──────────────────────────────────────────────

class EmbeddingScore(BaseModel):
    """Cosine similarity scores for an expert."""
    expert_name: str
    technical_match_score: float = Field(default=0.0, ge=0.0, le=1.0)
    text_representation: str = ""


# ──────────────────────────────────────────────
# Step 5: Ranked Expert
# ──────────────────────────────────────────────

class EvidenceDocument(BaseModel):
    """Evidence supporting an expert's ranking."""
    title: str
    patent_id: str
    role: str = ""


class RankedExpert(BaseModel):
    """Final ranked expert output."""
    rank: int
    name: str
    score: float
    expertise: list[str] = Field(default_factory=list)
    reasoning: str = ""
    evidence: list[EvidenceDocument] = Field(default_factory=list)
    contact: Optional[dict] = None


# ──────────────────────────────────────────────
# Step 6: Contact Info
# ──────────────────────────────────────────────

class ContactInfo(BaseModel):
    """Contact information for an expert."""
    name: str
    email: str = ""
    organization: str = ""
    profile_url: str = ""


# ──────────────────────────────────────────────
# Step 7: API Request / Response
# ──────────────────────────────────────────────

class DiscoverExpertsRequest(BaseModel):
    """Request body for POST /discover-experts.

    Only `query` is required. The backend automatically fetches patent
    documents from the external X-Search API using the configured API key.
    """
    query: str = Field(..., description="Natural language query, e.g. 'Find experts in lithium battery cathode materials'")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of top experts to return")
    # Optional overrides
    xsearch_api_key: Optional[str] = Field(default=None, description="Override the default X-Gravitee-Api-Key")
    page: int = Field(default=1, ge=1, description="Page number for X-Search pagination")
    page_size: int = Field(default=20, ge=1, le=100, description="Page size for X-Search")


class ExpertOutput(BaseModel):
    """Single expert in the API response."""
    rank: int
    name: str
    score: float
    expertise: list[str]
    reasoning: str
    evidence: list[EvidenceDocument]
    contact: Optional[dict] = None


class DiscoverExpertsResponse(BaseModel):
    """Response body for POST /discover-experts."""
    query: str
    xsearch_id: Optional[str] = Field(default=None, description="X-Search session ID for pagination")
    total_documents_found: int = 0
    raw_documents: list[dict] = Field(default_factory=list, description="Raw patent JSON as-is from X-Search API")
    experts: list[ExpertOutput] = Field(default_factory=list)


# ══════════════════════════════════════════════
# Research Expert Discovery — Layer Schemas
# ══════════════════════════════════════════════

# ── Layer 1: Research Work ───────────────────

class ResearchWorkAuthor(BaseModel):
    """Author entry within a research work — only identity fields from X-Search."""
    author_id: str = Field(default="", description="OpenAlex author ID")
    name: str = Field(default="", description="Author display name")
    position: str = Field(default="", description="Author position: first, middle, last")


class ResearchWorkSchema(BaseModel):
    """
    A single research work from X-Search.
    Only work_id, title, and authors extracted — all other data comes from OpenAlex.
    """
    work_id: str = Field(default="", description="Unique work identifier")
    title: str = Field(default="", description="Work title")
    authors: list[ResearchWorkAuthor] = Field(default_factory=list)


# ── Layer 2: Paper Evidence ──────────────────

class PaperEvidenceRecord(BaseModel):
    """Lightweight evidence record for a single work (in-memory)."""
    work_id: str
    title: str
    author_ids: list[str] = Field(default_factory=list)
    author_names: list[str] = Field(default_factory=list)
    author_positions: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of author_id → position (first/middle/last)",
    )


class PaperEvidenceStore(BaseModel):
    """In-memory store of evidence per query_id. NOT persisted to DB."""
    query_id: str
    works: list[PaperEvidenceRecord] = Field(default_factory=list)


# ── Layer 3: Author Extraction ───────────────

class AuthorEvidence(BaseModel):
    """Extracted author with evidence from research works."""
    author_id: str
    name: str
    matched_works: list[str] = Field(default_factory=list, description="Work IDs this author appears in")
    matched_titles: list[str] = Field(default_factory=list)
    positions: list[str] = Field(default_factory=list)
    first_author_count: int = 0
    last_author_count: int = 0
    middle_author_count: int = 0
    total_citations: int = 0


# ── Layer 4: OpenAlex Author Profile ─────────

class AuthorTopic(BaseModel):
    """A research topic from OpenAlex."""
    topic_name: str = ""
    count: int = 0
    subfield: str = ""


class AuthorProfileSchema(BaseModel):
    """Full author profile from OpenAlex enrichment."""
    author_id: str
    name: str
    works_count: int = 0
    cited_by_count: int = 0
    h_index: int = 0
    i10_index: int = 0
    counts_by_year: dict[str, int] = Field(default_factory=dict)
    topics: list[AuthorTopic] = Field(default_factory=list)
    subfields: list[str] = Field(default_factory=list)
    institution: str = ""
    career_years: int = 0
    first_year: int = 0
    last_year: int = 0
    matched_topic: Optional[str] = None
    matched_topic_count: int = 0
    topic_match_score: float = 0.0
    orcid: str = ""  # Normalized ORCID iD, e.g. "0000-0002-2192-9543"


# ── Layer 5: LLM Validation ─────────────────

class TopicValidationResult(BaseModel):
    """LLM's validation of author topic relevance."""
    match: str = "no"  # "yes" or "no"
    matched_topics: list[dict] = Field(
        default_factory=list,
        description="[{topic_name, count, reason}]",
    )


# ── Layer 6: Expert Ranking ─────────────────

class ComponentScores(BaseModel):
    """Breakdown of each scoring component."""
    problem_topic_match: float = 0.0
    topic_depth: float = 0.0
    research_continuity: float = 0.0
    research_ownership: float = 0.0
    impact: float = 0.0


class RankedExpertSchema(BaseModel):
    """Final ranked expert output."""
    author_id: str
    name: str
    expert_score: float = 0.0
    metrics: dict = Field(default_factory=lambda: {
        "works_count": 0,
        "citations": 0,
        "h_index": 0,
    })
    matched_topic: Optional[dict] = None
    all_topics: list[dict] = Field(default_factory=list)
    score_breakdown: ComponentScores = Field(default_factory=ComponentScores)
    reasoning: list[str] = Field(default_factory=list)
    institution: str = ""
    first_year: int = 0
    last_year: int = 0
    contacts: list["ContactEntry"] = Field(
        default_factory=list,
        description="Public contact info enriched from ORCID after ranking",
    )
    orcid: str = ""  # Normalized ORCID iD, e.g. "0000-0002-2192-9543"


# ── API Request / Response ──────────────────

class ResearchExpertRequest(BaseModel):
    """Request body for POST /experts/search."""
    query: str = Field(..., description="Natural language query, e.g. 'Find experts in quantum error correction'")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of top experts to return")


class ContactEntry(BaseModel):
    """A single contact entry from ORCID enrichment."""
    type: str = Field(..., description="Contact type: 'email' or 'url'")
    value: str = Field(..., description="The email address or URL")
    label: str = Field(default="", description="Display label (for URLs)")
    source: str = Field(default="orcid", description="Source of the contact data")


class ResearchExpertOutput(BaseModel):
    """Single expert in the research expert discovery response."""
    author_id: str = ""
    author: str
    score: float
    metrics: dict = Field(default_factory=lambda: {
        "works_count": 0,
        "citations": 0,
        "h_index": 0,
    })
    matched_topic: Optional[dict] = Field(
        default=None,
        description="{topic_name, topic_count} of best matched topic",
    )
    all_topics: list[dict] = Field(
        default_factory=list,
        description="[{topic_name, count, subfield}]",
    )
    why: list[str] = Field(default_factory=list)
    institution: str = ""
    first_year: int = 0
    last_year: int = 0
    openalex_url: str = ""
    contacts: list[ContactEntry] = Field(
        default_factory=list,
        description="Public contact info enriched from ORCID",
    )
    orcid: str = ""  # Normalized ORCID iD for linking to ORCID profile


class ResearchExpertResponse(BaseModel):
    """Response body for POST /experts/search."""
    query: str
    total_works_found: int = 0
    total_authors_extracted: int = 0
    experts: list[ResearchExpertOutput] = Field(default_factory=list)
