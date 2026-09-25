from html import escape

from aiogram import Router
from aiogram.types import Message

import ai
import categories
from handlers.expenses import save_and_reply

router = Router()


@router.message(lambda message: message.voice is not None)
async def handle_voice(message: Message) -> None:
    conn = message.bot.db_conn

    file = await message.bot.get_file(message.voice.file_id)
    audio = await message.bot.download_file(file.file_path)
    audio_bytes = audio.read()

    try:
        result = await ai.transcribe_voice(audio_bytes, categories.CHOOSABLE_CATEGORIES)
    except ai.GeminiUnavailable:
        await message.answer("Gemini сейчас перегружен 🙁 Подожди немного и попробуй снова.")
        return

    if not result:
        await message.answer("Не разобрал голос 🙁 Повтори ещё раз или напиши текстом.")
        return

    items = [(item["amount"], item["note"], item["category"]) for item in result["items"]]

    heard = result.get("heard")
    if heard:
        await message.answer(f"🎙 Услышал: {escape(heard)}")

    await save_and_reply(message, conn, items)
