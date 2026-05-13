"""End-to-end metadata extraction pipeline.

Workflow per page:
    1. (Optional) regex pass over the full text → top_k keywords.
    2. LLM pass over chunks, run concurrently, with the reduced (or full)
       keyword list.
    3. Merge per-chunk MaterialMetadata into one; validate LLM keywords
       against the known list; union with the regex top_k (if any).
    4. Return a PageExtractionReport that preserves chunk-level outputs
       and audit information.

Set ``regex_enabled=False`` in ``extract_page_metadata`` to ablate the
regex pre-pass — useful for comparing pipeline variants.
"""

import asyncio
import json
import logging
import time
import os
from collections.abc import Iterable
from datetime import datetime

from openai import AsyncOpenAI
from pydantic import BaseModel

from config import get_provider_config
from llm_extractor import KEYWORDS, analyze_content_with_llm_async
from regex_extractor import count_keyword_occurrences, split_keywords
from schemas import MaterialMetadata

logger = logging.getLogger(__name__)


# ============================================================================
# Audit report
# ============================================================================
class PageExtractionReport(BaseModel):
    """Per-page extraction result with audit data.

    Fields:
        merged: Final fused MaterialMetadata for the page.
        chunks: Per-chunk MaterialMetadata before fusion. Inspect these to
            see where chunks disagreed and the merge had to pick.
        regex_keywords: Keywords confirmed by the regex pre-pass.
            Empty list when ``regex_enabled=False``.
        discarded_keywords: Keywords the LLM emitted that were not in the
            known list; filtered out of ``merged`` but kept here so you
            can see what the model is hallucinating.
        extraction_seconds: Wall-clock time of the extraction.
    """

    merged: MaterialMetadata
    chunks: list[MaterialMetadata]
    regex_keywords: list[str]
    discarded_keywords: list[str]
    extraction_seconds: float


