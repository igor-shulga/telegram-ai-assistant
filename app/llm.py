import os
import json
import httpx
import logging

logger = logging.getLogger(__name__)

FREE_LLM_URL = "https://shir-man.com/free-llm/"
FALLBACK_MODEL = "meta-llama/llama-3.3-70b-instruct:free"

SYSTEM_PROMPT = """You are a personal AI assistant for a Head of Product & Quality
who works with AI systems, multi-agent platforms, and enterprise software (TiONA platform).

You are helpful, analytical, and concise. You answer in the same language the user writes in.
When discussing technical topics, be specific and practical.
"""


def get_best_model() -> str:
    """Fetch today's recommended free model from shir-man.com, fall back to llama."""
    try:
        resp = httpx.get(FREE_LLM_URL, timeout=10)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")

        if "json" in content_type:
            data = resp.json()
            model = data.get("model", FALLBACK_MODEL)
            logger.info("Free LLM model (JSON): %s", model)
            return model

        try:
            data = resp.json()
            model = data.get("model", FALLBACK_MODEL)
            logger.info("Free LLM model (parsed JSON): %s", model)
            return model
        except (json.JSONDecodeError, ValueError):
            pass

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup.select("code, pre, .model, #model"):
            text = tag.get_text(strip=True)
            if "/" in text and len(text) < 100:
                logger.info("Free LLM model (HTML): %s", text)
                return text

        logger.warning("Could not extract model, using fallback")
        return FALLBACK_MODEL
    except Exception as exc:
        logger.warning("Failed to fetch free model: %s — using fallback", exc)
        return FALLBACK_MODEL


async def chat(messages: list[dict]) -> str:
    api_key = os.environ["OPENROUTER_API_KEY"]
    model = get_best_model()

    payload = {
        "model": model,
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
