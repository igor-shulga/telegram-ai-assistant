import os
import asyncio
import logging
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from app.knowledge import get_context

logger = logging.getLogger(__name__)

MODEL_FLASH = "gemini-2.5-flash"
MODEL_PRO   = "gemini-2.5-pro"

THINK_KEYWORDS = [
    "подумай", "поміркуй", "розмірковуй",
    "think", "think deeply", "reason",
    "детально", "глибоко", "подробно",
    "порассуждай", "разбери подробно", "подумай хорошо",
]

SYSTEM_PROMPT = """You are a personal AI assistant and facilitation expert.
You have access to a facilitation knowledge base.

You are helpful, analytical, and concise. You answer in the same language the user writes in.
When discussing facilitation topics, use the knowledge base context provided.
When no context is provided, answer from your general knowledge.

FORMATTING RULES (Telegram chat — strict):
- Use plain text only. No markdown symbols.
- For bold: write in CAPS or use emphasis naturally in words.
- For lists: use numbers (1. 2. 3.) or dashes (- item)
- Do NOT use: ** * __ _ ## ### ` or any other markdown
- Keep responses concise. No unnecessary headers.
"""


def select_model(last_user_message: str) -> str:
    text = last_user_message.lower()
    if any(kw in text for kw in THINK_KEYWORDS):
        logger.info("Deep thinking requested — using Pro model")
        return MODEL_PRO
    return MODEL_FLASH


async def chat(messages: list[dict], google_context: str = "") -> str:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

    last_user_msg = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
    )
    model_name = select_model(last_user_msg)
    nav_model = genai.GenerativeModel(model_name=MODEL_FLASH)

    # Fetch relevant knowledge base context
    context = await get_context(last_user_msg, nav_model)

    system = SYSTEM_PROMPT
    if context:
        system += f"\n\n## Relevant knowledge base:\n\n{context}"
        logger.info("Knowledge context injected (%d chars)", len(context))
    if google_context:
        system += f"\n\n## Live data from Google:\n\n{google_context}"
        logger.info("Google context injected (%d chars)", len(google_context))

    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system,
    )

    history = []
    for m in messages[:-1]:
        role = "user" if m["role"] == "user" else "model"
        history.append({"role": role, "parts": [m["content"]]})

    chat_session = model.start_chat(history=history)

    for attempt in range(3):
        try:
            response = chat_session.send_message(last_user_msg)
            content = response.text
            if not content:
                return "Вибач, модель не відповіла. Спробуй ще раз."
            logger.info("Gemini response [model=%s, kb=%s]", model_name, "yes" if context else "no")
            return content
        except ResourceExhausted as e:
            wait = 30 * (attempt + 1)
            logger.warning("Rate limit hit (attempt %d/3), waiting %ds: %s", attempt + 1, wait, str(e)[:100])
            if attempt < 2:
                await asyncio.sleep(wait)
            else:
                return "Забагато запитів, спробуй через хвилину."
        except Exception as e:
            logger.error("Gemini error: %s", e)
            return "Помилка при зверненні до LLM. Спробуй ще раз."