# ============================================================================
# Chunking
# ============================================================================
def chunk_text(text: str, n_chunks: int = 3) -> list[str]:
    """Split text into roughly ``n_chunks`` pieces (byte-based, no overlap).

    Naive but acceptable: the pipeline unions results across chunks, so
    information cut at a boundary in one chunk is usually preserved in a
    neighbour. Swap in a paragraph-aware or overlapping splitter if needed.
    """
    if n_chunks <= 1 or not text:
        return [text] if text else []
    size = max(1, len(text) // n_chunks)
    return [text[i : i + size] for i in range(0, len(text), size)]


# ============================================================================
# Keyword validation
# ============================================================================
def validate_keywords(
    candidates: Iterable[str],
    known_keywords: Iterable[str],
) -> tuple[list[str], list[str]]:
    """Split LLM-emitted keywords into (valid_canonical, invented).

    Comparison is case-insensitive and whitespace-trimmed. Returned valid
    entries use the canonical spelling from ``known_keywords``. Invented
    entries are logged and returned so the caller can preserve them in
    audit output.
    """
    canonical = {kw.lower().strip(): kw for kw in known_keywords}
    valid: list[str] = []
    invented: list[str] = []
    for c in candidates or []:
        if not c or c == "Not found":
            continue
        canon = canonical.get(c.lower().strip())
        if canon is not None:
            valid.append(canon)
        else:
            invented.append(c)
    if invented:
        logger.warning(
            "LLM produced %d invented keyword(s) (discarded): %s",
            len(invented),
            invented,
        )
    return valid, invented


# ============================================================================
# Merge per-chunk MaterialMetadata
# ============================================================================
_LIST_FIELDS = {"keywords", "authors", "contributors"}
_LONGEST_TEXT_FIELDS = {"description", "learning_objectives", "prerequisites"}


def _merge_scalar(values: list[str], strategy: str = "first") -> str:
    """Pick a scalar value across chunks, treating "Not found" as missing."""
    present = [v for v in values if v and v != "Not found"]
    if not present:
        return "Not found"
    if strategy == "longest":
        return max(present, key=len)
    return present[0]


def _dedup_preserve_order(items: Iterable[str]) -> list[str]:
    """Remove duplicates and "Not found" entries, preserve insertion order."""
    return list(dict.fromkeys(x for x in items if x and x != "Not found"))


def _merge_list_field(values: list[list[str]]) -> list[str]:
    return _dedup_preserve_order(item for lst in values for item in (lst or []))


def merge_chunk_results(
    chunk_results: list[MaterialMetadata],
    regex_keywords: list[str],
    known_keywords: Iterable[str],
) -> tuple[MaterialMetadata, list[str]]:
    """Fuse per-chunk results into one MaterialMetadata.

    - Scalar fields: first non-"Not found" (or longest for description/learning_objectives).
    - List fields: union, deduped, order preserved.
    - "keywords": regex top_k ∪ validated LLM keywords across all chunks.

    Returns:
        Tuple ``(merged, discarded)``:
            merged: The fused MaterialMetadata.
            discarded: LLM keywords filtered out (not in ``known_keywords``).
    """
    if not chunk_results:
        raise ValueError("merge_chunk_results: empty chunk_results")

    merged: dict = {}
    for field in MaterialMetadata.model_fields:
        if field == "keywords":
            continue  # handled separately below
        values = [getattr(r, field) for r in chunk_results]
        if field in _LIST_FIELDS:
            merged[field] = _merge_list_field(values)
        elif field in _LONGEST_TEXT_FIELDS:
            merged[field] = _merge_scalar(values, "longest")
        else:
            merged[field] = _merge_scalar(values, "first")

    llm_keywords_flat = [kw for r in chunk_results for kw in (r.keywords or [])]
    validated, discarded = validate_keywords(llm_keywords_flat, known_keywords)
    merged["keywords"] = _dedup_preserve_order([*regex_keywords, *validated])

    return MaterialMetadata(**merged), discarded


# ============================================================================
# Async orchestration over chunks
# ============================================================================
async def analyze_chunks_async(
    chunks: list[str],
    keywords: list[str],
    provider: str | None = None,
    max_concurrency: int | None = None,
) -> list[MaterialMetadata]:
    """Run the LLM extractor on each chunk concurrently, bounded by a semaphore.

    Concurrency precedence:
        1. The explicit ``max_concurrency`` argument, if provided.
        2. ``cfg.max_concurrency`` from the provider config.
        3. Safe default of 1 (strict serialization).

    Why config-driven: concurrency is a property of the provider, not the
    call site. Local backends like Ollama serialize internally and queue
    excess requests server-side (which can time out and pile up memory);
    setting ``max_concurrency=1`` for them sidesteps that entirely. Cloud
    providers (OpenAI, Anthropic) can safely run several in flight.

    Failures on individual chunks are logged but do not crash the pipeline,
    as long as at least one chunk succeeds.
    """
    if not chunks:
        return []

    cfg = get_provider_config(provider)
    effective_concurrency = (
        max_concurrency
        if max_concurrency is not None
        else getattr(cfg, "max_concurrency", 1)
    )
    logger.info(
        "Provider '%s': running %d chunk(s) with max_concurrency=%d",
        cfg.name,
        len(chunks),
        effective_concurrency,
    )

    client = AsyncOpenAI(api_key=cfg.api_key, base_url=cfg.base_url)
    semaphore = asyncio.Semaphore(effective_concurrency)

    async def _one(chunk: str, idx: int) -> MaterialMetadata:
        async with semaphore:
            logger.info(
                "Analyzing chunk %d/%d (%d chars)", idx + 1, len(chunks), len(chunk)
            )
            return await analyze_content_with_llm_async(
                chunk, provider=provider, keywords=keywords, client=client
            )

    try:
        results = await asyncio.gather(
            *(_one(c, i) for i, c in enumerate(chunks)),
            return_exceptions=True,
        )
    finally:
        await client.close()

    ok = [r for r in results if isinstance(r, MaterialMetadata)]
    for r in results:
        if isinstance(r, BaseException):
            logger.error("Chunk analysis failed: %s", r)
    if not ok:
        raise RuntimeError("All chunks failed during LLM analysis")
    return ok


# ============================================================================
# Full pipeline for one page
# ============================================================================
async def extract_page_metadata(
    content: str,
    *,
    all_keywords: list[str] = KEYWORDS,
    top_k: int = 10,
    n_chunks: int = 3,
    provider: str | None = None,
    max_concurrency: int | None = None,
    regex_enabled: bool = True,
) -> PageExtractionReport:
    """Regex (optional) + LLM + merge for a single page.

    Args:
        content: Scraped text for the page.
        all_keywords: Full known keyword list. Defaults to ``KEYWORDS``.
        top_k: Number of keywords selected by the regex pre-pass (ignored
            when ``regex_enabled=False``).
        n_chunks: How many chunks to split the text into.
        provider: LLM provider key (key in config.yaml).
        max_concurrency: Maximum concurrent LLM requests. If ``None``
            (default), the value is read from the provider config
            (falling back to 1 if absent). Ollama-style local backends
            should keep this at 1; cloud providers can use more.
        regex_enabled: If False, the regex pre-pass is skipped. The LLM
            receives the full keyword list and ``regex_keywords`` in the
            returned report is empty.

    Returns:
        ``PageExtractionReport`` with the merged metadata, per-chunk
        results, regex contribution, and discarded keywords.
    """
    start = time.perf_counter()

    if regex_enabled:
        counts = count_keyword_occurrences(content, all_keywords)
        top, remaining = split_keywords(counts, all_keywords, k=top_k)
        logger.info(
            "Regex enabled: selected %d top keyword(s) %s; %d candidates left for LLM",
            len(top),
            top,
            len(remaining),
        )
    else:
        top, remaining = [], list(all_keywords)
        logger.info(
            "Regex disabled: sending full keyword list (%d entries) to LLM",
            len(remaining),
        )

    chunks = chunk_text(content, n_chunks=n_chunks)
    chunk_results = await analyze_chunks_async(
        chunks,
        keywords=remaining,
        provider=provider,
        max_concurrency=max_concurrency,
    )

    merged, discarded = merge_chunk_results(
        chunk_results, regex_keywords=top, known_keywords=all_keywords
    )

    return PageExtractionReport(
        merged=merged,
        chunks=chunk_results,
        regex_keywords=top,
        discarded_keywords=discarded,
        extraction_seconds=time.perf_counter() - start,
    )


# ============================================================================
# Entry point: regex + LLM pipeline
# ============================================================================
if __name__ == "__main__":
    from scraper import scrape_site_to_dict

    logging.basicConfig(level=logging.INFO)

    target_url = "https://alan-turing-institute.github.io/rse-course/html/index.html"
    provider = os.environ.get("PROVIDER")

    async def main() -> None:
        scraped = await scrape_site_to_dict(target_url, single_page=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        all_results: dict[str, dict] = {}
        for url, content in scraped.items():
            logger.info("Processing %s (%d chars)", url, len(content))
            report = await extract_page_metadata(
                content,
                top_k=10,
                n_chunks=2,
                provider=provider,
                regex_enabled=True,
            )
            all_results[url] = report.model_dump()

        filename = f"pipeline_results_{timestamp}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        logger.info("Saved final results to %s", filename)

    asyncio.run(main())
