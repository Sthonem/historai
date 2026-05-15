import logging
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional

from core.llm import llm_call

logger = logging.getLogger(__name__)

EventCallback = Callable[[dict], None]


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

# How many past turn summaries to keep in the world state for each actor prompt.
# Older summaries are dropped so the prompt stays roughly constant in size
# regardless of how many turns have passed.
WORLD_STATE_WINDOW = 2

# Per-actor memory window (in turns). Each actor only remembers their last
# few actions; this keeps the per-call prompt compact.
ACTOR_MEMORY_WINDOW = 3

ACTOR_DECISION_MAX_TOKENS = 220


def _emit(callback: Optional[EventCallback], event_type: str, **payload) -> None:
    if callback is None:
        return
    try:
        callback({"type": event_type, **payload})
    except Exception:
        logger.exception("Event callback failed for type=%s", event_type)


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
            quote = decision.strip()[:220].rstrip()
            if len(decision) > 220:
                quote += "..."
        elif idx < 4:
            quote = decision.strip()[:140].rstrip() + ("..." if len(decision) > 140 else "")
        else:
            quote = decision.strip()[:70].rstrip() + ("..." if len(decision) > 70 else "")
        lines.append(f"- {name} (infl {influence}): {quote}")
    return f"[Turn {turn_num} — by influence]\n" + "\n".join(lines)


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


def _build_world_state(
    base: str,
    recent_summaries: list[str],
    current_event: Optional[str],
) -> str:
    parts = [base.strip()]
    if recent_summaries:
        parts.append("\n\n".join(recent_summaries[-WORLD_STATE_WINDOW:]))
    if current_event:
        parts.append(f"[Unexpected event this turn: {current_event}]")
    return "\n\n".join(parts)


def run_actor_decision(
    actor: dict,
    world_state: str,
    memory: list[str],
    rank: int,
    total: int,
) -> str:
    memory_text = (
        "\n".join(memory[-ACTOR_MEMORY_WINDOW:]) if memory else "No previous actions."
    )
    label = _influence_label(rank, total, actor["influence"])

    prompt = f"""You are {actor['name']}, {actor['role']}.

Motivation: {actor['motivation']}
Faction: {actor['faction']}
Standing: {label}

Recent personal moves:
{memory_text}

Current situation:
{world_state}

In 2-3 sentences, first-person, respond. Be specific and let your power level
shape your tone: high-influence actors give orders, mid-tier maneuver,
low-influence plead, scheme, or rally support."""
    return llm_call(
        prompt,
        system=f"You are {actor['name']}. Respond authentically in first person, 2-3 sentences.",
        max_tokens=ACTOR_DECISION_MAX_TOKENS,
    )


def _run_actors_parallel(
    actors_sorted: list[dict],
    world_state: str,
    memories: dict[str, list[str]],
    turn_num: int,
    on_event: Optional[EventCallback],
) -> dict[str, str]:
    """Run all actor decisions for a turn concurrently.

    Each call is I/O-bound (LLM HTTP request) so a thread pool gives a near
    linear wall-clock win. Streaming events (``actor_thinking`` /
    ``actor_decided``) fire as the futures progress.
    """
    total = len(actors_sorted)
    decisions: dict[str, str] = {}

    for actor in actors_sorted:
        _emit(on_event, "actor_thinking", turn=turn_num, actor=actor["name"])

    with ThreadPoolExecutor(max_workers=min(8, max(1, total))) as pool:
        futures = {}
        for rank, actor in enumerate(actors_sorted):
            future = pool.submit(
                run_actor_decision,
                actor,
                world_state,
                memories[actor["name"]],
                rank,
                total,
            )
            futures[future] = actor

        for future in as_completed(futures):
            actor = futures[future]
            try:
                decision = future.result()
            except Exception as exc:
                logger.warning("Actor %s decision failed: %s", actor["name"], exc)
                decision = "(No response — communication lines disrupted.)"
            decisions[actor["name"]] = decision
            _emit(
                on_event,
                "actor_decided",
                turn=turn_num,
                actor=actor["name"],
                decision=decision,
            )

    return decisions


def run_simulation(
    question: str,
    actors: list[dict],
    turns: int = DEFAULT_TURNS,
    on_event: Optional[EventCallback] = None,
) -> dict:
    """Run the multi-turn simulation, optionally streaming progress via ``on_event``.

    Actor decisions within a turn run concurrently. The world-state summary
    fed back into each prompt is windowed (last ``WORLD_STATE_WINDOW`` turns)
    so prompts stay roughly constant in size across the simulation.
    """

    world_state_base = (
        f"Historical what-if scenario: {question}\n\n"
        "The divergence point has just occurred. History has changed.\n"
        "Key actors are now responding to this new reality."
    )

    memories: dict[str, list[str]] = {actor["name"]: [] for actor in actors}
    recent_summaries: list[str] = []
    all_turns: list[dict] = []

    actors_sorted = sorted(actors, key=lambda a: a["influence"], reverse=True)
    event_probability, event_pool = _event_probability(actors_sorted)
    pool_label = (
        "concentrated"
        if event_pool is RANDOM_EVENTS_CONCENTRATED
        else "unstable"
        if event_pool is RANDOM_EVENTS_UNSTABLE
        else "general"
    )
    logger.info(
        "Simulation event probability=%.2f pool=%s",
        event_probability,
        pool_label,
    )

    _emit(on_event, "simulation_started", question=question, turns=turns, actors=actors_sorted)

    for turn_num in range(1, turns + 1):
        _emit(on_event, "turn_started", turn=turn_num)

        event = None
        if random.random() < event_probability:
            event = random.choice(event_pool)
            _emit(on_event, "event_injected", turn=turn_num, event=event)

        world_state = _build_world_state(world_state_base, recent_summaries, event)

        decisions = _run_actors_parallel(
            actors_sorted, world_state, memories, turn_num, on_event
        )

        for name, decision in decisions.items():
            memories[name].append(f"T{turn_num}: {decision[:160]}")

        summary = _world_state_summary(turn_num, decisions, actors_sorted)
        recent_summaries.append(summary)
        if len(recent_summaries) > WORLD_STATE_WINDOW:
            recent_summaries.pop(0)

        turn_data = {
            "turn": turn_num,
            "decisions": decisions,
            "event": event,
        }
        all_turns.append(turn_data)

        _emit(
            on_event,
            "turn_completed",
            turn=turn_num,
            decisions=decisions,
            event=event,
        )

    _emit(on_event, "simulation_completed", turns=turns)

    return {
        "question": question,
        "actors": actors,
        "turns": all_turns,
        "final_world_state": _build_world_state(world_state_base, recent_summaries, None),
    }
