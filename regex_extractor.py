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
from pathlib import Path

logger = logging.getLogger(__name__)

KEYWORDS_PATH = Path(__file__).parent / "known_keywords.json"


def load_keywords(path: Path = KEYWORDS_PATH) -> list[str]:
    """Charge la liste de mots-clés depuis le JSON (même source que llm_extractor)."""
    with open(path, "r", encoding="utf-8") as f_in:
        data = json.load(f_in)
    return data["ai_filtered_keywords"]


def count_keyword_occurrences(
    text: str,
    keywords: list[str],
    case_insensitive: bool = True,
) -> Counter:
    """Compte les occurrences de chaque mot-clé dans le texte.

    Utilise des limites de mot (``\\b``) pour éviter les correspondances
    partielles (« java » ne sera pas trouvé dans « javascript »).
    Les mots-clés multi-mots (« machine learning ») sont gérés via
    ``re.escape`` qui préserve les espaces et échappe les caractères spéciaux.

    Args:
        text: Texte source dans lequel chercher.
        keywords: Liste de mots-clés candidats.
        case_insensitive: Recherche insensible à la casse (défaut: True).

    Returns:
        Counter ne contenant que les mots-clés avec au moins une occurrence.
        L'absence d'un mot-clé dans le résultat signifie ``count == 0``.
    """
    flags = re.IGNORECASE if case_insensitive else 0
    counts: Counter = Counter()
    for kw in keywords:
        if not kw:
            continue
        pattern = r"\b" + re.escape(kw) + r"\b"
        matches = re.findall(pattern, text, flags=flags)
        if matches:
            counts[kw] = len(matches)
    return counts


def top_k_keywords(
    text: str,
    keywords: list[str],
    k: int = 10,
) -> list[str]:
    """Retourne les k mots-clés les plus fréquents dans le texte.

    Wrapper de convenance autour de ``count_keyword_occurrences``.

    Args:
        text: Texte source.
        keywords: Liste de mots-clés candidats.
        k: Nombre maximum de mots-clés à retourner.

    Returns:
        Liste de mots-clés triée par fréquence décroissante (≤ k éléments).
    """
    return [kw for kw, _ in count_keyword_occurrences(text, keywords).most_common(k)]


def split_keywords(
    counts: Counter,
    all_keywords: list[str],
    k: int = 10,
) -> tuple[list[str], list[str]]:
    """Sépare la liste complète en (top_k regex, candidats restants pour le LLM).

    Le second passage LLM ne devrait recevoir que ``remaining`` — pas la
    liste complète — pour éviter qu'il « redécouvre » ce que le regex a
    déjà confirmé, et pour réduire la pression sur les petits modèles.

    Args:
        counts: Compteur retourné par ``count_keyword_occurrences``.
        all_keywords: Liste complète des mots-clés candidats.
        k: Taille du top à sélectionner.

    Returns:
        Tuple ``(selected, remaining)``:
          - ``selected``: top_k mots-clés trouvés par regex, triés par fréquence.
          - ``remaining``: mots-clés candidats non sélectionnés (à passer au LLM).
    """
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

        selected, remaining = split_keywords(counts, keywords, k=50)

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
