from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

import categories

MAIN = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Сегодня"), KeyboardButton(text="📆 Неделя"), KeyboardButton(text="📅 Месяц")],
        [KeyboardButton(text="📤 Экспорт"), KeyboardButton(text="↩️ Отменить")],
    ],
    resize_keyboard=True,
)

ALL_CATEGORIES = list(categories.CATEGORIES.keys())


def entry_kb(expense_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Категория", callback_data=f"cat:{expense_id}"),
                InlineKeyboardButton(text="🗑 Удалить", callback_data=f"del:{expense_id}"),
            ]
        ]
    )


def category_picker_kb(expense_id: int) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=name, callback_data=f"set:{expense_id}:{index}")]
        for index, name in enumerate(ALL_CATEGORIES)
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
