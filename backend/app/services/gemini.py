import asyncio
import json
import re
from google import genai
from google.genai import types
from app.config import GEMINI_API_KEY, GEMINI_MODEL

client = genai.Client(api_key=GEMINI_API_KEY)


async def call_gemini(prompt: str) -> str:
    loop = asyncio.get_event_loop()

    def sync_call():
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                max_output_tokens=8000,
            )
        )
        return response.text

    return await loop.run_in_executor(None, sync_call)


def parse_ai_json(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'\s*```\s*$', '', raw, flags=re.MULTILINE)
    return json.loads(raw.strip())
