from openai import AsyncOpenAI
from config import get_provider_config
from pydantic import BaseModel, Field


class KeyWordsMetadata(BaseModel):
    """Structured metadata extracted from a training material web page."""
    # scientific_topics: str = Field(
    #     description="Scientific field of the material, following a certain ontology, by default from EDAM"
    # )
    keywords: list[str] = Field(description="Keywords that describe the material")
provider = "eosc"


cfg = get_provider_config(provider)


client = AsyncOpenAI(api_key=cfg.api_key, base_url=cfg.base_url)


async def main():
    completion = await client.beta.chat.completions.parse(
        model=cfg.model,
        temperature=cfg.temperature,
        messages=[
            {"role": "user", "content": "Hi"},
        ],
        response_format=KeyWordsMetadata,
    )
    return completion


if __name__ == "__main__":
    import asyncio

    result = asyncio.run(main())
    print(result)
