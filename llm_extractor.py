"""LLM-based metadata extractor.

Provides both a synchronous extractor (compatible with the previous API)
and an async extractor used by the chunked pipeline. The `keywords`
parameter lets callers narrow the candidate list — typically to the
"remaining" keywords produced by the regex pre-pass.

The ``__main__`` here is an **ablation harness**: it runs the full chunked,
async LLM pipeline with regex disabled (no top_k pre-selection, no
union at merge time). The output format is identical to ``pipeline.py``'s
output so the two JSONs are directly comparable.
"""

import json
import logging
import os
from pathlib import Path

from openai import AsyncOpenAI, OpenAI

from config import get_provider_config
from prompt_templates import PROMPT_TEMPLATE, SYSTEM_PROMPT
from schemas import MaterialMetadata

logger = logging.getLogger(__name__)

KEYWORDS_PATH = Path(__file__).parent / "known_keywords.json"


def load_keywords(path: Path = KEYWORDS_PATH) -> list[str]:
    with open(path, "r", encoding="utf-8") as f_in:
        data = json.load(f_in)
    return data["ai_filtered_keywords"]


KEYWORDS = load_keywords()


def build_user_message(content: str, keywords: list[str] = KEYWORDS) -> str:
    """Inject keywords list and scraped text into the prompt template."""
    return PROMPT_TEMPLATE.format(
        keywords="\n".join(keywords),
        scraped_text=content,
    )


def _parse_or_raise(completion) -> MaterialMetadata:
    """Extract the parsed pydantic object or raise with the refusal message."""
    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ValueError(
            "Model returned no parsable output. Refusal: "
            f"{completion.choices[0].message.refusal}"
        )
    return parsed


def analyze_content_with_llm(
    content: str,
    provider: str | None = None,
    keywords: list[str] = KEYWORDS,
) -> MaterialMetadata:
    """Synchronous single-chunk extraction."""
    cfg = get_provider_config(provider)
    logger.info("Using provider '%s' with model '%s'", cfg.name, cfg.model)

    client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)
    completion = client.beta.chat.completions.parse(
        model=cfg.model,
        temperature=cfg.temperature,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_message(content, keywords=keywords)},
        ],
        response_format=MaterialMetadata,
    )
    return _parse_or_raise(completion)


async def analyze_content_with_llm_async(
    content: str,
    provider: str | None = None,
    keywords: list[str] = KEYWORDS,
    client: AsyncOpenAI | None = None,
) -> MaterialMetadata:
    """Async single-chunk extraction.

    Accepts an optional pre-built ``client`` so the caller can share one
    connection pool across many concurrent extractions.
    """
    cfg = get_provider_config(provider)
    own_client = client is None
    if own_client:
        client = AsyncOpenAI(api_key=cfg.api_key, base_url=cfg.base_url)
    try:
        completion = await client.beta.chat.completions.parse(
            model=cfg.model,
            temperature=cfg.temperature,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": build_user_message(content, keywords=keywords),
                },
            ],
            response_format=MaterialMetadata,
        )
        return _parse_or_raise(completion)
    finally:
        if own_client:
            await client.close()


# ---------------------------------------------------------------------------
# Ablation entry point: LLM-only (regex disabled)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import asyncio
    from datetime import datetime

    # Local imports: avoid a top-level circular import with pipeline.py,
    # which already imports from this module.
    from fields_extractor_pipeline import extract_page_metadata
    from scraper import scrape_site_to_dict

    logging.basicConfig(level=logging.INFO)

    target_url = (
        "https://carpentries-incubator.github.io/python-intermediate-development/"
    )
    provider = os.environ.get("PROVIDER")

    async def main() -> None:
        scraped = await scrape_site_to_dict(target_url, single_page=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        all_results: dict[str, dict] = {}
        for url, content in scraped.items():
            logger.info("Processing %s (%d chars) — regex DISABLED", url, len(content))
            report = await extract_page_metadata(
                content,
                n_chunks=2,
                provider=provider,
                regex_enabled=False,
            )
            all_results[url] = report.model_dump()

        filename = f"llm_only_results_{timestamp}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        logger.info("Saved LLM-only results to %s", filename)

    asyncio.run(main())
