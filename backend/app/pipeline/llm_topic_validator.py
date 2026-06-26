"""
Layer 5: LLM Topic Validation

Uses LLM to validate whether an author's research topics are relevant to
the user's problem.

This is a strict JSON-based validation step:
  - Input: user problem + author topics
  - Output: {"match": "yes"/"no", "matched_topics": [...]}

If match = "no" → author is removed from the expert pool (in Layer 6).
If match = "yes" → author proceeds to ranking with matched_topic info.

Performance:
  - Authors are processed in batches of 50 per LLM call
  - 3 concurrent workers run in parallel via ThreadPoolExecutor
"""
from __future__ import annotations

import concurrent.futures
import json
import logging
from typing import Optional

from app.pipeline.schemas import AuthorProfileSchema, TopicValidationResult
from app.services.llm_client import llm_client

logger = logging.getLogger(__name__)


# ── Constants ────────────────────────────────
BATCH_SIZE = 50
MAX_WORKERS = 3


SINGLE_SYSTEM_PROMPT = """You are a research topic validator. Your job is to determine if an author's research topics are related to a given user problem.

Return a JSON object with these fields:
- "match": "yes" if at least one topic is clearly related, "no" otherwise
- "matched_topics": array of objects, each with:
  - "topic_name": the exact topic name from the input
  - "count": the author's work count for that topic
  - "reason": one sentence explaining why this topic matches

Rules:
1. Be strict — only return "yes" if there is clear topical overlap
2. A topic like "Quantum Computing" matches a query about "quantum error correction"
3. A topic like "Battery Materials" matches a query about "lithium batteries"
4. If no topic matches, return {"match": "no"}
5. Do NOT make up topics — only use the topics provided in the input
6. Return ONLY valid JSON, no other text"""


BATCH_SYSTEM_PROMPT = """You are a research topic validator. Your job is to validate MULTIPLE authors' topics against the user's problem in a single response.

Return a JSON object with a single key "results" whose value is a JSON array where each element corresponds to one author, in the same order:
[
  {
    "author_index": 0,
    "match": "yes" or "no",
    "matched_topics": [
      {
        "topic_name": "exact topic name from input",
        "count": <author's work count for this topic>,
        "reason": "one sentence why this matches"
      }
    ]
  },
  ...
]

Rules:
1. Be strict — only return "yes" if there is clear topical overlap
2. If no topic matches for an author, return {"author_index": N, "match": "no", "matched_topics": []}
3. Do NOT make up topics — only use the topics provided in the input
4. Return ONLY valid JSON, no other text"""


def validate_author_topics(
    problem: str,
    profile: AuthorProfileSchema,
) -> Optional[TopicValidationResult]:
    """
    Validate whether an author's topics match the user's problem.

    Args:
        problem: The user's problem description
        profile: Author's profile with topics

    Returns:
        TopicValidationResult or None if LLM call fails
    """
    if not profile.topics:
        logger.info(
            "[L5] No topics for %s (%s) → no match",
            profile.name, profile.author_id,
        )
        return TopicValidationResult(match="no", matched_topics=[])

    # Build compact topic list for LLM
    topic_list = [
        f"- {t.topic_name} (count: {t.count}, subfield: {t.subfield})"
        for t in profile.topics[:20]  # limit to top 20 topics
    ]
    topics_text = "\n".join(topic_list)

    user_prompt = f"""User Problem: {problem}

Author: {profile.name}

Research Topics:
{topics_text}

Does this author have research experience related to the user problem?
Return strict JSON with "match" and "matched_topics"."""

    try:
        raw = llm_client.chat(
            system_prompt=SINGLE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_format={"type": "json_object"},
        )

        # Parse JSON from response
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            raw = "\n".join(lines).strip()

        result = json.loads(raw)
        validation = TopicValidationResult(
            match=result.get("match", "no"),
            matched_topics=result.get("matched_topics", []),
        )

        logger.info(
            "[L5] %s → match=%s | matched_topics=%d",
            profile.name, validation.match, len(validation.matched_topics),
        )
        return validation

    except Exception as exc:
        logger.warning(
            "[L5] LLM validation failed for %s: %s",
            profile.name, exc,
        )
        # On failure, be conservative: mark as no match
        return TopicValidationResult(match="no", matched_topics=[])


