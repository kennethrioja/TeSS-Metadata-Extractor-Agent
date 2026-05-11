from openai import OpenAI
import os
import logging
logger = logging.getLogger(__name__)
from dotenv import load_dotenv
import json
load_dotenv()

MODEL = "gemma4" #'AI4EOSC/Qwen/Qwen3-14B'
TEMPERATURE = 0.0

def load_keywords():
    with open('./known_keywords.json') as f_in:
        data = json.load(f_in)
        
    return data["keywords"]

def analyze_content_with_llm(
    content: str,
    keywords: list[str],
    provider: str = "eosc",
) -> dict:
    """
    Effectue une correspondance sémantique entre une liste de mots-clés et
    un contenu textuel via un LLM compatible avec l'API OpenAI.

    Returns:
        Un dict JSON-sérialisable de la forme :
        {
            "provider": str,
            "model": str,
            "content_length": int,
            "found_keywords": list[str]   # toujours en dernier
        }
    """
    
    logger.info("Appel API — provider=%s, model=%s", provider, MODEL )

    # Schéma JSON strict (utilisé si le provider le supporte).
    json_schema = {
        "name": "keyword_match_result",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "found_keywords": {
                    "type": "array",
                    "description": (
                        "Sous-ensemble de la liste source de mots-clés correspondant "
                        "sémantiquement au contenu. Strictement issus de la liste source."
                    ),
                    "items": {"type": "string", "enum": keywords},
                }
            },
            "required": ["found_keywords"],
            "additionalProperties": False,
        },
    }

    system_prompt = (
        "Vous êtes un expert en analyse académique de corpus textuels. Votre tâche "
        "est de croiser une liste de mots-clés prédéfinis avec un texte source et "
        "d'identifier les correspondances thématiques et sémantiques.\n\n"
        f"Mots-clés source : {', '.join(keywords)}.\n\n"
        "INSTRUCTIONS STRICTES :\n"
        "1. Lisez attentivement le CONTEXTE.\n"
        "2. Retournez UN SEUL objet JSON avec la clé 'found_keywords'.\n"
        "3. N'incluez QUE des mots-clés strictement issus de la liste source.\n"
        "4. Utilisez la correspondance sémantique, pas seulement lexicale.\n"
        "5. Si aucun mot-clé ne correspond, retournez une liste vide."
    )

    user_message = (
        "Analysez le contenu suivant et retournez la liste des mots-clés "
        f"correspondants.\n\nCONTEXTE:\n---\n{content}\n---"
    )

    client = OpenAI(
        api_key=os.environ.get('EOSC_API_KEY', 'ollama'),
        base_url="http://localhost:11434/v1" ## 'https://vllm.cloud.ai4eosc.eu',
    )

    # On tente le mode strict, puis on retombe sur json_object (mieux supporté par Ollama).
    response_formats = [
        {"type": "json_schema", "json_schema": json_schema},
        {"type": "json_object"},
    ]

    keywords_set = set(keywords)
    last_error: Exception | None = None

    for fmt in response_formats:
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.0,
                response_format=fmt,
            )

            raw = response.choices[0].message.content or "{}"
            parsed = json.loads(raw)
            found = parsed.get("found_keywords", []) or []

            # Garde-fou : on ne conserve que les mots-clés réellement issus de la liste source.
            found_keywords = [kw for kw in found if kw in keywords_set]

            logger.info("✅ %d mot(s)-clé(s) trouvé(s).", len(found_keywords))
            return {
                "provider": provider,
                "model": MODEL,
                "content_length": len(content),
                "found_keywords": found_keywords,  # placé en dernier
            }

        except (json.JSONDecodeError, Exception) as e:
            last_error = e
            logger.warning("Échec avec response_format=%s : %s", fmt["type"], e)
            continue

    logger.error("🚨 Échec définitif de l'analyse : %s", last_error)
    return {
        "provider": provider,
        "model": MODEL,
        "content_length": len(content),
        "error": str(last_error) if last_error else "unknown",
        "found_keywords": [],
    }


# Exécution
if __name__ == "__main__":
    import asyncio
    from scraper import scrape_site_to_dict
    url_cible = "https://carpentries-incubator.github.io/python-intermediate-development/"
    contenu_final = asyncio.run(scrape_site_to_dict(url_cible))

    keywords = load_keywords()
    # Aperçu
    for url, content in contenu_final.items():
        print(f"URL: {url} | Taille contenu: {len(content)} caractères")
        results = analyze_content_with_llm(content=content, keywords=keywords)
        print(results)
        break 