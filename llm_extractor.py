import json
import logging
from pathlib import Path

from openai import OpenAI

from config import get_provider_config
from material_fields_llm_context import PROMPT_TEMPLATE
from schemas import MaterialMetadata

logger = logging.getLogger(__name__)

KEYWORDS_PATH = Path(__file__).parent / "known_keywords.json"

SYSTEM_PROMPT = (
    "Vous êtes un expert en analyse de corpus textuels. Votre tâche "
    "est de croiser une liste de mots-clés prédéfinis avec un texte source."
)


def load_keywords(path: Path = KEYWORDS_PATH) -> list[str]:
    with open(path, "r", encoding="utf-8") as f_in:
        data = json.load(f_in)
    return data["keywords"]


KEYWORDS = load_keywords()


def build_user_message(content: str, keywords: list[str] = KEYWORDS) -> str:
    """Build the user message by injecting keywords and scraped text into the prompt."""
    return PROMPT_TEMPLATE.format(
        keywords="\n".join(keywords),
        scraped_text=content,
    )


def analyze_content_with_llm(
    content: str,
    provider: str | None = None,
) -> MaterialMetadata:
    """
    Analyze scraped content using the LLM provider defined in config.yaml.
    Returns a validated MaterialMetadata object (structured output).

    Args:
        content: Raw scraped text to analyze.
        provider: Provider name (key in config.yaml). Falls back to default_provider.

    Returns:
        A MaterialMetadata Pydantic instance with all fields populated.
    """
    cfg = get_provider_config(provider)
    logger.info("Using provider '%s' with model '%s'", cfg.name, cfg.model)

    client = OpenAI(
        api_key=cfg.api_key,
        base_url=cfg.base_url,
    )

    user_message = build_user_message(content)

    completion = client.beta.chat.completions.parse(
        model=cfg.model,
        temperature=cfg.temperature,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format=MaterialMetadata,
    )

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ValueError(
            f"Model returned no parsable output. Refusal: "
            f"{completion.choices[0].message.refusal}"
        )

    return parsed


# Execution
if __name__ == "__main__":
    import asyncio

    from scraper import scrape_site_to_dict

    logging.basicConfig(level=logging.INFO)

    target_url = "https://carpentries-incubator.github.io/python-intermediate-development/"
    scraped_content = asyncio.run(
        scrape_site_to_dict(target_url, single_page=True)
    )

    for url, content in scraped_content.items():
        print(f"URL: {url} | Content size: {len(content)} characters")
        result = analyze_content_with_llm(content=content, provider="ollama")

        # result is a validated Pydantic object — full IDE autocomplete works
        print(f"Title: {result.name}")
        print(f"License: {result.license}")
        print(f"Status: {result.creativeWorkStatus}")
        print(f"Keywords: {result.keywords}")

        # Or dump the whole thing as JSON
        print(result.model_dump_json(indent=2))
        break