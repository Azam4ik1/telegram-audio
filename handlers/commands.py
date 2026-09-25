from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

import keyboards

router = Router()

WELCOME = (
    "💰 Просто пиши траты — я запишу.\n\n"
    "Текстом: <code>50 такси</code> или <code>плов 35</code>\n"
    "Несколько сразу — каждая с новой строки.\n"
    "Голосом: просто скажи, что потратил.\n\n"
    "Отчёты и экспорт — на клавиатуре ниже."
)


@router.message(CommandStart())
@router.message(Command("help"))
async def cmd_start(message: Message) -> None:
    await message.answer(WELCOME, reply_markup=keyboards.MAIN)
