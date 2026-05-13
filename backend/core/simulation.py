import logging
import random

from core.llm import llm_call

logger = logging.getLogger(__name__)


RANDOM_EVENTS_GENERAL = [
    "A major economic crisis is emerging in Europe.",
    "A diplomatic message has been intercepted.",
    "A natural disaster has struck a key region.",
    "New intelligence reports have changed the strategic picture.",
    "A secret meeting between two factions has taken place.",
]

RANDOM_EVENTS_UNSTABLE = [
    "Public unrest is growing in the capital.",
    "A coup attempt has been narrowly averted.",
    "Soldiers are deserting on the frontier.",
    "Rival factions are arming civilians.",
    "Bread riots have broken out in major cities.",
]

RANDOM_EVENTS_CONCENTRATED = [
    "A significant military movement has been reported on the borders.",
    "A key military commander has fallen ill.",
    "A surprise offensive has been ordered.",
    "An ultimatum has been delivered to a rival power.",
    "A new alliance has been signed in secret.",
]


DEFAULT_TURNS = 6
BASE_EVENT_PROBABILITY = 0.25
MEMORY_WINDOW = 5


def _influence_label(rank: int, total: int, influence: int) -> str:
    if rank == 0:
        return "the most influential actor in this scenario"
    if rank < max(1, total // 3):
        return f"a top-tier power broker (influence {influence}/10)"
    if rank < (2 * total) // 3:
        return f"a mid-tier actor (influence {influence}/10)"
    return f"a lower-influence actor (influence {influence}/10) who must rely on cunning or alliance"


def _world_state_summary(turn_num: int, decisions: dict[str, str], actors: list[dict]) -> str:
    """Render the turn summary, weighting space by actor influence."""
    influence_map = {a["name"]: a["influence"] for a in actors}
    ordered = sorted(decisions.items(), key=lambda kv: influence_map.get(kv[0], 0), reverse=True)

    lines: list[str] = []
    for idx, (name, decision) in enumerate(ordered):
        influence = influence_map.get(name, 5)
        if idx < 2:
            quote = decision.strip()
        elif idx < 4:
            quote = decision.strip()[:180].rstrip() + ("..." if len(decision) > 180 else "")
        else:
            quote = decision.strip()[:80].rstrip() + ("..." if len(decision) > 80 else "")
        lines.append(f"- {name} (influence {influence}): {quote}")
    return f"[Turn {turn_num} Summary — ordered by influence]\n" + "\n".join(lines)


def _event_probability(actors: list[dict]) -> tuple[float, list[str]]:
    """Compute event probability and the pool to draw from, based on power distribution."""
    if not actors:
        return BASE_EVENT_PROBABILITY, RANDOM_EVENTS_GENERAL

    influences = [a["influence"] for a in actors]
    avg = sum(influences) / len(influences)
    peak = max(influences)
    spread = peak - avg

    probability = BASE_EVENT_PROBABILITY + min(0.25, 0.04 * spread)

    if spread >= 4:
        return probability, RANDOM_EVENTS_CONCENTRATED
    if avg <= 4.5:
        return probability, RANDOM_EVENTS_UNSTABLE
    return probability, RANDOM_EVENTS_GENERAL


def run_actor_decision(
    actor: dict,
    world_state: str,
    memory: list[str],
    rank: int,
    total: int,
) -> str:
    memory_text = "\n".join(memory[-MEMORY_WINDOW:]) if memory else "No previous actions."
    label = _influence_label(rank, total, actor["influence"])

    prompt = f"""
You are {actor['name']}, {actor['role']} during this historical scenario.

Your motivation: {actor['motivation']}
Your faction: {actor['faction']}
Your standing in this moment: {label}

Recent history:
{memory_text}

Current situation:
{world_state}

What do you do and say in response to the current situation?
Respond in 2-3 sentences, in first person, as {actor['name']}.
Be specific, historically consistent, and let your relative power shape your tone:
high-influence actors give orders, mid-tier actors maneuver, low-influence actors plead, scheme, or rally support.
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
    total_actors = len(actors_sorted)

    event_probability, event_pool = _event_probability(actors_sorted)
    logger.info(
        "Simulation event probability=%.2f pool=%s",
        event_probability,
        "concentrated" if event_pool is RANDOM_EVENTS_CONCENTRATED else "unstable" if event_pool is RANDOM_EVENTS_UNSTABLE else "general",
    )

    for turn_num in range(1, turns + 1):
        turn_data: dict = {
            "turn": turn_num,
            "world_state": world_state,
            "decisions": {},
            "event": None,
        }

        if random.random() < event_probability:
            event = random.choice(event_pool)
            world_state += f"\n[Unexpected event: {event}]"
            turn_data["event"] = event

        for rank, actor in enumerate(actors_sorted):
            try:
                decision = run_actor_decision(
                    actor,
                    world_state,
                    memories[actor["name"]],
                    rank=rank,
                    total=total_actors,
                )
            except Exception as exc:
                logger.warning("Actor %s decision failed: %s", actor["name"], exc)
                decision = "(No response — communication lines disrupted.)"
            turn_data["decisions"][actor["name"]] = decision
            memories[actor["name"]].append(f"Turn {turn_num}: {decision}")

        world_state += "\n\n" + _world_state_summary(turn_num, turn_data["decisions"], actors_sorted)
        all_turns.append(turn_data)

    return {
        "question": question,
        "actors": actors,
        "turns": all_turns,
        "final_world_state": world_state,
    }
