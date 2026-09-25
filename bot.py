import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import config
import db
from handlers import callbacks, commands, expenses, photo, reports, voice


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    bot.db_conn = await db.connect(config.DB_PATH)
    await db.init_db(bot.db_conn)
    # user_id -> ("amount" | "category", expense_id): чего бот ждёт следующим текстовым сообщением
    bot.pending = {}

    dp = Dispatcher()
    # порядок важен: сначала специфичные хендлеры (команды/кнопки/голос/фото),
    # текстовый catch-all в expenses.router — последним
    dp.include_router(commands.router)
    dp.include_router(reports.router)
    dp.include_router(voice.router)
    dp.include_router(photo.router)
    dp.include_router(callbacks.router)
    dp.include_router(expenses.router)

    try:
        print("Pocket Expense Bot запущен. Ctrl+C для выхода.")
        await dp.start_polling(bot)
    finally:
        await bot.db_conn.close()


if __name__ == "__main__":
    asyncio.run(main())
