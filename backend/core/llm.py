import os
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def llm_call(prompt: str, system: str = "You are a helpful historical analysis assistant.") -> str:
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800,
            )
            return response.choices[0].message.content
        except Exception as e:
            if "rate_limit_exceeded" in str(e):
                wait = (attempt + 1) * 10
                print(f"Rate limit hit, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise e
    return "Unable to generate response due to rate limits."