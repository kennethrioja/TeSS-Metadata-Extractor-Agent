import json
import re
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",   # Ollama's OpenAI-compatible endpoint
    api_key="ollama",                        # required by the client, ignored by Ollama
)

MODEL = "gemma4"
TEMPERATURE = 0.0

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


def classify(doc: str, kw: str) -> dict:
    count = len(re.findall(re.escape(kw), doc, flags=re.IGNORECASE))

    # Cheap pre-filter: zero hits → never a core topic, skip the LLM call.
    if count == 0:
        return {"keyword": kw, "count": 0, "reasoning": "not present",
                "evidence_quote": "", "is_core": False}

    resp = client.chat.completions.create(
        model=MODEL,
        temperature=TEMPERATURE,
        response_format={"type": "json_object"},  # forces valid JSON output
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": USER_TEMPLATE.format(doc=doc, kw=kw, count=count)},
        ],
    )
    payload = json.loads(resp.choices[0].message.content)
    return {"keyword": kw, "count": count, **payload}


def filter_keywords(doc: str, keywords: list[str]) -> list[dict]:
    results = [classify(doc, kw) for kw in keywords]
    return [r for r in results if r["is_core"]]


if __name__ == "__main__":
    keywords = [
        "python", "module", "advanced", "git", "research software engineering",
        "software engineering", "testing", "version control", "c",
        "collaborative environment", "data analysis", "github", "packaging",
        "continuous integration", "debugging", "documentation", "intermediate",
        "jupyter", "matlab", "programming language", "r", "software project",
    ]
    with open("test_scrap.md", encoding="utf-8") as f:
        document = f.read()

    relevant = filter_keywords(document, keywords)
    print(json.dumps(relevant, indent=2, ensure_ascii=False))