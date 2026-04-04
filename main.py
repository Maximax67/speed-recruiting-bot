"""
Entrypoint
==========
Reads ENV to decide whether to run webhook (production) or polling (development).
"""

from __future__ import annotations

import asyncio
import logging
import sys

from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    setup_application,
)
from aiohttp import web

from src.bot import create_bot, create_dispatcher
from src.config import get_settings
from src.di import build_container

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def _run_polling() -> None:
    settings = get_settings()
    container = build_container(settings)
    bot = create_bot(settings)
    dp = create_dispatcher(container)

    logger.info("Starting in POLLING mode")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


def _run_webhook() -> None:
    settings = get_settings()
    container = build_container(settings)
    bot = create_bot(settings)
    dp = create_dispatcher(container)

    async def on_startup(app: web.Application) -> None:
        webhook_url = settings.webhook_url
        secret = settings.WEBHOOK_SECRET.get_secret_value() or None
        await bot.set_webhook(webhook_url, secret_token=secret)
        logger.info("Webhook set to %s", webhook_url)

    async def on_shutdown(app: web.Application) -> None:
        await bot.delete_webhook()
        await bot.session.close()
        logger.info("Webhook deleted, session closed")

    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    secret = settings.WEBHOOK_SECRET.get_secret_value() or None
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=secret,
    ).register(app, path=settings.WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)

    logger.info(
        "Starting in WEBHOOK mode on %s:%s%s",
        settings.WEBHOOK_HOST,
        settings.WEBHOOK_PORT,
        settings.WEBHOOK_PATH,
    )
    web.run_app(app, host=settings.WEBHOOK_HOST, port=settings.WEBHOOK_PORT)


if __name__ == "__main__":
    settings = get_settings()
    if settings.is_production:
        _run_webhook()
    else:
        asyncio.run(_run_polling())
