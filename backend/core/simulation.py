import logging
import random

from core.llm import llm_call

logger = logging.getLogger(__name__)

RANDOM_EVENTS = [
    "A major economic crisis is emerging in Europe.",
    "A significant military movement has been reported on the borders.",
    "A diplomatic message has been intercepted.",
    "Public unrest is growing in the capital.",
    "A natural disaster has struck a key region.",
    "A secret meeting between two factions has taken place.",
    "A key military commander has fallen ill.",
    "New intelligence reports have changed the strategic picture.",
]

DEFAULT_TURNS = 6
EVENT_PROBABILITY = 0.3
MEMORY_WINDOW = 5


def run_actor_decision(actor: dict, world_state: str, memory: list[str]) -> str:
    memory_text = "\n".join(memory[-MEMORY_WINDOW:]) if memory else "No previous actions."

    prompt = f"""
You are {actor['name']}, {actor['role']} during this historical scenario.

Your motivation: {actor['motivation']}
Your faction: {actor['faction']}
Your influence (1-10): {actor['influence']}

Recent history:
{memory_text}

Current situation:
{world_state}

What do you do and say in response to the current situation?
Respond in 2-3 sentences, in first person, as {actor['name']}.
Be specific and historically consistent.
"""
    return llm_call(
        prompt,
        system=f"You are {actor['name']}, a historical figure. Respond authentically in first person.",
    )


def run_simulation(question: str, actors: list[dict], turns: int = DEFAULT_TURNS) -> dict:
    world_state = f"""
Historical what-if scenario: {question}

The divergence point has just occurred. History has changed.
Key actors are now responding to this new reality.
"""

    memories: dict[str, list[str]] = {actor["name"]: [] for actor in actors}
    all_turns: list[dict] = []

    actors_sorted = sorted(actors, key=lambda a: a["influence"], reverse=True)

    for turn_num in range(1, turns + 1):
        turn_data: dict = {
            "turn": turn_num,
            "world_state": world_state,
            "decisions": {},
            "event": None,
        }

        if random.random() < EVENT_PROBABILITY:
            event = random.choice(RANDOM_EVENTS)
            world_state += f"\n[Unexpected event: {event}]"
            turn_data["event"] = event

        for actor in actors_sorted:
            try:
                decision = run_actor_decision(actor, world_state, memories[actor["name"]])
            except Exception as exc:
                logger.warning("Actor %s decision failed: %s", actor["name"], exc)
                decision = "(No response — communication lines disrupted.)"
            turn_data["decisions"][actor["name"]] = decision
            memories[actor["name"]].append(f"Turn {turn_num}: {decision}")

        influence_map = {a["name"]: a["influence"] for a in actors}
        decisions_summary = "\n".join(
            f"- {name} (influence {influence_map.get(name, '?')}): {decision[:100]}..."
            for name, decision in turn_data["decisions"].items()
        )

        world_state += f"\n\n[Turn {turn_num} Summary]\n{decisions_summary}"
        all_turns.append(turn_data)

    return {
        "question": question,
        "actors": actors,
        "turns": all_turns,
        "final_world_state": world_state,
    }
