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
