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
bot = create_bot(settings)
dp = create_dispatcher(container)


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
            update = Update.model_validate(json.loads(body))
            asyncio.run(dp.feed_update(bot, update))
        except Exception as e:
            return self._send_json({"error": str(e)}, status=500)

        self._send_json({"status": "ok"})

    def do_GET(self) -> None:
        self._send_json({"status": "Speed Recruiting Bot is running."})
