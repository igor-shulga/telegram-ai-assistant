import os
import logging
import google.generativeai as genai
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import Command
from app.llm import chat, MODEL_FLASH
from app.memory import add_message, get_history, clear_history
from app.google_services import (
    get_calendar_events,
    get_recent_emails,
    create_calendar_event,
    parse_event_from_text,
    extract_gmail_query,
)

logger = logging.getLogger(__name__)
router = Router()

# ─── Intent keywords ─────────────────────────────────────────────────────────

CREATE_EVENT_KEYWORDS = [
    "створи зустріч", "створи подію", "додай зустріч", "додай подію",
    "заплануй", "create a meeting", "create meeting", "create event",
    "schedule a meeting", "schedule meeting",
]

CALENDAR_KEYWORDS = [
    "календар", "calendar", "зустріч", "meeting", "завтра", "tomorrow",
    "сьогодні", "today", "розклад", "schedule", "події", "events",
    "що у мене", "what do i have", "покажи зустрічі",
]

EMAIL_SEARCH_KEYWORDS = [
    "знайди листи", "знайди лист", "пошук листів", "пошук листи",
    "search emails", "search email", "find emails", "find email",
    "покажи листи від", "покажи листи за",
]

EMAIL_KEYWORDS = [
    "пошта", "email", "mail", "лист", "листи", "письмо", "письма",
    "inbox", "gmail", "непрочитані", "unread", "покажи листи",
    "від кого", "from", "повідомлення",
]


def detect_intent(text: str) -> str | None:
    """Detect user intent from message text.

    Priority order: create_event > email_search > calendar > email.
    More specific intents are checked first to avoid false matches.
    """
    t = text.lower()
    if any(kw in t for kw in CREATE_EVENT_KEYWORDS):
        return "create_event"
    if any(kw in t for kw in EMAIL_SEARCH_KEYWORDS):
        return "email_search"
    if any(kw in t for kw in CALENDAR_KEYWORDS):
        return "calendar"
    if any(kw in t for kw in EMAIL_KEYWORDS):
        return "email"
    return None


def get_allowed_user_id() -> int | None:
    val = os.environ.get("ALLOWED_USER_ID", "")
    return int(val) if val.strip() else None


def google_enabled() -> bool:
    return bool(os.environ.get("GOOGLE_REFRESH_TOKEN"))


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    google_status = "Google Calendar, Gmail і Drive підключені." if google_enabled() else ""
    await message.answer(
        "Привіт! Я твій AI-асистент.\n\n"
        "Знаю базу знань з фасилітації. "
        f"{google_status}\n\n"
        "/clear — очистити контекст розмови\n"
        "/today — події на сьогодні\n"
        "/inbox — непрочитані листи"
    )


@router.message(Command("clear"))
async def cmd_clear(message: Message) -> None:
    clear_history(message.from_user.id)
    await message.answer("Контекст очищений.")


@router.message(Command("today"))
async def cmd_today(message: Message) -> None:
    if not google_enabled():
        await message.answer("Google не підключений.")
        return
    await message.bot.send_chat_action(message.chat.id, "typing")
    events = get_calendar_events(days_ahead=1)
    await message.answer(f"Події на сьогодні:\n\n{events}")


@router.message(Command("inbox"))
async def cmd_inbox(message: Message) -> None:
    if not google_enabled():
        await message.answer("Google не підключений.")
        return
    await message.bot.send_chat_action(message.chat.id, "typing")
    emails = get_recent_emails(query="is:unread", max_results=5)
    await message.answer(f"Непрочитані листи:\n\n{emails}")


@router.message()
async def handle_message(message: Message) -> None:
    allowed = get_allowed_user_id()
    if allowed and message.from_user.id != allowed:
        return

    user_id = message.from_user.id
    text = message.text or ""
    if not text:
        return

    await message.bot.send_chat_action(message.chat.id, "typing")

    # Inject Google context if relevant
    google_context = ""
    if google_enabled():
        intent = detect_intent(text)

        # Feature 1: Create calendar event
        if intent == "create_event":
            try:
                genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
                model = genai.GenerativeModel(model_name=MODEL_FLASH)
                event_data = await parse_event_from_text(text, model)
                if event_data:
                    start_iso = f"{event_data['date']}T{event_data['time']}:00"
                    result = create_calendar_event(
                        title=event_data["title"],
                        start_iso=start_iso,
                        duration_minutes=event_data.get("duration_minutes", 60),
                    )
                    await message.answer(
                        f"Подію створено: {event_data['title']} "
                        f"на {event_data['date']} о {event_data['time']}"
                    )
                    add_message(user_id, "user", text)
                    add_message(user_id, "assistant", f"Event created: {event_data['title']}")
                    return
                else:
                    google_context = "[Could not parse event details from message]"
            except Exception as e:
                logger.error("Event creation error: %s", e)
                google_context = "[Event creation failed — answering via LLM]"

        # Feature 2: Gmail search
        elif intent == "email_search":
            try:
                genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
                model = genai.GenerativeModel(model_name=MODEL_FLASH)
                gmail_query = await extract_gmail_query(text, model)
                if gmail_query:
                    emails = get_recent_emails(query=gmail_query, max_results=10)
                    google_context = f"[Gmail search: {gmail_query}]\n{emails}"
                    logger.info("Gmail search context injected: %s", gmail_query)
                else:
                    emails = get_recent_emails(max_results=5)
                    google_context = f"[Gmail — recent emails]\n{emails}"
            except Exception as e:
                logger.error("Gmail search error: %s", e)
                google_context = "[Gmail search failed]"

        elif intent == "calendar":
            events = get_calendar_events(days_ahead=3)
            google_context = f"[Google Calendar — next 3 days]\n{events}"
            logger.info("Calendar context injected")
        elif intent == "email":
            emails = get_recent_emails(max_results=5)
            google_context = f"[Gmail — recent emails]\n{emails}"
            logger.info("Email context injected")

    add_message(user_id, "user", text)
    history = get_history(user_id)

    try:
        response = await chat(history, google_context=google_context)
        add_message(user_id, "assistant", response)
        await message.answer(response)
    except Exception as e:
        logger.error("LLM error: %s", e)
        await message.answer("Помилка при зверненні до LLM. Спробуй ще раз.")
