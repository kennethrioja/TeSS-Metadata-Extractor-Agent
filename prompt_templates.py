"""Prompt templates for the LLM metadata extractor.

Designed to be robust with small models (7B-class, Ollama-hosted). Key choices:

- One language throughout (English). Mixing languages between system and
  user messages noticeably degrades small models.
- Sections are delimited with markdown headers and XML tags so the model
  can locate each block even with weak attention. The text-to-analyse and
  the allowed-keywords list are wrapped explicitly.
- The closed-vocabulary constraint on the `keywords` field is stated
  redundantly ("copy verbatim", "do not invent", "do not paraphrase").
  Post-pipeline validation filters invented keywords as a safety net.
- The final cue ("Now produce the JSON object.") exploits recency bias to
  re-anchor the task after a potentially long text block.
- The JSON-output rules don't dwell on syntax — the structured-output
  layer enforces the schema. The prompt focuses on semantic rules.
"""

SYSTEM_PROMPT = (
    "You are a metadata-extraction assistant. You read a training-material "
    "web page and return a single JSON object that fits the provided schema. "
    'If a field is not in the text, you return the exact string "Not found". '
    "You never invent information."
)


PROMPT_TEMPLATE = """\
Extract metadata from the training-material text below and return it as a JSON object.

## Output rules

1. Return exactly ONE JSON object. No markdown fences, no commentary, no preamble, no trailing text.
2. If information for a field (except for dates) is not in the text, set that field to the exact string "Not found".
4. List-typed fields must be JSON arrays of strings. Use [] only when no item applies.

## Date fields – strict rule

Dates MUST use the format "YYYY-MM-DD", if the information is not in the text, you MUST set that field to an empty string (i.e., "").

## Licence field – strict rule

Licence MUST follow SPDX standardized short identifier AND NOT the human readable format, e.g. it must be CC-BY-4.0 AND NOT Creative Commons Attribution 4.0 International

## Keywords field — strict rules

The `keywords` field must contain ONLY entries copied verbatim from the allowed list below.

- Do not invent keywords.
- Do not paraphrase keywords.
- Do not translate keywords.
- Copy each selected keyword exactly as it appears in the list (same spelling, same case, same punctuation).
- Select only keywords whose topic is clearly present in the text.
- If no keyword from the list applies, return [].

<allowed_keywords>
{keywords}
</allowed_keywords>

## Text to analyze

<text>
{scraped_text}
</text>

Now produce the JSON object.
"""
