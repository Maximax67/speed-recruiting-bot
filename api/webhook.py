import asyncio
import json
from http.server import BaseHTTPRequestHandler
from typing import Any

from aiogram.types import Update

from src.bot import create_bot, create_dispatcher
from src.config import get_settings
from src.di import build_container

settings = get_settings()
container = build_container(settings)


async def _process_update(body: bytes) -> None:
    bot = create_bot(settings)
    dp = create_dispatcher(container)
    try:
        update = Update.model_validate(json.loads(body))
        await dp.feed_update(bot, update)
    finally:
        # Always close the session so the underlying connector is not leaked.
        await bot.session.close()


class handler(BaseHTTPRequestHandler):
    def _send_json(self, data: dict[str, Any], status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        secret = settings.WEBHOOK_SECRET.get_secret_value()
        if secret:
            token = self.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if token != secret:
                return self._send_json({"error": "Forbidden"}, status=403)

        try:
            # Each call to asyncio.run() gets its own fresh event loop.
            # _process_update creates the bot inside that loop and closes it
            # before the loop is destroyed, so no dangling sessions remain.
            asyncio.run(_process_update(body))
        except Exception as e:
            return self._send_json({"error": str(e)}, status=500)

        self._send_json({"status": "ok"})

    def do_GET(self) -> None:
        self._send_json({"status": "Speed Recruiting Bot is running."})
