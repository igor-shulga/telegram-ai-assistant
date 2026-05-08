import os
import httpx
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a personal AI assistant for a Head of Product & Quality
who works with AI systems, multi-agent platforms, and enterprise software (TiONA platform).

You are helpful, analytical, and concise. You answer in the same language the user writes in.
When discussing technical topics, be specific and practical.
"""

async def chat(messages: list[dict]) -> str:
    api_key = os.environ["OPENROUTER_API_KEY"]

    payload = {
        "model": "inclusionai/ling-2.6-1t:free",
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        "max_tokens": 1000,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://github.com/personal-assistant",
            },
            json=payload,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"].get("content")
        if not content:
            return "Вибач, модель не відповіла. Спробуй ще раз."
        return content
