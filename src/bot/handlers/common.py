from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="common")

_HELP_TEXT = (
    "<b>Бот для складання розкладу швидкого рекрутингу</b>\n\n"
    "<b>Команда</b>\n"
    "<code>/generate N K M</code>\n\n"
    "<b>Параметри</b>\n"
    "• <b>N</b> — загальна кількість студентів (1 – 1000)\n"
    "• <b>K</b> — кількість партнерів у кімнаті (1 – 200)\n"
    "• <b>M</b> — кількість раундів за сесію (1 – 50, M ≤ K)\n\n"
    "<b>Обмеження</b>\n"
    "• M ≤ K  (за сесію студент відвідує M різних партнерів)\n\n"
    "<b>Приклади</b>\n"
    "<code>/generate 10 15 3</code>  — 10 студентів, 15 партнерів, 3 раунд, 1 сесія\n"
    "<code>/generate 40 15 3</code>  — 40 студентів, 15 партнерів, 3 сесії по 15/15/10\n\n"
    "Бот надішле текстовий розклад і кольорову таблицю у форматі PNG."
)


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(_HELP_TEXT, parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(_HELP_TEXT, parse_mode="HTML")
