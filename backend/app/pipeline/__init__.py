"""
Expert Discovery Pipeline.

Modules:
  schemas          — all data models (Pydantic)
  parser           — Step 1: Parse raw API JSON → ParsedDocument
  expert_extractor — Step 2: Extract & deduplicate expert profiles
  technology_extractor — Step 3: LLM-based technology extraction
  embedding_service    — Step 4: In-memory embedding similarity scoring
  ranking_engine       — Step 5: Weighted ranking algorithm
  enrichment_service   — Step 6: Contact enrichment (MVP: mocked)
  orchestrator         — Pipeline orchestrator (wires all steps)
"""
