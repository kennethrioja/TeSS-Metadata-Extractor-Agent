import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from time import time
from typing import Optional

from openai import AsyncOpenAI

from config import ProviderConfig, get_provider_config
from regex_extractor import (
    count_keyword_occurrences,
    load_keywords,
    split_keywords,
)
from scraper import scrape_site_to_dict

logger = logging.getLogger(__name__)

SYSTEM = (
    "You are a strict metadata classifier. "
    "You output only valid JSON matching the requested schema. No prose."
)

USER_TEMPLATE = """Decide if a keyword is a CORE TOPIC of the document below.

Rules:
- CORE = has its own section/chapter, OR is a recurring theme, OR is a tool actually used in the course.
- NOT CORE = appears only as a passing example, an alternative, or is too generic.
- Mentions inside a list of "other examples" (e.g. "languages like X, Y, Z") do NOT count as core.

Document:
\"\"\"{doc}\"\"\"

Keyword: "{kw}"
Occurrences in document: {count}

Think step by step in the "reasoning" field (max 25 words), then decide.
Respond ONLY with JSON of this exact shape:
{{"reasoning": "<short>", "evidence_quote": "<short quote from doc or empty>", "is_core": true|false}}"""


async def _classify_one(
    client: AsyncOpenAI,
    provider: ProviderConfig,
    doc: str,
    keyword: str,
    count: int,
    semaphore: asyncio.Semaphore,
) -> dict:
    async with semaphore:
        try:
            resp = await client.chat.completions.create(
                model=provider.model,
                temperature=provider.temperature,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM},
                    {
                        "role": "user",
                        "content": USER_TEMPLATE.format(
                            doc=doc, kw=keyword, count=count
                        ),
                    },
                ],
            )
            payload = json.loads(resp.choices[0].message.content)
            return {"keyword": keyword, "count": count, **payload}
        except Exception as e:
            logger.exception("LLM classification failed for '%s'", keyword)
            return {
                "keyword": keyword,
                "count": count,
                "reasoning": f"error: {e}",
                "evidence_quote": "",
                "is_core": False,
            }


BATCH_USER_TEMPLATE = """Decide which keywords are CORE TOPICS of the document below.

Rules:
- CORE = has its own section/chapter, OR is a recurring theme, OR is a tool actually used in the course.
- NOT CORE = appears only as a passing example, an alternative, or is too generic.
- Mentions inside a list of "other examples" (e.g. "languages like X, Y, Z") do NOT count as core.

Document:
\"\"\"{doc}\"\"\"

Classify EACH of these keywords. The number in parentheses is its occurrence count.
{keyword_list}

Respond ONLY with JSON of this exact shape, one entry per keyword, SAME ORDER:
{{"verdicts": [
  {{"keyword": "<kw>", "reasoning": "<max 15 words>", "is_core": true}},
  ...
]}}"""


async def _classify_batch(
    client: AsyncOpenAI,
    provider: ProviderConfig,
    doc: str,
    batch: list[tuple[str, int]],
    semaphore: asyncio.Semaphore,
) -> list[dict]:
    async with semaphore:
        kw_list = "\n".join(f'- "{kw}" (count: {c})' for kw, c in batch)
        try:
            resp = await client.chat.completions.create(
                model=provider.model,
                temperature=provider.temperature,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM},
                    {
                        "role": "user",
                        "content": BATCH_USER_TEMPLATE.format(
                            doc=doc,
                            keyword_list=kw_list,
                        ),
                    },
                ],
            )
            payload = json.loads(resp.choices[0].message.content)
            verdicts = payload.get("verdicts", [])
        except Exception as e:
            logger.exception("Batch of %d failed", len(batch))
            return [
                {
                    "keyword": kw,
                    "count": c,
                    "reasoning": f"error: {e}",
                    "is_core": False,
                }
                for kw, c in batch
            ]

        # Guard against models that drop or reorder entries.
        by_kw = {v.get("keyword"): v for v in verdicts if isinstance(v, dict)}
        out = []
        for kw, c in batch:
            v = by_kw.get(kw)
            if v is None:
                out.append(
                    {
                        "keyword": kw,
                        "count": c,
                        "reasoning": "missing from batch response",
                        "is_core": False,
                    }
                )
            else:
                out.append({**v, "count": c})
        return out


