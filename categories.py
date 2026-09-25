from typing import Dict, List, Optional

import aiosqlite

import ai
import db

CATEGORIES: Dict[str, List[str]] = {
    "🍔 Еда": [
        "еда", "плов", "обед", "ужин", "завтрак", "кофе", "чай", "ресторан",
        "кафе", "продукты", "суп", "шашлык", "хлеб", "молоко", "мясо",
        "фрукты", "овощи",
    ],
    "🚕 Транспорт": [
        "такси", "бензин", "метро", "автобус", "маршрутка", "транспорт",
        "парковка", "авиабилет", "билет",
    ],
    "🏠 Дом": ["аренда", "квартира", "коммуналка", "свет", "вода", "газ", "ремонт"],
    "📱 Связь": ["интернет", "мобильный", "симка", "связь"],
    "🛍 Покупки": ["одежда", "обувь", "покупка", "техника"],
    "💊 Здоровье": ["аптека", "лекарства", "врач", "больница", "стоматолог", "витамины"],
    "🎉 Развлечения": ["кино", "бар", "клуб", "игра", "подписка", "концерт"],
    "📦 Другое": [],
}

DEFAULT_CATEGORY = "📦 Другое"

# categories a caller can offer to a classifier / picker — excludes the catch-all
CHOOSABLE_CATEGORIES: List[str] = [name for name in CATEGORIES if name != DEFAULT_CATEGORY]


def detect_by_keywords(note: str) -> Optional[str]:
    lowered = note.lower()
    for category, keywords in CATEGORIES.items():
        if any(keyword in lowered for keyword in keywords):
            return category
    return None


async def alias(conn: aiosqlite.Connection, user_id: int, note: str) -> Optional[str]:
    return await db.get_alias(conn, user_id, note)


async def detect(conn: aiosqlite.Connection, user_id: int, note: str) -> Optional[str]:
    """Личный алиас -> ключевые слова. None, если категория не найдена (нужен AI-fallback)."""
    aliased = await alias(conn, user_id, note)
    if aliased:
        return aliased
    return detect_by_keywords(note)


async def resolve_category(conn: aiosqlite.Connection, user_id: int, note: str) -> str:
    """Алиас -> ключевые слова -> Gemini fallback (только для незнакомых слов) -> «Другое»."""
    found = await detect(conn, user_id, note)
    if found:
        return found

    guessed = await ai.classify_category(note, CHOOSABLE_CATEGORIES)
    return guessed or DEFAULT_CATEGORY
