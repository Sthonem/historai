import json
import logging
from json import JSONDecodeError

from core.llm import llm_call

logger = logging.getLogger(__name__)


def _extract_json_array(text: str) -> list[dict]:
    """Best-effort extraction of a JSON array from an LLM response."""
    try:
        return json.loads(text)
    except JSONDecodeError:
        start = text.find("[")
        end = text.rfind("]") + 1
        if start == -1 or end <= start:
            raise
        return json.loads(text[start:end])


def generate_actors(question: str) -> list[dict]:
    prompt = f"""
You are a historical analysis expert.

Given this what-if historical question: "{question}"

Generate 6-8 key historical actors who would be most relevant to this scenario.
For each actor provide:
- name: their real historical name
- role: their position/title at the time
- motivation: their primary goal or interest (1 sentence)
- influence: their power level from 1-10
- faction: which side/group they represent

Return ONLY a valid JSON array, no explanation, no markdown, no backticks.

Example format:
[
  {{
    "name": "Sultan Mehmed V",
    "role": "Ottoman Sultan",
    "motivation": "Preserve the Ottoman Empire and maintain his throne",
    "influence": 8,
    "faction": "Ottoman Leadership"
  }}
]
"""
    response = llm_call(
        prompt,
        system="You are a historical analysis expert. Always respond with valid JSON only.",
        max_tokens=900,
    )

    actors = _extract_json_array(response)

    normalized: list[dict] = []
    for actor in actors:
        if not isinstance(actor, dict):
            continue
        try:
            influence = int(actor.get("influence", 5))
        except (TypeError, ValueError):
            influence = 5
        normalized.append(
            {
                "name": str(actor.get("name", "Unknown")),
                "role": str(actor.get("role", "Unknown")),
                "motivation": str(actor.get("motivation", "")),
                "influence": max(1, min(10, influence)),
                "faction": str(actor.get("faction", "Unaligned")),
            }
        )
    return normalized