async def llm_inspect(
    document: str,
    keyword_counts: dict[str, int],
    provider: ProviderConfig,
    batch_size: int = 8,
) -> list[dict]:
    client = AsyncOpenAI(
        base_url=provider.base_url,
        api_key=provider.api_key or "ollama",
    )
    semaphore = asyncio.Semaphore(max(1, provider.max_concurrency))
    items = list(keyword_counts.items())
    batches = [items[i : i + batch_size] for i in range(0, len(items), batch_size)]
    results = await asyncio.gather(
        *[_classify_batch(client, provider, document, b, semaphore) for b in batches]
    )
    return [v for batch in results for v in batch]


async def run_pipeline(
    url: str,
    *,
    top_k: int = 50,
    llm_activated: bool = True,
    provider_name: Optional[str] = None,
    batch_size: int = 8,  # NEW
) -> dict:
    # 1. Scrape
    scraped = await scrape_site_to_dict(url, single_page=True)
    page_url, content = next(iter(scraped.items()))
    logger.info("Scraped %s | %d chars", page_url, len(content))

    # 2. Candidate keywords
    keywords = load_keywords()
    logger.info("Loaded %d candidate keywords", len(keywords))

    # 3. Regex pass
    start = time()
    counts = count_keyword_occurrences(content, keywords)
    regex_time = time() - start
    selected, remaining = split_keywords(counts, keywords, k=top_k)
    logger.info(
        "Regex matched %d/%d candidates in %.4fs (top_k=%d)",
        len(counts),
        len(keywords),
        regex_time,
        top_k,
    )

    result = {
        "url": page_url,
        "llm_activated": llm_activated,
        "regex": {
            "execution_time": regex_time,
            "matched_count": len(counts),
            "top_keywords": selected,
            "all_counts": dict(counts.most_common()),
            "remaining_keywords": remaining,
        },
    }

    # 4. LLM pass (optional)
    if llm_activated:
        provider = get_provider_config(provider_name)
        logger.info(
            "LLM inspection via provider=%s model=%s temp=%s concurrency=%d",
            provider.name,
            provider.model,
            provider.temperature,
            provider.max_concurrency,
        )

        # Only inspect what regex actually found.
        candidate_counts = {kw: counts[kw] for kw in selected}

        start = time()
        verdicts = await llm_inspect(
            content,
            candidate_counts,
            provider,
            batch_size=batch_size,  # NEW
        )
        llm_time = time() - start

        kept = [v["keyword"] for v in verdicts if v.get("is_core")]
        dropped = [v["keyword"] for v in verdicts if not v.get("is_core")]

        result["llm"] = {
            "execution_time": llm_time,
            "provider": provider.name,
            "model": provider.model,
            "verdicts": verdicts,
            "kept": kept,
            "dropped": dropped,
        }
        logger.info(
            "LLM kept %d / dropped %d in %.2fs", len(kept), len(dropped), llm_time
        )

    return result


# Execution
if __name__ == "__main__":
    import os
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )

    TARGET_URL = "https://alan-turing-institute.github.io/rse-course/html/index.html"
    LLM_ACTIVATED = True  # toggle this to skip the LLM pass
    TOP_K = 16
    BATCH_SIZE = 8  # keywords per LLM call; 8 is safe for 7B models
    PROVIDER_NAME = os.environ.get('PROVIDER')  # None -> default_provider from config.yaml

    result = asyncio.run(
        run_pipeline(
            url=TARGET_URL,
            top_k=TOP_K,
            llm_activated=LLM_ACTIVATED,
            provider_name=PROVIDER_NAME,
            batch_size=BATCH_SIZE,
        )
    )

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_path = Path(f"keywords_extraction_pipeline_results_{timestamp}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to {out_path}")

    print(f"\nRegex top-{TOP_K} ({len(result['regex']['top_keywords'])}):")
    for kw in result["regex"]["top_keywords"]:
        print(f"  - {kw} ({result['regex']['all_counts'][kw]})")

    if "llm" in result:
        print(f"\nLLM kept ({len(result['llm']['kept'])}):")
        for kw in result["llm"]["kept"]:
            print(f"  - {kw}")
        print(f"\nLLM dropped ({len(result['llm']['dropped'])}):")
        for kw in result["llm"]["dropped"]:
            print(f"  - {kw}")
