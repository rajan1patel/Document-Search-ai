# 🔬 Research Expert Discovery — Full Pipeline Flow

> **Endpoint:** `POST /experts/search`
> **File:** `backend/app/api/routes/research_experts.py`
> **Orchestrator:** `backend/app/pipeline/research_orchestrator.py`

---

## 📋 High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        Frontend (Nuxt/Vue)                       │
│  research-experts.vue  ──►  useResearchExpert.ts  ──►  api.post │
└────────────────────────────────┬─────────────────────────────────┘
                                 │  POST /experts/search
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                     FastAPI Router (research_experts.py)         │
│  Validates request → calls run_expert_pipeline()                │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│              Research Orchestrator (research_orchestrator.py)    │
│                                                                  │
│  [L1] Research Retrieval ──── X-Search API (NPL corpus)         │
│  [L2] Paper Evidence Store ── In-memory per query               │
│  [L3] Author Extraction ───── ALL authors (no filtering)        │
│  [L4] Author Profile Builder ─ OpenAlex enrichment              │
│  [L5] LLM Topic Validation ── Batched + concurrent LLM calls   │
│  [L6] Expert Ranking Engine ── Weighted scoring + reasoning     │
│                                                                  │
│  └──► ResearchExpertResponse (ranked experts)                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Component-by-Component Breakdown

### 0️⃣ Entry Point — FastAPI Route

| File | Role |
|------|------|
| `backend/app/api/routes/research_experts.py` | Defines `POST /experts/search` endpoint |
| `backend/app/main.py` | Registers `research_experts_router` on the app |

**Flow:**
1. FastAPI receives `POST /experts/search` with `ResearchExpertRequest` body → `{ query, top_k }`
2. The route handler `search_experts()` calls `run_expert_pipeline(request)` from the orchestrator
3. On success, returns `ResearchExpertResponse` (ranked experts)
4. On failure, returns `500 HTTPException`

**Request Schema (`ResearchExpertRequest`):**
```json
{
  "query": "Find experts in quantum error correction",
  "top_k": 5
}
```

**Response Schema (`ResearchExpertResponse`):**
```json
{
  "query": "...",
  "total_works_found": 150,
  "total_authors_extracted": 320,
  "experts": [
    {
      "author_id": "A5034008951",
      "author": "John Doe",
      "score": 87.3,
      "metrics": { "works_count": 120, "citations": 5400, "h_index": 28 },
      "matched_topic": { "topic_name": "Quantum Computing", "topic_count": 15 },
      "all_topics": [ { "topic_name": "...", "count": 10, "subfield": "..." } ],
      "why": [ "Ranked #1 with overall score 0.873", "..." ],
      "institution": "MIT",
      "first_year": 2005,
      "last_year": 2025,
      "openalex_url": "https://openalex.org/authors/A5034008951"
    }
  ]
}
```

---

### 1️⃣ [L1] Research Retrieval — X-Search API

| File | Function | Role |
|------|----------|------|
| `backend/app/pipeline/research_retrieval.py` | `retrieve_works()` | Fetches research papers via X-Search |
| `backend/app/services/xsearch_client.py` | `XSearchClient.search()` | HTTP client for external API |
| `backend/app/core/config.py` | `settings.XSEARCH_*` | API key + base URL config |

**Flow:**
1. Generates a `query_id` (UUID) for this search session
2. Calls `XSearchClient.search()` with:
   - `nl_query` = user's natural language query
   - `corpora = ["npl"]` — searches **non-patent literature** only (journal papers, conference papers, preprints)
   - `page=1, page_size=100`
3. X-Search API returns: `{ xsearch_id, npl: { hits: [...] } }`
4. Parses raw NPL hits into `ResearchWorkSchema[]` via `_parse_xsearch_works()`
5. Extracts authors from `authorships` array — infers position (first/middle/last) from array index (X-Search returns `null` for `author_position`)
6. Returns: `{ query_id, works: ResearchWorkSchema[], xsearch_id, total }`

**Key Data Flow:**
```
X-Search Response (NPL) ───► ResearchWorkSchema[]
  _source.display_name     ───► title
  _source.authorships[]    ───► authors (id, name, position inferred)
```

---

### 2️⃣ [L2] Paper Evidence Store — In-Memory

