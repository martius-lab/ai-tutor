"""LLM-assisted concept generation for the Beta AI Tutor."""

from typing import cast

import decouple
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from aitutor.config import get_config


class GeneratedConcept(BaseModel):
    """One generated concept candidate."""

    concept_id: str
    label: str
    description: str
    core_points: list[str] = Field(default_factory=list)
    misconceptions: list[str] = Field(default_factory=list)


class GeneratedConceptsResponse(BaseModel):
    """Structured concept-generation response."""

    concepts: list[GeneratedConcept] = Field(default_factory=list)


async def generate_concepts_from_material(
    title: str,
    description: str,
    source_material_text: str,
    concept_target_count: int = 8,
    core_point_target_count: int = 4,
    misconception_target_count: int = 2,
) -> GeneratedConceptsResponse:
    """Generate a compact, professor-reviewable concept registry."""
    api_key = cast(str, decouple.config("OPENAI_API_KEY", cast=str, default=""))
    if api_key == "":
        raise ValueError("API key not found.")

    client = AsyncOpenAI(api_key=api_key)
    completion = await client.beta.chat.completions.parse(
        model=get_config().response_ai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You generate a compact, reviewable concept registry for a "
                    "university AI tutor. Return only structured data. Generate "
                    f"about {concept_target_count} concepts. Each concept must be "
                    "specific enough to be checked in a student answer. Use about "
                    f"{core_point_target_count} core points per concept and about "
                    f"{misconception_target_count} common misconceptions per "
                    "concept. Do not invent content unsupported by the material."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Exercise title: {title}\n\n"
                    f"Exercise description: {description}\n\n"
                    "Teaching material:\n"
                    f"{source_material_text[:200000]}"
                ),
            },
        ],
        response_format=GeneratedConceptsResponse,
    )

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ValueError("The model did not return valid concepts.")
    return parsed
