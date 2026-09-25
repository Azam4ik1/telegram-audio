from typing import Dict, List, Optional

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    note TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS aliases (
    user_id INTEGER NOT NULL,
    word TEXT NOT NULL,
    category TEXT NOT NULL,
    PRIMARY KEY (user_id, word)
);

CREATE INDEX IF NOT EXISTS idx_exp_user_date ON expenses(user_id, created_at);
"""


async def connect(db_path: str) -> aiosqlite.Connection:
    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row
    return conn


async def init_db(conn: aiosqlite.Connection) -> None:
    await conn.executescript(SCHEMA)
    await conn.commit()


async def insert_expense(
    conn: aiosqlite.Connection,
    user_id: int,
    amount: float,
    category: str,
    note: str,
    created_at: str,
) -> int:
    cursor = await conn.execute(
        "INSERT INTO expenses (user_id, amount, category, note, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, amount, category, note, created_at),
    )
    await conn.commit()
    return cursor.lastrowid


async def fetch_expenses(
    conn: aiosqlite.Connection, user_id: int, since: Optional[str] = None
) -> List[Dict]:
    if since is None:
        query = "SELECT * FROM expenses WHERE user_id = ? ORDER BY created_at"
        params = (user_id,)
    else:
        query = "SELECT * FROM expenses WHERE user_id = ? AND created_at >= ? ORDER BY created_at"
        params = (user_id, since)
    cursor = await conn.execute(query, params)
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def fetch_last_expense(conn: aiosqlite.Connection, user_id: int) -> Optional[Dict]:
    cursor = await conn.execute(
        "SELECT * FROM expenses WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (user_id,),
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def delete_expense(conn: aiosqlite.Connection, expense_id: int, user_id: int) -> bool:
    cursor = await conn.execute(
        "DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id)
    )
    await conn.commit()
    return cursor.rowcount > 0


async def update_expense_amount(
    conn: aiosqlite.Connection, expense_id: int, user_id: int, amount: float
) -> bool:
    cursor = await conn.execute(
        "UPDATE expenses SET amount = ? WHERE id = ? AND user_id = ?",
        (amount, expense_id, user_id),
    )
    await conn.commit()
    return cursor.rowcount > 0


async def update_expense_note(
    conn: aiosqlite.Connection, expense_id: int, user_id: int, note: str
) -> bool:
    cursor = await conn.execute(
        "UPDATE expenses SET note = ? WHERE id = ? AND user_id = ?",
        (note, expense_id, user_id),
    )
    await conn.commit()
    return cursor.rowcount > 0


async def update_expense_category(
    conn: aiosqlite.Connection, expense_id: int, user_id: int, category: str
) -> bool:
    cursor = await conn.execute(
        "UPDATE expenses SET category = ? WHERE id = ? AND user_id = ?",
        (category, expense_id, user_id),
    )
    await conn.commit()
    return cursor.rowcount > 0


async def get_expense(conn: aiosqlite.Connection, expense_id: int, user_id: int) -> Optional[Dict]:
    cursor = await conn.execute(
        "SELECT * FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def get_alias(conn: aiosqlite.Connection, user_id: int, word: str) -> Optional[str]:
    cursor = await conn.execute(
        "SELECT category FROM aliases WHERE user_id = ? AND word = ?", (user_id, word.lower())
    )
    row = await cursor.fetchone()
    return row["category"] if row else None


async def set_alias(conn: aiosqlite.Connection, user_id: int, word: str, category: str) -> None:
    await conn.execute(
        "INSERT INTO aliases (user_id, word, category) VALUES (?, ?, ?) "
        "ON CONFLICT (user_id, word) DO UPDATE SET category = excluded.category",
        (user_id, word.lower(), category),
    )
    await conn.commit()
