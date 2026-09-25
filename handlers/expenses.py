from datetime import datetime
from html import escape
from typing import List, Optional, Tuple

from aiogram import F, Router
from aiogram.types import Message

import categories
import config
import db
import keyboards
import parser

router = Router()

Item = Tuple[float, str, Optional[str]]  # (amount, note, category | None -> resolve)


async def save_and_reply(message: Message, conn, items: List[Item]) -> None:
    user_id = message.from_user.id
    now = datetime.now(tz=config.ZONE)

    saved = []
    for amount, note, category in items:
        resolved = category or await categories.resolve_category(conn, user_id, note)
        expense_id = await db.insert_expense(conn, user_id, amount, resolved, note, now.isoformat())
        saved.append((expense_id, amount, note, resolved))

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    today_expenses = await db.fetch_expenses(conn, user_id, since=today_start)
    total_today = sum(row["amount"] for row in today_expenses)

    if len(saved) == 1:
        expense_id, amount, note, resolved = saved[0]
        text = (
            f"✅ {escape(resolved)} · {parser.fmt(amount)} — {escape(note)}\n"
            f"Сегодня всего: {parser.fmt(total_today)}"
        )
        await message.answer(text, reply_markup=keyboards.entry_kb(expense_id))
    else:
        lines = [
            f"{escape(resolved)} · {parser.fmt(amount)} — {escape(note)}"
            for _, amount, note, resolved in saved
        ]
        text = (
            f"✅ Записал {len(saved)} трат:\n" + "\n".join(lines) +
            f"\nСегодня всего: {parser.fmt(total_today)}"
        )
        await message.answer(text, reply_markup=keyboards.MAIN)


async def _handle_pending(message: Message, conn, action: str, expense_id: int) -> None:
    user_id = message.from_user.id
    text = message.text.strip()

    if action == "amount":
        amount = parser.parse_amount(text)
        if amount is None:
            message.bot.pending[user_id] = (action, expense_id)
            await message.answer("Не понял число. Напиши, например: 45")
            return
        updated = await db.update_expense_amount(conn, expense_id, user_id, amount)
    elif action == "note":
        updated = await db.update_expense_note(conn, expense_id, user_id, text)
    else:  # action == "category"
        category = text
        expense = await db.get_expense(conn, expense_id, user_id)
        if expense:
            await db.set_alias(conn, user_id, expense["note"], category)
        updated = await db.update_expense_category(conn, expense_id, user_id, category)

    if not updated:
        await message.answer("Не нашёл эту запись", reply_markup=keyboards.MAIN)
        return

    expense = await db.get_expense(conn, expense_id, user_id)
    await message.answer(
        f"✅ {escape(expense['category'])} · {parser.fmt(expense['amount'])} — {escape(expense['note'])}",
        reply_markup=keyboards.entry_kb(expense_id),
    )


@router.message(F.text)
async def handle_text(message: Message) -> None:
    conn = message.bot.db_conn

    pending = message.bot.pending.pop(message.from_user.id, None)
    if pending:
        action, expense_id = pending
        await _handle_pending(message, conn, action, expense_id)
        return

    lines = message.text.strip().splitlines()

    items: List[Item] = []
    for line in lines:
        parsed = parser.parse_line(line)
        if parsed:
            amount, note = parsed
            items.append((amount, note, None))

    if not items:
        await message.answer("Не понял сумму. Напиши, например: <code>50 такси</code>")
        return

    await save_and_reply(message, conn, items)
