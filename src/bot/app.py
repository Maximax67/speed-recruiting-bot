"""
Bot & Dispatcher factory
========================
Keeps aiogram object construction separate from startup logic.
"""

from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.config import Settings
from src.di import Container
from src.bot.handlers import build_main_router
from src.bot.middlewares import ContainerMiddleware


def create_bot(settings: Settings) -> Bot:
    return Bot(
        token=settings.BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher(container: Container) -> Dispatcher:
    dp = Dispatcher()

    # Register middleware on all update types
    dp.update.middleware(ContainerMiddleware(container))

    # Register all routers
    dp.include_router(build_main_router())

    return dp