def _validate_batch(
    problem: str,
    batch: list[AuthorProfileSchema],
    global_start_index: int,
) -> list[tuple[AuthorProfileSchema, TopicValidationResult]]:
    """
    Validate a single batch of authors (≤BATCH_SIZE) in one LLM call.

    Args:
        problem: The user's problem description
        batch: The batch of author profiles to validate
        global_start_index: The index of the first author in this batch
                            within the full profiles list (used for author_index)

    Returns:
        List of (profile, validation_result) tuples for this batch.
    """
    if not batch:
        return []

    logger.info(
        "[L5] Validating batch of %d authors (global offset=%d)",
        len(batch), global_start_index,
    )

    # Build a compact list of authors for the LLM prompt
    author_entries = []
    for offset, p in enumerate(batch):
        topics_str = "; ".join(
            f"{t.topic_name} (count={t.count}, subfield={t.subfield})"
            for t in p.topics[:10]  # top 10 topics per author
        )
        author_entries.append(
            f"[{offset}] {p.name}: {topics_str or '(no topics)'}"
        )

    authors_text = "\n".join(author_entries)
    user_prompt = f"""User Problem: {problem}

Authors and their research topics:
{authors_text}

For each author, determine if they have research experience related to the user problem.
Return a JSON object with key "results" whose value is a JSON array with one result per author in the SAME order."""

    try:
        raw = llm_client.chat(
            system_prompt=BATCH_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_format={"type": "json_object"},
        )

        # Parse the batch response
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            raw = "\n".join(lines).strip()

        try:
            batch_results = json.loads(raw)
        except json.JSONDecodeError as parse_err:
            logger.error(
                "[L5] JSON parse failed for batch at offset %d. "
                "Raw response (first 2000 chars): %s",
                global_start_index, raw[:2000],
            )
            raise RuntimeError(
                f"[L5] LLM returned invalid JSON for batch at offset "
                f"{global_start_index}: {parse_err}"
            ) from parse_err

        # Response is { "results": [...] }
        if isinstance(batch_results, dict):
            batch_results = batch_results.get("results", batch_results.get("validations", []))

        # Map results back to profiles using batch-local indices
        results: list[tuple[AuthorProfileSchema, TopicValidationResult]] = []
        for offset, profile in enumerate(batch):
            entry = None
            for r in batch_results:
                if isinstance(r, dict) and r.get("author_index") == offset:
                    entry = r
                    break

            if entry:
                validation = TopicValidationResult(
                    match=entry.get("match", "no"),
                    matched_topics=entry.get("matched_topics", []),
                )
            else:
                validation = TopicValidationResult(match="no", matched_topics=[])

            results.append((profile, validation))

        matched = sum(1 for _, v in results if v.match == "yes")
        logger.info(
            "[L5] Batch complete: %d matched, %d no-match out of %d",
            matched, len(results) - matched, len(results),
        )
        return results

    except Exception as exc:
        logger.error(
            "[L5] Batch LLM call failed for batch at offset %d (%d authors): %s",
            global_start_index, len(batch), exc,
        )
        raise RuntimeError(
            f"[L5] LLM validation failed for batch at offset {global_start_index} "
            f"({len(batch)} authors): {exc}"
        ) from exc


def batch_validate(
    problem: str,
    profiles: list[AuthorProfileSchema],
) -> list[tuple[AuthorProfileSchema, TopicValidationResult]]:
    """
    Validate ALL authors against the user problem using batched + concurrent LLM calls.

    Splits profiles into chunks of {BATCH_SIZE} and processes them with
    {MAX_WORKERS} concurrent workers via ThreadPoolExecutor.

    Falls back to per-author validation if any batch call fails.

    Returns list of (profile, validation_result) tuples in the original order.
    """
    if not profiles:
        return []

    total = len(profiles)
    logger.info(
        "[L5] Batch validating %d profiles (batch_size=%d, workers=%d) — problem: '%s'",
        total, BATCH_SIZE, MAX_WORKERS, problem[:60],
    )

    # Split profiles into chunks of BATCH_SIZE
    chunks: list[tuple[int, list[AuthorProfileSchema]]] = []
    for start in range(0, total, BATCH_SIZE):
        end = min(start + BATCH_SIZE, total)
        chunks.append((start, profiles[start:end]))

    logger.info(
        "[L5] Split into %d batches (last batch: %d authors)",
        len(chunks), len(chunks[-1][1]) if chunks else 0,
    )

    # Process batches concurrently with MAX_WORKERS threads
    all_results: list[tuple[int, list[tuple[AuthorProfileSchema, TopicValidationResult]]]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {
            executor.submit(_validate_batch, problem, batch, start): (start, batch)
            for start, batch in chunks
        }

        for future in concurrent.futures.as_completed(future_map):
            start_idx, batch = future_map[future]
            try:
                batch_results = future.result()
                all_results.append((start_idx, batch_results))
                logger.info(
                    "[L5] Worker completed batch at offset %d (%d authors)",
                    start_idx, len(batch),
                )
            except Exception as exc:
                logger.error(
                    "[L5] Worker failed for batch at offset %d: %s",
                    start_idx, exc,
                )
                raise

    # Reassemble results in original order by sorting by start index
    all_results.sort(key=lambda x: x[0])
    final_results: list[tuple[AuthorProfileSchema, TopicValidationResult]] = []
    for _, batch_results in all_results:
        final_results.extend(batch_results)

    # Summary stats
    total_matched = sum(1 for _, v in final_results if v.match == "yes")
    logger.info(
        "[L5] All batches complete: %d matched, %d no-match out of %d (workers=%d)",
        total_matched, total - total_matched, total, MAX_WORKERS,
    )

    return final_results
