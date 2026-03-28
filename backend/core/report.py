from core.llm import llm_call

def generate_report(simulation_result: dict) -> dict:
    question = simulation_result["question"]
    actors = simulation_result["actors"]
    turns = simulation_result["turns"]
    final_world_state = simulation_result["final_world_state"]

    turns_summary = ""
    for turn in turns:
        turns_summary += f"\n[Turn {turn['turn']}]"
        if turn["event"]:
            turns_summary += f"\nUnexpected event: {turn['event']}"
        for actor_name, decision in turn["decisions"].items():
            turns_summary += f"\n{actor_name}: {decision[:150]}..."

    narrative_prompt = f"""
You are a historian analyzing an alternate history simulation.

Original question: {question}

The simulation ran for {len(turns)} turns. Here is what happened:
{turns_summary}

Write a compelling 3-4 paragraph narrative report answering:
1. What would most likely have happened in this alternate timeline?
2. What were the key turning points?
3. How would history have been different?

Write in a confident, engaging historical style.
"""

    narrative = llm_call(
        narrative_prompt,
        system="You are a brilliant historian writing an engaging alternate history analysis."
    )

    actor_cards = []
    for actor in actors:
        actor_decisions = []
        for turn in turns:
            if actor["name"] in turn["decisions"]:
                actor_decisions.append(turn["decisions"][actor["name"]])

        card_prompt = f"""
Summarize {actor['name']}'s role in this alternate history simulation in 2-3 sentences.
Their decisions were:
{chr(10).join(actor_decisions)}

Focus on: how they responded, what they tried to achieve, how they evolved across the simulation.
"""
        summary = llm_call(
            card_prompt,
            system="You are a historian writing concise actor summaries."
        )

        actor_cards.append({
            "name": actor["name"],
            "role": actor["role"],
            "faction": actor["faction"],
            "influence": actor["influence"],
            "summary": summary
        })

    return {
        "question": question,
        "narrative": narrative,
        "actor_cards": actor_cards
    }