"""Full metadata pipeline: keyword extraction + fields extraction on one scrape.

Scrapes the page once, then:
    1. Regex + (optional) LLM keyword classification on the content.
    2. Sleep `sleep_seconds` to avoid hitting per-minute rate limits.
    3. LLM fields extraction on the same content (chunked + merged).
    4. Attach the kept keywords to the merged fields under "keywords".

Notes:
    - `run_pipeline` from keyword_extraction_pipeline is NOT called here
      because it scrapes internally; we re-use its building blocks
      (`llm_inspect`, regex helpers) so we scrape exactly once.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import get_provider_config
from fields_extractor_pipeline import extract_page_metadata
from keyword_extraction_pipeline import llm_inspect
from regex_extractor import (
    count_keyword_occurrences,
    load_keywords,
    split_keywords,
)
from scraper import scrape_site_to_dict

logger = logging.getLogger(__name__)


async def get_all_metadata(
    url: str,
    *,
    top_k: int = 16,
    llm_activated: bool = True,
    batch_size: int = 8,
    provider: Optional[str] = None,
    n_chunks: int = 2,
    sleep_seconds: float = 4.0,
) -> dict:
    """Run keyword extraction and fields extraction over a single scrape.

    Args:
        url: Page to scrape.
        top_k: Keep the top-k regex-matched keywords as LLM candidates.
        llm_activated: If False, skip the LLM keyword classification and
            keep the regex top_k as-is.
        batch_size: Keywords per LLM classification call.
        provider: Provider key from config.yaml. ``None`` uses the default.
        n_chunks: Chunk count for the fields extractor.
        sleep_seconds: Pause between the keyword LLM pass and the fields
            LLM pass, to stay under per-minute rate limits.

    Returns:
        The merged ``MaterialMetadata`` as a dict, with the kept keywords
        attached under ``"keywords"``.
    """
    # 1. Scrape once. Both passes use this content.
    scraped = await scrape_site_to_dict(url, single_page=True)
    page_url, content = next(iter(scraped.items()))
    logger.info("Scraped %s | %d chars", page_url, len(content))

    # 2. Regex pass over the known keyword list.
    keywords = load_keywords()
    logger.info("Loaded %d candidate keywords", len(keywords))

    counts = count_keyword_occurrences(content, keywords)
    selected, _ = split_keywords(counts, keywords, k=top_k)
    logger.info(
        "Regex matched %d/%d candidates (top_k=%d)",
        len(counts),
        len(keywords),
        top_k,
    )

    # 3. Optional LLM classification of the regex top_k.
    if llm_activated:
        provider_cfg = get_provider_config(provider)
        logger.info(
            "LLM keyword inspection via provider=%s model=%s",
            provider_cfg.name,
            provider_cfg.model,
        )
        candidate_counts = {kw: counts[kw] for kw in selected}
        verdicts = await llm_inspect(
            content,
            candidate_counts,
            provider_cfg,
            batch_size=batch_size,
        )
        kept_keywords = [v["keyword"] for v in verdicts if v.get("is_core")]
        logger.info(
            "LLM kept %d / dropped %d",
            len(kept_keywords),
            len(verdicts) - len(kept_keywords),
        )
    else:
        kept_keywords = list(selected)

    # 4. Async pause to spare the rate-limit budget before the next LLM pass.
    if sleep_seconds > 0:
        logger.info("Sleeping %.1fs before fields extraction", sleep_seconds)
        await asyncio.sleep(sleep_seconds)

    # 5. Fields extraction on the same content.
    report = await extract_page_metadata(
        content=content,
        n_chunks=n_chunks,
        provider=provider,
    )
    fields_results: dict = report.model_dump().get("merged", {})

    # 6. Attach keywords to the merged fields.
    fields_results["keywords"] = kept_keywords
    return fields_results


def run_full_pipeline(target_url: str):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )

    TARGET_URL = target_url
    SAVE_RESULTS = False  # This allows to create a json in the src directory
    LLM_ACTIVATED = True
    TOP_K = 16
    BATCH_SIZE = 8
    N_CHUNKS = 3
    SLEEP_SECONDS = 4.0
    PROVIDER_NAME = os.environ.get("PROVIDER")  # None -> default in config.yaml

    results = asyncio.run(
        get_all_metadata(
            url=TARGET_URL,
            top_k=TOP_K,
            llm_activated=LLM_ACTIVATED,
            batch_size=BATCH_SIZE,
            provider=PROVIDER_NAME,
            n_chunks=N_CHUNKS,
            sleep_seconds=SLEEP_SECONDS,
        )
    )

    if SAVE_RESULTS:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        out_path = Path(f"full_metadata_pipeline_results_{timestamp}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nSaved to {out_path}")

    print(json.dumps(results, indent=2, ensure_ascii=False))

    return results


if __name__ == "__main__":
    run_full_pipeline(
        "https://alan-turing-institute.github.io/rse-course/html/index.html"
    )
