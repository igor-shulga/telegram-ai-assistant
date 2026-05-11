import os
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

MODEL_FLASH = "gemini-2.5-flash"
MODEL_PRO   = "gemini-2.5-pro"

THINK_KEYWORDS = [
    "подумай", "поміркуй", "розмірковуй",
    "think", "think deeply", "reason",
    "детально", "глибоко", "подробно",
    "порассуждай", "разбери подробно", "подумай хорошо",
]

SYSTEM_PROMPT = """You are a personal AI assistant for a Head of Product & Quality
who works with AI systems, multi-agent platforms, and enterprise software (TiONA platform).

You are helpful, analytical, and concise. You answer in the same language the user writes in.
When discussing technical topics, be specific and practical.
"""


def select_model(last_user_message: str) -> str:
    text = last_user_message.lower()
    if any(kw in text for kw in THINK_KEYWORDS):
        logger.info("Deep thinking requested — using Pro model")
        return MODEL_PRO
    return MODEL_FLASH


async def chat(messages: list[dict]) -> str:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

    last_user_msg = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
    )
    model_name = select_model(last_user_msg)
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=SYSTEM_PROMPT,
    )

    # Convert messages to Gemini format
    history = []
    for m in messages[:-1]:  # all except last
        role = "user" if m["role"] == "user" else "model"
        history.append({"role": role, "parts": [m["content"]]})

    chat_session = model.start_chat(history=history)
    response = chat_session.send_message(last_user_msg)

    content = response.text
    if not content:
        return "Вибач, модель не відповіла. Спробуй ще раз."

    logger.info("Gemini response [model=%s]", model_name)
    return content
