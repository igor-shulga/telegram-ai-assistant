import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher
from aiogram.types import Update

from app.bot import router, google_enabled

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

WEBHOOK_PATH = "/webhook"


@asynccontextmanager
async def lifespan(app: FastAPI):
    bot = Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])
    dp = Dispatcher()
    dp.include_router(router)

    base_url = os.environ["WEBHOOK_BASE_URL"].rstrip("/")
    webhook_url = f"{base_url}{WEBHOOK_PATH}"

    await bot.set_webhook(webhook_url)
    logger.info("Webhook set: %s", webhook_url)

    # Start calendar reminder scheduler if Google is configured
    scheduler = None
    if google_enabled():
        allowed_user_id = os.environ.get("ALLOWED_USER_ID", "")
        if allowed_user_id.strip():
            try:
                from app.reminders import start_reminder_scheduler
                chat_id = int(allowed_user_id)
                scheduler = start_reminder_scheduler(bot, chat_id)
                logger.info("Calendar reminders enabled for chat_id=%s", chat_id)
            except Exception as e:
                logger.error("Failed to start reminder scheduler: %s", e)
        else:
            logger.warning("ALLOWED_USER_ID not set — reminders disabled")

    app.state.bot = bot
    app.state.dp = dp
    app.state.scheduler = scheduler
    yield

    if scheduler:
        scheduler.shutdown(wait=False)
        logger.info("Reminder scheduler stopped")
    await bot.session.close()
    logger.info("Bot session closed")


app = FastAPI(lifespan=lifespan)


@app.api_route("/", methods=["GET", "HEAD"])
async def health():
    return {"status": "ok"}


@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    bot: Bot = request.app.state.bot
    dp: Dispatcher = request.app.state.dp
    update = Update.model_validate(await request.json())
    await dp.feed_update(bot, update)
    return {"ok": True}
