import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from aiogram.types import Update

from app.bot import router

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

    app.state.bot = bot
    app.state.dp = dp
    yield

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
