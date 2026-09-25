import csv
import io
from datetime import datetime, timedelta
from html import escape
from typing import Dict, List

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message

import config
import db
import keyboards
import parser

router = Router()


def build_report(rows: List[Dict], title: str) -> str:
    if not rows:
        return f"{title}\n\nПока нет трат."

    total = sum(row["amount"] for row in rows)
    by_category: Dict[str, float] = {}
    for row in rows:
        by_category[row["category"]] = by_category.get(row["category"], 0.0) + row["amount"]

    lines = [f"{title}", f"Всего: {parser.fmt(total)}", ""]
    for category, amount in sorted(by_category.items(), key=lambda kv: kv[1], reverse=True):
        percent = (amount / total * 100) if total else 0.0
        filled = round(percent / 10)
        bar = "▓" * filled + "░" * (10 - filled)
        lines.append(f"{escape(category)} {parser.fmt(amount)} ({percent:.0f}%) {bar}")

    return "\n".join(lines)


async def _report_since(message: Message, since: datetime, title: str) -> None:
    conn = message.bot.db_conn
    rows = await db.fetch_expenses(conn, message.from_user.id, since=since.isoformat())
    await message.answer(build_report(rows, title), reply_markup=keyboards.MAIN)


@router.message(Command("today"))
@router.message(F.text == "📊 Сегодня")
async def report_today(message: Message) -> None:
    now = datetime.now(tz=config.ZONE)
    since = now.replace(hour=0, minute=0, second=0, microsecond=0)
    await _report_since(message, since, "📊 Сегодня")


@router.message(Command("week"))
@router.message(F.text == "📆 Неделя")
async def report_week(message: Message) -> None:
    since = datetime.now(tz=config.ZONE) - timedelta(days=7)
    await _report_since(message, since, "📆 Последние 7 дней")


@router.message(Command("month"))
@router.message(F.text == "📅 Месяц")
async def report_month(message: Message) -> None:
    now = datetime.now(tz=config.ZONE)
    since = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    await _report_since(message, since, "📅 Этот месяц")


@router.message(Command("export"))
@router.message(F.text == "📤 Экспорт")
async def export_csv(message: Message) -> None:
    conn = message.bot.db_conn
    rows = await db.fetch_expenses(conn, message.from_user.id)
    if not rows:
        await message.answer("Пока нет трат для экспорта.", reply_markup=keyboards.MAIN)
        return

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["дата", "сумма", "категория", "заметка"])
    for row in rows:
        writer.writerow([row["created_at"], row["amount"], row["category"], row["note"]])

    document = BufferedInputFile(buffer.getvalue().encode("utf-8-sig"), filename="expenses.csv")
    await message.answer_document(document, reply_markup=keyboards.MAIN)


@router.message(Command("undo"))
@router.message(F.text == "↩️ Отменить")
async def undo_last(message: Message) -> None:
    conn = message.bot.db_conn
    user_id = message.from_user.id

    last = await db.fetch_last_expense(conn, user_id)
    if not last:
        await message.answer("Нечего отменять.", reply_markup=keyboards.MAIN)
        return

    await db.delete_expense(conn, last["id"], user_id)
    await message.answer(
        f"↩️ Удалил: {escape(last['category'])} · {parser.fmt(last['amount'])} — {escape(last['note'])}",
        reply_markup=keyboards.MAIN,
    )
