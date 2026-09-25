from aiogram import F, Router
from aiogram.types import CallbackQuery

import db
import keyboards
import parser

router = Router()


@router.callback_query(F.data.startswith("del:"))
async def on_delete(callback: CallbackQuery) -> None:
    conn = callback.bot.db_conn
    expense_id = int(callback.data.split(":", 1)[1])

    deleted = await db.delete_expense(conn, expense_id, callback.from_user.id)
    if deleted:
        await callback.message.edit_text("🗑 Удалено")
    await callback.answer()


@router.callback_query(F.data.startswith("cat:"))
async def on_pick_category(callback: CallbackQuery) -> None:
    expense_id = int(callback.data.split(":", 1)[1])
    await callback.message.edit_reply_markup(reply_markup=keyboards.category_picker_kb(expense_id))
    await callback.answer()


@router.callback_query(F.data.startswith("set:"))
async def on_set_category(callback: CallbackQuery) -> None:
    conn = callback.bot.db_conn
    _, expense_id_str, index_str = callback.data.split(":")
    expense_id = int(expense_id_str)
    category = keyboards.ALL_CATEGORIES[int(index_str)]

    updated = await db.update_expense_category(conn, expense_id, callback.from_user.id, category)
    if not updated:
        await callback.answer("Не нашёл эту запись", show_alert=True)
        return

    expense = await db.get_expense(conn, expense_id, callback.from_user.id)
    await callback.message.edit_text(
        f"✅ {category} · {parser.fmt(expense['amount'])} — {expense['note']}",
        reply_markup=keyboards.entry_kb(expense_id),
    )
    await callback.answer("Категория изменена")
