"""
regex_extractor.py

Premier passage d'extraction de mots-clés via regex.

Complémentaire à `llm_extractor.py`: rapide, déterministe, sans coût de tokens,
et scale linéairement avec la taille du texte (pas de fenêtre de contexte).

Pipeline visé:
    1. (Ici) compter les occurrences des mots-clés candidats sur le texte complet
       et sélectionner les top_k présents textuellement.
    2. Passer la liste *restante* au LLM (par chunks) pour récupérer les
       mots-clés sémantiques que le regex ne peut pas attraper.
    3. Fusionner les deux ensembles dans le champ `keywords` du
       MaterialMetadata final.
"""

import json
import logging
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)
KEYWORDS_PATH = Path(__file__).parent / "known_keywords.json"


def load_keywords(path: Path = KEYWORDS_PATH) -> list[str]:
    with open(path, "r", encoding="utf-8") as f_in:
        data = json.load(f_in)
    return data["ai_filtered_keywords"]


def build_pattern(keyword: str) -> str:
    """Build a robust boundary pattern for a single keyword.

    - Splits the keyword on whitespace so re.escape never touches a space
      (re.escape in 3.7+ adds a backslash before whitespace, which
      breaks naive \\s+ substitution).
    - Joins tokens with \\s+ so multi-word keywords still match across
      line breaks and double spaces.
    - Uses \\b at alphanumeric edges, (?<!\\w) / (?!\\w) otherwise, so
      keywords like 'c++', '.net', 'c#' get correct boundaries.
    """
    tokens = keyword.split()
    if not tokens:
        return ""
    escaped = r"\s+".join(re.escape(t) for t in tokens)

    left = r"\b" if keyword[:1].isalnum() or keyword[:1] == "_" else r"(?<!\w)"
    right = r"\b" if keyword[-1:].isalnum() or keyword[-1:] == "_" else r"(?!\w)"
    return left + escaped + right


@lru_cache(maxsize=4096)
def _compile(keyword: str, case_insensitive: bool) -> re.Pattern:
    flags = re.IGNORECASE if case_insensitive else 0
    return re.compile(build_pattern(keyword), flags)


def count_keyword_occurrences(
    text: str,
    keywords: list[str],
    case_insensitive: bool = True,
) -> Counter:
    counts: Counter = Counter()
    for kw in keywords:
        if not kw:
            continue
        matches = _compile(kw, case_insensitive).findall(text)
        if matches:
            counts[kw] = len(matches)
    return counts


def split_keywords(
    counts: Counter,
    all_keywords: list[str],
    k: int = 10,
) -> tuple[list[str], list[str]]:
    selected = [kw for kw, _ in counts.most_common(k)]
    selected_set = set(selected)
    remaining = [kw for kw in all_keywords if kw not in selected_set]
    return selected, remaining


# Execution
if __name__ == "__main__":
    import asyncio
    from time import time
    from datetime import datetime

    from scraper import scrape_site_to_dict

    logging.basicConfig(level=logging.INFO)

    target_url = "https://alan-turing-institute.github.io/rse-course/html/index.html"
    scraped_content = asyncio.run(scrape_site_to_dict(target_url, single_page=True))
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    keywords = load_keywords()
    logger.info("Loaded %d candidate keywords", len(keywords))

    for url, content in scraped_content.items():
        print(f"URL: {url} | Content size: {len(content)} characters")

        # Pas besoin de chunks: regex traite le texte complet en une passe.
        start = time()
        counts = count_keyword_occurrences(content, keywords)
        delta = time() - start

        selected, remaining = split_keywords(counts, keywords, k=100)

        print(f"Regex extraction completed in {delta:.4f} seconds")
        print(f"Matched {len(counts)} / {len(keywords)} candidate keywords")
        print("Top 10 selected:")
        for kw in selected:
            print(f"  - {kw} ({counts[kw]} occurrences)")

        # Sauvegarde pour le second passage LLM.
        filename = f"regex_results_{timestamp}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "url": url,
                    "execution_time": delta,
                    "top_keywords": selected,
                    "all_counts": dict(counts.most_common()),
                    "remaining_keywords": remaining,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        print(f"Saved to {filename}")
