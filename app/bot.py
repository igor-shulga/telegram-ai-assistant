import os
import logging
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import Command
from app.llm import chat
from app.memory import add_message, get_history, clear_history

logger = logging.getLogger(__name__)
router = Router()

def get_allowed_user_id() -> int | None:
    val = os.environ.get("ALLOWED_USER_ID", "")
    return int(val) if val.strip() else None

@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Привіт! Я твій AI-асистент.\n\n"
        "Просто пиши мені — відповідаю через OpenRouter LLM.\n"
        "/clear — очистити контекст розмови"
    )

@router.message(Command("clear"))
async def cmd_clear(message: Message) -> None:
    clear_history(message.from_user.id)
    await message.answer("Контекст очищений.")

@router.message()
async def handle_message(message: Message) -> None:
    allowed = get_allowed_user_id()
    if allowed and message.from_user.id != allowed:
        return  # ігноруємо чужих

    user_id = message.from_user.id
    text = message.text or ""
    if not text:
        return

    # Показати "typing..."
    await message.bot.send_chat_action(message.chat.id, "typing")

    add_message(user_id, "user", text)
    history = get_history(user_id)

    try:
        response = await chat(history)
        add_message(user_id, "assistant", response)
        await message.answer(response)
    except Exception as e:
        logger.error("LLM error: %s", e)
        await message.answer("Помилка при зверненні до LLM. Спробуй ще раз.")
