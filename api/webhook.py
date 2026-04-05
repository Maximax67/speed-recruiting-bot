from __future__ import annotations

import asyncio
import json
import logging
import traceback
from http.server import BaseHTTPRequestHandler
from typing import Any

from aiogram.types import Update

from src.bot import create_bot, create_dispatcher
from src.config import get_settings
from src.di import build_container

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("webhook")

logger.info("Initialising module-level singletons")
try:
    settings = get_settings()
    container = build_container(settings)
    dp = create_dispatcher(container)  # registers routers once; must not repeat
    logger.info("Singletons ready (env=%s)", settings.ENV)
except Exception:
    logger.critical("Failed to initialise singletons:\n%s", traceback.format_exc())
    raise


async def _process_update(body: bytes) -> None:
    """
    Parse the incoming Telegram payload and feed it to the dispatcher.

    A new Bot instance is created here so that its aiohttp session is bound to
    the event loop that asyncio.run() provides for *this* request.  The session
    is always closed before we return, preventing resource leaks and ensuring
    the next request gets a clean slate.
    """
    bot = create_bot(settings)
    logger.debug("Bot session created for this request")
    try:
        update = Update.model_validate(json.loads(body))
        logger.info("Processing update id=%s type=%s", update.update_id, update.event_type)
        await dp.feed_update(bot, update)
        logger.info("Update id=%s handled successfully", update.update_id)
    finally:
        await bot.session.close()
        logger.debug("Bot session closed")


class handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        logger.debug("HTTP %s", fmt % args)

    def _send_json(self, data: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        self._send_json({"status": "Speed Recruiting Bot is running."})

    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        secret = settings.WEBHOOK_SECRET.get_secret_value()
        if secret:
            received = self.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if received != secret:
                logger.warning("Rejected request: invalid secret token")
                return self._send_json({"error": "Forbidden"}, status=403)

        try:
            asyncio.run(_process_update(body))
        except json.JSONDecodeError as exc:
            logger.error("Malformed JSON in request body: %s", exc)
            return self._send_json({"error": "Bad Request"}, status=400)
        except Exception:
            logger.error("Unhandled exception while processing update:\n%s", traceback.format_exc())
            return self._send_json({"error": "Internal Server Error"}, status=500)

        self._send_json({"status": "ok"})
