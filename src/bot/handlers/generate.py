from __future__ import annotations
import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message
from src.core.constraints import ValidationError, parse_and_validate
from src.di import Container

logger = logging.getLogger(__name__)
router = Router(name="generate")


@router.message(Command("generate"))
async def cmd_generate(message: Message, container: Container) -> None:
    raw_args = (message.text or "").split()[1:]

    if len(raw_args) != 3:
        await message.answer(
            "⚠️ Використання: <code>/generate N K M</code>\n\n"
            "Приклад: <code>/generate 40 15 3</code>\n"
            "Введіть /help для повного опису параметрів.",
            parse_mode="HTML",
        )
        return

    try:
        params = parse_and_validate(*raw_args)
    except ValidationError as exc:
        await message.answer(f"⚠️ {exc}", parse_mode="HTML")
        return

    n_sess = params.n_sessions
    sess_label = "сесія" if n_sess == 1 else ("сесії" if n_sess < 5 else "сесій")

    status = await message.answer(
        f"⏳ Генерую розклад для "
        f"<b>{params.n_students}</b> студентів, "
        f"<b>{params.n_partners}</b> партнерів, "
        f"<b>{params.n_rounds}</b> раундів "
        f"(<b>{n_sess}</b> {sess_label})…",
        parse_mode="HTML",
    )

    try:
        schedule = await container.scheduler.generate_async(params)
    except Exception as exc:
        logger.exception("Schedule generation failed: %s", exc)
        await status.edit_text("❌ Не вдалося згенерувати розклад. Спробуйте ще раз.")
        return

    chunks = container.scheduler.format_schedule(schedule, params)
    await status.delete()

    for chunk in chunks:
        await message.answer(f"<pre>{chunk}</pre>", parse_mode="HTML")

    image_bytes: bytes | None = None
    try:
        image_bytes = await container.visualizer.generate_image_async(schedule, params)
        await message.answer_photo(
            BufferedInputFile(image_bytes, filename="schedule.png"),
            caption=(
                f"📊 Розклад — {params.n_students} студентів × "
                f"{params.n_rounds} раундів ({params.n_partners} партнерів, "
                f"{n_sess} {sess_label})"
            ),
        )
    except Exception as exc:
        logger.exception("Image send failed: %s", exc)
        is_send_success = False

        if image_bytes:
            try:
                await message.answer_document(
                    BufferedInputFile(image_bytes, filename="schedule.png"),
                    caption=(
                        f"📊 Розклад — {params.n_students} студентів × "
                        f"{params.n_rounds} раундів ({params.n_partners} партнерів, "
                        f"{n_sess} {sess_label})"
                    ),
                )
                is_send_success = True
            except Exception as exc2:
                logger.exception("Image send as file failed: %s", exc2)

        if not is_send_success:
            await message.answer(
                "⚠️ Не вдалося згенерувати зображення, але текстовий розклад вище є повним."
            )
