# 💰 Трекер расходов в Telegram

Пишешь или говоришь трату — бот записывает. Без меню и форм.

```
50 такси
плов 35
1.5к аренда
```

Голосом: «такси пятьдесят и плов тридцать пять».

## Возможности

- Запись текстом, несколько трат сразу (каждая с новой строки)
- Запись голосом через Gemini
- Автокатегории по ключевым словам + личные алиасы (✏️ меняешь категорию — бот запоминает слово)
- Fallback-классификация через Gemini для слов, которых нет в списке ключевых слов
- Отчёты: 📊 сегодня · 📆 неделя · 📅 месяц (сумма, проценты, полоски)
- 📤 Экспорт в CSV, ↩️ отмена последней записи

## Запуск

```bash
pip install -r requirements.txt
cp .env.example .env   # заполни BOT_TOKEN и GEMINI_API_KEY
export $(cat .env | xargs) && python bot.py
```

## Тесты

```bash
pytest
```

## Docker

```bash
docker build -t expense-bot .
docker run -d --env-file .env -v ./data:/app/data -e DB_PATH=/app/data/expenses.db expense-bot
```

## Структура

```
bot.py            # точка входа
config.py         # переменные окружения
db.py             # SQLite: expenses, aliases
categories.py     # категории, детект по алиасам/ключевым словам
parser.py         # parse_line(), fmt()
ai.py             # Gemini: голос + fallback-категория
keyboards.py      # клавиатуры
handlers/         # commands, expenses, voice, reports, callbacks
tests/            # тесты parser.py и categories.py
```

Подробная архитектура — в приложенном `ARCHITECTURE.md`.
