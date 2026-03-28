import json
from core.llm import llm_call

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
    response = llm_call(prompt, system="You are a historical analysis expert. Always respond with valid JSON only.")
    
    try:
        actors = json.loads(response)
        return actors
    except json.JSONDecodeError:
        start = response.find('[')
        end = response.rfind(']') + 1
        actors = json.loads(response[start:end])
        return actors