import asyncio
import json
import logging
from typing import Dict, List, Optional

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

import config

logger = logging.getLogger(__name__)

_client: Optional[genai.Client] = None

VOICE_TIMEOUT_SECONDS = 25
CLASSIFY_TIMEOUT_SECONDS = 5


class VoiceUnavailable(Exception):
    """Gemini временно недоступен (перегрузка/503) — стоит повторить попытку."""


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _client


def _voice_prompt(categories: List[str]) -> str:
    category_list = ", ".join(categories)
    return (
        "Ты — парсер голосовых сообщений о расходах на русском/тоҷикӣ языке. "
        "В сообщении может быть НЕСКОЛЬКО трат подряд — перечисли КАЖДУЮ из них "
        "отдельным элементом массива items, ничего не пропускай и не объединяй разные траты в одну. "
        "Для каждой определи сумму (только число, если сумма произнесена словами — переведи в цифры) "
        "и короткую заметку (1-3 слова). "
        f"Категория — одна из списка: {category_list}. Если ни одна не подходит — не указывай категорию. "
        "Ответь ТОЛЬКО JSON без пояснений в формате: "
        '{"heard": "что услышал", "items": ['
        '{"amount": 50, "note": "такси", "category": "🚕 Транспорт"}, '
        '{"amount": 35, "note": "плов", "category": "🍔 Еда"}'
        "]}"
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
    except genai_errors.ServerError as e:
        logger.warning("Gemini overloaded during transcribe_voice: %s", e)
        raise VoiceUnavailable from e
    except Exception:
        logger.exception("transcribe_voice failed")
        return None

    items = []
    for item in data.get("items", []):
        note = item.get("note")
        category = item.get("category")
        try:
            amount = float(str(item.get("amount")).replace(",", "."))
        except (TypeError, ValueError):
            continue
        if amount <= 0 or not note:
            continue
        if category not in categories:
            category = None
        items.append({"amount": amount, "note": str(note).strip(), "category": category})

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
        logger.exception("classify_category failed")
        return None

    category = data.get("category")
    return category if category in categories else None
