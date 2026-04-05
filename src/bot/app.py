from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.config import Settings
from src.di import Container
from src.bot.handlers import build_main_router
from src.bot.middlewares import ContainerMiddleware


def create_bot(settings: Settings) -> Bot:
    """Return a new Bot instance with an unbound aiohttp session."""
    return Bot(
        token=settings.BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher(container: Container) -> Dispatcher:
    """
    Build and return a fully-wired Dispatcher.

    This function MUST be called only once per process.  Aiogram's handler
    routers (common_router, generate_router, …) are module-level singletons.
    include_router() sets a parent pointer on each router; calling it a second
    time raises RuntimeError because the router already has a parent.
    """
    dp = Dispatcher()
    dp.update.middleware(ContainerMiddleware(container))
    dp.include_router(build_main_router())

    return dp