| File | Function/Class | Role |
|------|---------------|------|
| `backend/app/pipeline/paper_evidence.py` | `build_evidence_records()` + `PaperEvidenceStore` | In-memory storage per query |

**Flow:**
1. `build_evidence_records()` converts `ResearchWorkSchema[]` to `PaperEvidenceRecord[]`
2. `PaperEvidenceStore.store_works()` stores records in a **module-level dict** keyed by `query_id`
3. Deduplicates by `work_id` within the same query
4. NOT persisted to any database — entirely in-memory, cleaned when server restarts
5. Provides lookup methods: `get_by_query()`, `get_author_evidence()`, `get_all_authors()`

**Purpose:** Allows later pipeline stages to reference the original evidence (author positions, etc.) without re-parsing.

---

### 3️⃣ [L3] Author Extraction — ALL Authors, No Filtering

| File | Function | Role |
|------|----------|------|
| `backend/app/pipeline/author_extractor.py` | `extract_authors_from_works()` | Extracts every author from every work |

**Design Principle:** *"Do not rank authors from the paper. Do not remove authors early. If a paper has 10 authors, all 10 enter the author pool."*

**Flow:**
1. Iterates over every `ResearchWorkSchema` in the works list
2. For each work, iterates over **all** authors
3. Skips authors with no OpenAlex ID (can't enrich later)
4. Builds `AuthorEvidence` objects with:
   - `author_id`, `name`
   - `matched_works[]` — list of work IDs
   - `matched_titles[]` — list of work titles
   - `positions[]` — raw position list
   - `first_author_count`, `last_author_count`, `middle_author_count`
5. Returns `ExtractionResult{ authors: dict[str, AuthorEvidence], total_works, total_authors }`

**Also provides:** `extract_authors_from_evidence()` — alternative path for re-processing stored evidence.

**Leadership score helper:** `compute_leadership_score()` = `(first*1.0 + last*0.8 + middle*0.3) / total_works`

---

### 4️⃣ [L4] Author Profile Builder — OpenAlex Enrichment

| File | Function | Role |
|------|----------|------|
| `backend/app/pipeline/author_profile_builder.py` | `build_profiles()` + `build_author_profile()` | Enrich authors with OpenAlex data |
| `backend/app/providers/openalex.py` | `OpenAlexProvider.get_author()` | HTTP client for OpenAlex API |
| `backend/app/providers/base.py` | `ResearchProvider` (ABC), `AuthorInfo` dataclass | Abstract provider interface |

**Flow:**
1. Takes ALL extracted `AuthorEvidence` objects from L3
2. For each author, calls `OpenAlexProvider.get_author()` with their OpenAlex ID
   - Handles ID formats: `https://openalex.org/A5034008951` → bare `A5034008951`
   - Fetches: `display_name`, `works_count`, `cited_by_count`, `h_index`, `i10_index`, `topics[]`, `counts_by_year`, `last_known_institutions`
3. Converts OpenAlex topics → `AuthorTopic[]` with `{ topic_name, count, subfield }`
4. Computes `career_years`, `first_year`, `last_year` from `counts_by_year`
5. If OpenAlex fetch fails, builds a **minimal profile** from evidence alone
6. Uses **ThreadPoolExecutor (max_workers=5)** for concurrent API calls
7. Returns `list[AuthorProfileSchema]`

**Key Data Flow:**
```
AuthorEvidence ──► OpenAlex API ──► AuthorProfileSchema
  author_id          /authors/{id}    h_index, topics, institution,
                                      career_years, works_count, etc.
```

---

### 5️⃣ [L5] LLM Topic Validation — Batched + Concurrent

| File | Function | Role |
|------|----------|------|
| `backend/app/pipeline/llm_topic_validator.py` | `batch_validate()` | LLM-based topic relevance check |
| `backend/app/services/llm_client.py` | `LLMClient.chat()` | OpenAI-compatible HTTP client (OpenRouter) |

**Flow:**
1. Takes all `AuthorProfileSchema` objects from L4
2. Splits profiles into **batches of 50** (`BATCH_SIZE`)
3. Processes batches **concurrently** with **3 workers** (`MAX_WORKERS`) via ThreadPoolExecutor
4. For each batch, calls LLM with a `BATCH_SYSTEM_PROMPT` asking it to validate each author's topics against the user's problem
5. LLM returns JSON: `{ "results": [{ "author_index": 0, "match": "yes"/"no", "matched_topics": [...] }, ...] }`
6. Maps results back to profiles using batch-local indices
7. **Filters out** any author where `match != "yes"` — only validated experts proceed
8. Returns `list[tuple[AuthorProfileSchema, TopicValidationResult]]`

**LLM Configuration (from `config.py`):**
```python
LLM_MODEL = "google/gemini-3.1-flash-image"
LLM_BASE_URL = "https://openrouter.ai/api/v1"
LLM_MAX_TOKENS = 16384
LLM_TEMPERATURE = 0.7
LLM_TIMEOUT = 180  # seconds
```

**Validation Rules:**
- Strict — only `"yes"` if clear topical overlap
- Topics like "Quantum Computing" match a query about "quantum error correction"
- If no topic matches → `"no"` → author is **removed** from the expert pool
- On LLM failure → conservative default: `match = "no"`

---

### 6️⃣ [L6] Expert Ranking Engine — Weighted Scoring

| File | Function | Role |
|------|----------|------|
| `backend/app/pipeline/expert_ranker.py` | `rank_experts()` | Weighted scoring + explainable ranking |

**Scoring Formula:**
```
expert_score =
  0.45 × problem_topic_match
+ 0.25 × topic_depth
+ 0.15 × research_continuity
+ 0.10 × research_ownership
+ 0.05 × impact
```

**Component Breakdown:**

| Component | Weight | How it's computed | What it measures |
|-----------|--------|-------------------|------------------|
| **Problem Topic Match** | 0.45 | Raw `matched_count` (number of distinct topics that matched). Pool normalization scales it relative to the best candidate. | **Breadth of relevance** — how many distinct areas of the author's expertise are relevant to the query. |
| **Topic Depth** | 0.25 | `matched_count / total_topics` — ratio of matched topics to author's all OpenAlex topics. | **Focused relevance** — what fraction of the author's research portfolio overlaps with the query. Higher = more focused. |
| **Research Continuity** | 0.15 | `career_years / 30` (capped at 1.0). | **Career longevity** — how sustained their research output has been. |
| **Research Ownership** | 0.10 | Leadership score: `(first×1.0 + last×0.8 + middle×0.3) / total_works`. Updated after normalization via `_update_ownership_scores()`. | **Leadership** — how often the author leads (first/last author) vs. contributes (middle author). |
| **Impact** | 0.05 | `h_index / 80` (or `citations / 10,000` if no h-index). | **Research influence** — citation-based impact, deliberately low weight to avoid biasing toward famous-but-irrelevant researchers. |

**Steps:**
1. **Compute raw scores** for each candidate using `_compute_component_scores()`
2. **Pool normalization** — each component scaled so max value = 1.0 (via `_normalize_scores()`)
3. **Apply weights** from the formula above
4. **Update ownership scores** after normalization using extracted author position evidence (via `_update_ownership_scores()`)
5. **Sort** with tiebreakers: `final_score → problem_topic_match → h_index`
6. **Scale to 0–100** for readability (`expert_score * 100`)
7. **Generate explainable reasoning** — identifies the top contributor, includes matched topics, institution, h-index
8. Returns `list[RankedExpertSchema]` (top_k only)

**Tiebreaker Order:**
1. `final_score` (descending)
2. `problem_topic_match` (descending)
3. `h_index` (descending)

---

### 7️⃣ Orchestrator — Tying It All Together

| File | `backend/app/pipeline/research_orchestrator.py` |
|------|--------------------------------------------------|
| Function | `run_expert_pipeline(request) → ResearchExpertResponse` |

**Complete Orchestration Flow:**

```
User Query
  │
  ▼
[L1] retrieve_works(query)
  │  X-Search API → ResearchWorkSchema[]
  │  Returns: { query_id, works, xsearch_id, total }
  │
  ▼
[L2] build_evidence_records(works) → PaperEvidenceRecord[]
  │  PaperEvidenceStore.store_works(query_id, records)
  │  (in-memory only)
  │
  ▼
[L3] extract_authors_from_works(works) → ExtractionResult
  │  ALL authors extracted — no pre-filtering
  │  Returns: { authors: dict[str, AuthorEvidence], total_works, total_authors }
  │
  ▼
[L4] build_profiles(authors, problem_domain) → AuthorProfileSchema[]
  │  OpenAlex concurrent enrichment (5 workers)
  │  h-index, topics, institution, career years
  │
  ▼
[L5] batch_validate(problem, profiles) → list of (profile, validation)
  │  LLM batched validation (50/batch, 3 concurrent workers)
  │  Filters: only keep profiles where match="yes"
  │
  ▼
[L6] rank_experts(validated_profiles, validations, problem, top_k)
  │  Weighted scoring → normalization → ownership update → ranking
  │  Returns: RankedExpertSchema[] (top_k)
  │
  ▼
Build ResearchExpertResponse
  │  Maps ranked experts → ResearchExpertOutput[]
  │  Adds openalex_url for each expert
  │
  ▼
Return ResearchExpertResponse
```

**Early Exit Conditions:**
- If **no works** retrieved → empty response (total_works_found=0)
- If **no authors** extracted → empty response (total_authors_extracted=0)
- If **no profiles** built → empty response
- If **no validated experts** after LLM step → empty response

**Logging:** Every step logs structured JSON events with `query_id` for tracing and debugging.

---

## 🌐 Frontend Integration

| File | Role |
|------|------|
| `frontend/app/pages/research-experts.vue` | UI page with search bar, expert cards, expandable details |
| `frontend/app/composables/useResearchExpert.ts` | API call wrapper — `searchExperts(query, topK)` |
| `frontend/app/utils/api.ts` | Base API client (`api.post()`) |

**Frontend Flow:**
1. User types a research problem (or clicks an example query)
2. Clicks "Search Experts" → calls `searchExperts(query, 20)`
3. Composables sends `POST /api/experts/search` with `{ query, top_k: 20 }`
4. Displays results: summary stats (papers found, authors extracted, experts ranked)
5. Each expert card shows: name, institution, score, reasoning bullets
6. Click "Details" expands: metrics (works, citations, h-index), all topics, OpenAlex link

---

## 🗂️ Schema Model Hierarchy

All schemas are defined in `backend/app/pipeline/schemas.py`:

```
ResearchExpertRequest          ──► Input: { query, top_k }
  │
  ▼
ResearchWorkSchema             ──► { work_id, title, authors[] }
  │
  ▼
PaperEvidenceRecord            ──► { work_id, title, author_ids[], author_positions{} }
  │
  ▼
AuthorEvidence                 ──► { author_id, name, matched_works[], positions[],
  │                                  first_author_count, last_author_count, ... }
  ▼
AuthorProfileSchema            ──► { author_id, name, h_index, topics[], institution,
  │                                  career_years, ... }
  ▼
TopicValidationResult          ──► { match: "yes"/"no", matched_topics[] }
  │
  ▼
ComponentScores                ──► { problem_topic_match, topic_depth,
  │                                  research_continuity, research_ownership, impact }
  ▼
RankedExpertSchema             ──► { author_id, name, expert_score, metrics{},
  │                                  matched_topic, all_topics, score_breakdown,
  │                                  reasoning[], institution, ... }
  ▼
ResearchExpertOutput           ──► { author_id, author, score, metrics{},
  │                                  matched_topic, all_topics, why[],
  │                                  institution, first_year, last_year, openalex_url }
  ▼
ResearchExpertResponse         ──► { query, total_works_found, total_authors_extracted,
                                     experts[] }
```

---

## 🔧 External Dependencies

| Service | Used By | Purpose |
|---------|---------|---------|
| **X-Search API** (`xsearch_client.py`) | L1 — Research Retrieval | Fetches research papers (NPL corpus) |
| **OpenAlex API** (`openalex.py`) | L4 — Profile Builder | Enriches authors with h-index, topics, institution |
| **OpenRouter / LLM** (`llm_client.py`) | L5 — Topic Validation | Validates topic relevance via LLM |

---

## 🔐 Configuration (`.env`)

```ini
XSEARCH_API_KEY=...          # X-Search API key
XSEARCH_BASE_URL=...         # http://192.168.0.57:8082/patent_search
OPENALEX_APIKEY=...          # OpenAlex API key (optional, free tier)
OPENROUTER_API_KEY=...       # OpenRouter API key
LLM_MODEL=google/gemini-3.1-flash-image
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MAX_TOKENS=16384
LLM_TEMPERATURE=0.7
LLM_TIMEOUT=180
```
