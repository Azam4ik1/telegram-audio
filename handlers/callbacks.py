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


@router.callback_query(F.data.startswith("amt:"))
async def on_edit_amount(callback: CallbackQuery) -> None:
    expense_id = int(callback.data.split(":", 1)[1])
    callback.bot.pending[callback.from_user.id] = ("amount", expense_id)
    await callback.message.answer("Введи новую сумму (например: 45 или 1.5к)")
    await callback.answer()


@router.callback_query(F.data.startswith("custom:"))
async def on_custom_category(callback: CallbackQuery) -> None:
    expense_id = int(callback.data.split(":", 1)[1])
    callback.bot.pending[callback.from_user.id] = ("category", expense_id)
    await callback.message.answer("Напиши свою категорию (например: 🎁 Подарки) — запомню на будущее")
    await callback.answer()


@router.callback_query(F.data.startswith("set:"))
async def on_set_category(callback: CallbackQuery) -> None:
    conn = callback.bot.db_conn
    _, expense_id_str, index_str = callback.data.split(":")
    expense_id = int(expense_id_str)
    category = keyboards.ALL_CATEGORIES[int(index_str)]

    expense = await db.get_expense(conn, expense_id, callback.from_user.id)
    if expense:
        await db.set_alias(conn, callback.from_user.id, expense["note"], category)

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
