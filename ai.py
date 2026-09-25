import asyncio
import json
from typing import Dict, List, Optional

from google import genai
from google.genai import types

import config

_client: Optional[genai.Client] = None

VOICE_TIMEOUT_SECONDS = 15
CLASSIFY_TIMEOUT_SECONDS = 5


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _client


def _voice_prompt(categories: List[str]) -> str:
    category_list = ", ".join(categories)
    return (
        "Ты — парсер голосовых сообщений о расходах на русском/тоҷикӣ языке. "
        "Раздели услышанное на отдельные траты. Для каждой определи сумму (число) "
        "и короткую заметку (1-3 слова). "
        f"Категория — одна из списка: {category_list}. Если ни одна не подходит — не указывай категорию. "
        "Ответь ТОЛЬКО JSON без пояснений в формате: "
        '{"heard": "что услышал", "items": [{"amount": 50.0, "note": "такси", "category": "🚕 Транспорт"}]}'
    )


async def transcribe_voice(audio_bytes: bytes, categories: List[str]) -> Optional[Dict]:
    """Голос -> {"heard": str, "items": [{"amount", "note", "category"}]}, либо None при ошибке."""
    try:
        client = _get_client()
        response = await asyncio.wait_for(
            client.aio.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=[
                    types.Part.from_bytes(data=audio_bytes, mime_type="audio/ogg"),
                    _voice_prompt(categories),
                ],
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            ),
            timeout=VOICE_TIMEOUT_SECONDS,
        )
        data = json.loads(response.text)
    except Exception:
        return None

    items = []
    for item in data.get("items", []):
        amount = item.get("amount")
        note = item.get("note")
        category = item.get("category")
        if not isinstance(amount, (int, float)) or amount <= 0 or not note:
            continue
        if category not in categories:
            category = None
        items.append({"amount": float(amount), "note": str(note).strip(), "category": category})

    if not items:
        return None

    return {"heard": str(data.get("heard", "")), "items": items}


async def classify_category(note: str, categories: List[str]) -> Optional[str]:
    """Fallback-классификация категории для слова, не найденного в keyword-списке/алиасах."""
    try:
        client = _get_client()
        category_list = ", ".join(categories)
        prompt = (
            f'Слово или фраза о трате: "{note}". '
            f"Выбери одну подходящую категорию из списка: {category_list}. "
            'Ответь ТОЛЬКО JSON: {"category": "..."}. Если ничего не подходит — {"category": null}.'
        )
        response = await asyncio.wait_for(
            client.aio.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json"),
            ),
            timeout=CLASSIFY_TIMEOUT_SECONDS,
        )
        data = json.loads(response.text)
    except Exception:
        return None

    category = data.get("category")
    return category if category in categories else None
