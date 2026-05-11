import os
import httpx
import logging

logger = logging.getLogger(__name__)

GOOGLE_API_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"

MODEL_FLASH = "gemini-2.0-flash"
MODEL_PRO   = "gemini-2.5-pro"

# Keywords that trigger deep thinking mode (Pro model)
THINK_KEYWORDS = [
    "подумай", "поміркуй", "подумайте", "розмірковуй",
    "think", "think deeply", "think harder", "reason",
    "проаналізуй детально", "детально", "глибоко",
    "подробно", "детально проанализируй", "подумай хорошо",
    "порассуждай", "разбери подробно",
]

SYSTEM_PROMPT = """You are a personal AI assistant for a Head of Product & Quality
who works with AI systems, multi-agent platforms, and enterprise software (TiONA platform).

You are helpful, analytical, and concise. You answer in the same language the user writes in.
When discussing technical topics, be specific and practical.
"""


def select_model(last_user_message: str) -> str:
    """Use Pro model if user asks to think deeply, Flash otherwise."""
    text = last_user_message.lower()
    if any(kw in text for kw in THINK_KEYWORDS):
        logger.info("Deep thinking requested — using Pro model")
        return MODEL_PRO
    return MODEL_FLASH


async def chat(messages: list[dict]) -> str:
    api_key = os.environ["GOOGLE_API_KEY"]

    last_user_msg = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
    )
    model = select_model(last_user_msg)

    payload = {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        "max_tokens": 2000,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            GOOGLE_API_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"].get("content")
        if not content:
            return "Вибач, модель не відповіла. Спробуй ще раз."
        logger.info("Gemini response [model=%s]", model)
        return content
