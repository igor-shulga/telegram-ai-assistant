"""Calendar reminder scheduler.

Checks upcoming events every 5 minutes and sends Telegram reminders
15 minutes before each event. Uses APScheduler with AsyncIOScheduler.
"""

import logging
from datetime import datetime, timezone, timedelta

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.google_services import get_calendar_events_raw

logger = logging.getLogger(__name__)

# Track reminded events to avoid duplicates: set of "eventId_YYYY-MM-DD"
_reminded_events: set[str] = set()


def _parse_event_time(event: dict) -> datetime | None:
    """Extract start datetime from a calendar event dict.

    Returns None for all-day events or missing start time.
    """
    start = event.get("start", {})
    dt_str = start.get("dateTime")
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _make_reminder_key(event: dict) -> str:
    """Build a unique key for tracking reminded events."""
    event_id = event.get("id", "unknown")
    event_time = _parse_event_time(event)
    date_str = event_time.strftime("%Y-%m-%d") if event_time else "nodate"
    return f"{event_id}_{date_str}"


def _should_remind(
    event: dict,
    now: datetime,
    window_min: int = 15,
    window_max: int = 20,
) -> bool:
    """Check if event is within the reminder window and not yet reminded.

    Returns True if event starts between window_min and window_max minutes from now
    and has not been reminded already.
    """
    event_time = _parse_event_time(event)
    if event_time is None:
        return False

    delta = (event_time - now).total_seconds() / 60.0
    if not (window_min <= delta <= window_max):
        return False

    key = _make_reminder_key(event)
    if key in _reminded_events:
        return False

    return True


async def check_and_send_reminders(bot: Bot, chat_id: int) -> None:
    """Fetch upcoming events and send reminders for those starting in 15-20 minutes.

    Called periodically by the scheduler. Marks reminded events to prevent duplicates.
    """
    try:
        events = get_calendar_events_raw(minutes_ahead=25)
        now = datetime.now(timezone.utc)

        for event in events:
            if _should_remind(event, now):
                title = event.get("summary", "Untitled event")
                event_time = _parse_event_time(event)
                time_str = event_time.strftime("%H:%M") if event_time else ""

                await bot.send_message(
                    chat_id=chat_id,
                    text=f"Reminder: {title} starts in 15 minutes ({time_str})",
                )
                key = _make_reminder_key(event)
                _reminded_events.add(key)
                logger.info("Reminder sent for event: %s", title)

    except Exception as e:
        logger.error("Reminder check error: %s", e)


def start_reminder_scheduler(bot: Bot, chat_id: int) -> AsyncIOScheduler:
    """Start a background scheduler that checks for upcoming events every 5 minutes.

    Returns the scheduler instance for lifecycle management.
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_and_send_reminders,
        "interval",
        minutes=5,
        args=[bot, chat_id],
        id="calendar_reminders",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Reminder scheduler started (every 5 min, chat_id=%d)", chat_id)
    return scheduler
