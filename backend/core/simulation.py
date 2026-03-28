import json
import random
from core.llm import llm_call

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

def run_actor_decision(actor: dict, world_state: str, memory: list[str]) -> str:
    memory_text = "\n".join(memory[-5:]) if memory else "No previous actions."
    
    prompt = f"""
You are {actor['name']}, {actor['role']} during this historical scenario.

Your motivation: {actor['motivation']}
Your faction: {actor['faction']}

Recent history:
{memory_text}

Current situation:
{world_state}

What do you do and say in response to the current situation?
Respond in 2-3 sentences, in first person, as {actor['name']}.
Be specific and historically consistent.
"""
    return llm_call(prompt, system=f"You are {actor['name']}, a historical figure. Respond authentically in first person.")

def run_simulation(question: str, actors: list[dict], turns: int = 12) -> dict:
    world_state = f"""
Historical what-if scenario: {question}

The divergence point has just occurred. History has changed.
Key actors are now responding to this new reality.
"""
    
    memories = {actor['name']: [] for actor in actors}
    all_turns = []

    for turn_num in range(1, turns + 1):
        turn_data = {
            "turn": turn_num,
            "world_state": world_state,
            "decisions": {},
            "event": None
        }

        if random.random() < 0.3:
            event = random.choice(RANDOM_EVENTS)
            world_state += f"\n[Unexpected event: {event}]"
            turn_data["event"] = event

        actors_sorted = sorted(actors, key=lambda x: x['influence'], reverse=True)

        for actor in actors_sorted:
            decision = run_actor_decision(actor, world_state, memories[actor['name']])
            turn_data["decisions"][actor['name']] = decision
            memories[actor['name']].append(f"Turn {turn_num}: {decision}")

        decisions_summary = "\n".join([
            f"- {name} (influence {next(a['influence'] for a in actors if a['name'] == name)}): {decision[:100]}..."
            for name, decision in turn_data["decisions"].items()
        ])
        
        world_state += f"\n\n[Turn {turn_num} Summary]\n{decisions_summary}"
        all_turns.append(turn_data)

    return {
        "question": question,
        "actors": actors,
        "turns": all_turns,
        "final_world_state": world_state
    }