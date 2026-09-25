from html import escape

from aiogram import Router
from aiogram.types import Message

import ai
import categories
from handlers.expenses import save_and_reply

router = Router()


@router.message(lambda message: message.photo is not None)
async def handle_photo(message: Message) -> None:
    conn = message.bot.db_conn

    largest = message.photo[-1]
    file = await message.bot.get_file(largest.file_id)
    photo = await message.bot.download_file(file.file_path)
    image_bytes = photo.read()

    try:
        result = await ai.analyze_receipt(image_bytes, categories.CHOOSABLE_CATEGORIES)
    except ai.GeminiUnavailable:
        await message.answer("Gemini сейчас перегружен 🙁 Подожди немного и попробуй снова.")
        return

    if not result:
        await message.answer("Не разобрал чек на фото 🙁 Попробуй чётче или напиши текстом.")
        return

    items = [(item["amount"], item["note"], item["category"]) for item in result["items"]]

    heard = result.get("heard")
    if heard:
        await message.answer(f"🧾 Увидел: {escape(heard)}")

    await save_and_reply(message, conn, items)
