from aiogram import Router
from .common import router as common_router
from .generate import router as generate_router


def build_main_router() -> Router:
    root = Router(name="root")
    root.include_router(common_router)
    root.include_router(generate_router)
    return root
