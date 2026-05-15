import json
import logging
from json import JSONDecodeError
from typing import Any

from core.llm import llm_call

logger = logging.getLogger(__name__)


NARRATIVE_MAX_TOKENS = 700
ACTOR_CARDS_MAX_TOKENS = 1200
MAP_MAX_TOKENS = 500


def _extract_json_object(text: str) -> dict:
    try:
        return json.loads(text)
    except JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end <= start:
            raise
        return json.loads(text[start:end])


def _extract_json_array(text: str) -> list:
    try:
        return json.loads(text)
    except JSONDecodeError:
        start = text.find("[")
        end = text.rfind("]") + 1
        if start == -1 or end <= start:
            raise
        return json.loads(text[start:end])


def generate_map_data(question: str, narrative: str) -> dict:
    prompt = f"""Alternate history scenario: "{question}"
Outcome: {narrative[:400]}

Return a JSON object showing territorial control. Use ONLY modern country names
(Turkey, not Ottoman Empire; Russia, not Soviet Union).

Format:
{{
  "factions": [
    {{"name": "...", "color": "red|blue|green|yellow|purple|orange", "countries": ["..."]}}
  ],
  "year": "approximate year"
}}

Rules: modern country names only, 5-8 countries per major faction, max 6 factions.
Return ONLY valid JSON, no markdown, no explanation."""
    response = llm_call(
        prompt,
        system="You are a historical cartographer. Return only valid JSON with modern country names.",
        max_tokens=MAP_MAX_TOKENS,
    )
    try:
        return _extract_json_object(response)
    except JSONDecodeError as exc:
        logger.warning("Map data JSON parse failed: %s", exc)
        return {"factions": [], "year": None}


def _build_turn_summary(turns: list[dict]) -> str:
    lines: list[str] = []
    for turn in turns:
        lines.append(f"\n[Turn {turn['turn']}]")
        if turn.get("event"):
            lines.append(f"Event: {turn['event']}")
        for actor_name, decision in turn["decisions"].items():
            snippet = decision[:120].rstrip()
            if len(decision) > 120:
                snippet += "..."
            lines.append(f"{actor_name}: {snippet}")
    return "\n".join(lines)


def _generate_actor_cards_bulk(actors: list[dict], turns: list[dict]) -> list[dict]:
    """Single-call summarization of every actor's arc, returned as JSON array.

    Falls back to a per-actor placeholder if the JSON parse fails. Saves
    ``len(actors) - 1`` LLM calls compared to the legacy implementation.
    """
    actor_blocks: list[str] = []
    for actor in actors:
        decisions = [
            turn["decisions"].get(actor["name"])
            for turn in turns
            if actor["name"] in turn["decisions"]
        ]
        decisions = [d for d in decisions if d]
        if not decisions:
            continue
        joined = "\n".join(
            f"- {d[:160].rstrip()}{'...' if len(d) > 160 else ''}" for d in decisions
        )
        actor_blocks.append(f"### {actor['name']} ({actor['faction']})\n{joined}")

    if not actor_blocks:
        return []

    prompt = f"""For each actor below, write a 2-3 sentence summary of their role in the
simulation: how they responded, what they tried to achieve, how they evolved.

Return a JSON array. Each item: {{ "name": "...", "summary": "..." }}.
Names must match exactly. Return ONLY the JSON array, no markdown, no preamble.

{chr(10).join(actor_blocks)}"""

    response = llm_call(
        prompt,
        system="You are a historian writing concise actor summaries. Return only valid JSON.",
        max_tokens=ACTOR_CARDS_MAX_TOKENS,
    )

    try:
        items = _extract_json_array(response)
    except JSONDecodeError as exc:
        logger.warning("Actor cards JSON parse failed: %s", exc)
        return []

    summaries: dict[str, str] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        summary = item.get("summary")
        if isinstance(name, str) and isinstance(summary, str):
            summaries[name.strip()] = summary.strip()
    return [{"name": name, "summary": summary} for name, summary in summaries.items()]


def generate_report(simulation_result: dict) -> dict:
    question = simulation_result["question"]
    actors = simulation_result["actors"]
    turns = simulation_result["turns"]

    turns_summary = _build_turn_summary(turns)

    narrative_prompt = f"""You are a historian analyzing an alternate history simulation.

Original question: {question}

The simulation ran for {len(turns)} turns. What happened:
{turns_summary}

Write a compelling 3-4 paragraph narrative answering:
1. What would most likely have happened in this alternate timeline?
2. What were the key turning points?
3. How would history have been different?

Write in a confident, engaging historical style."""

    narrative = llm_call(
        narrative_prompt,
        system="You are a brilliant historian writing an engaging alternate history analysis.",
        max_tokens=NARRATIVE_MAX_TOKENS,
    )

    bulk_summaries: dict[str, str] = {}
    try:
        for entry in _generate_actor_cards_bulk(actors, turns):
            bulk_summaries[entry["name"]] = entry["summary"]
    except Exception as exc:
        logger.warning("Bulk actor cards failed, falling back to placeholders: %s", exc)

    actor_cards: list[dict[str, Any]] = []
    for actor in actors:
        summary = bulk_summaries.get(actor["name"]) or "(Summary unavailable.)"
        actor_cards.append(
            {
                "name": actor["name"],
                "role": actor["role"],
                "faction": actor["faction"],
                "influence": actor["influence"],
                "summary": summary,
            }
        )

    map_data = generate_map_data(question, narrative)

    return {
        "question": question,
        "narrative": narrative,
        "actor_cards": actor_cards,
        "map_data": map_data,
    }
