import os
import time
from groq import Groq
from google import genai
from dotenv import load_dotenv

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def llm_call_groq(prompt: str, system: str) -> str:
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=800,
    )
    return response.choices[0].message.content

def llm_call_gemini(prompt: str, system: str) -> str:
    full_prompt = f"{system}\n\n{prompt}"
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=full_prompt
    )
    return response.text

def llm_call(prompt: str, system: str = "You are a helpful historical analysis assistant.") -> str:
    for attempt in range(2):
        try:
            return llm_call_groq(prompt, system)
        except Exception as e:
            if "rate_limit_exceeded" in str(e):
                if attempt == 0:
                    print("Groq rate limit, waiting 5s...")
                    time.sleep(5)
                else:
                    print("Groq rate limit, switching to Gemini...")
                    break
            else:
                print(f"Groq error: {e}, switching to Gemini...")
                break

    for attempt in range(2):
        try:
            return llm_call_gemini(prompt, system)
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                if attempt == 0:
                    print("Gemini rate limit, waiting 10s...")
                    time.sleep(10)
                else:
                    print("Both APIs rate limited, waiting 30s...")
                    time.sleep(30)
                    return llm_call_groq(prompt, system)
            else:
                print(f"Gemini error: {e}")
                raise e

    return "Unable to generate response."