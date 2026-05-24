# Speaky-Chinese — Telegram Bot для практики китайского

Telegram-бот для практики разговорного китайского языка с AI.

## Возможности

- 🎤 **Голосовые диалоги** — говорите на китайском, бот отвечает голосом
- 📝 **Текстовые сообщения** — пишите иероглифами, получайте ответы
- ✏️ **Исправление ошибок** — AI исправляет грамматику и объясняет ошибки
- 📚 **HSK 1-3** — словарь адаптируется под ваш уровень
- 🎯 **6 тем** — путешествия, еда, работа, быт, учёба, здоровье
- 📖 **Личный словарь** — сохраняйте новые слова
- 👥 **Реферальная программа** — приглашайте друзей, получайте Premium

## Установка

### Требования

- Python 3.11+
- Telegram Bot Token (от @BotFather)
- OpenAI API Key

### Шаги

1. Клонируйте репозиторий:

```bash
git clone <repo-url>
cd speaky-chinese
```

1. Создайте виртуальное окружение:

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

1. Установите зависимости:

```bash
pip install -r requirements.txt
```

1. Создайте `.env` файл:

```bash
cp .env.example .env
```

1. Заполните `.env`:

```env
BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
ADMIN_IDS=123456789,987654321
```

1. Запустите бота:

```bash
python -m bot.main
```

## Структура проекта

```
hanyu-bot/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Точка входа
│   ├── config.py            # Настройки (Pydantic)
│   ├── handlers/            # Обработчики команд
│   │   ├── start.py         # /start, /help
│   │   ├── dialog.py        # Голосовые и текстовые сообщения
│   │   ├── topic.py         # /topic
│   │   ├── settings.py      # /settings, /level
│   │   ├── premium.py       # /premium
│   │   ├── referral.py      # /invite
│   │   ├── vocabulary.py    # /vocabulary
│   │   ├── admin.py         # /admin
│   │   ├── profile.py       # Профиль
│   │   └── callbacks.py     # Inline-кнопки
│   ├── keyboards/           # Клавиатуры
│   │   ├── reply.py         # Нижнее меню
│   │   └── inline.py        # Inline-кнопки
│   ├── middlewares/         # Middleware
│   │   ├── auth.py          # Авторизация
│   │   ├── subscription.py  # Проверка лимитов
│   │   └── throttling.py    # Rate limiting
│   ├── services/            # Сервисы
│   │   └── ai.py            # OpenAI (Whisper, GPT, TTS)
│   ├── database/            # База данных
│   │   ├── database.py      # SQLite подключение
│   │   ├── models.py        # Dataclass модели
│   │   └── repositories.py  # CRUD операции
│   └── utils/               # Утилиты
│       └── hsk.py           # HSK словари
├── data/
│   ├── hsk1.json            # HSK 1 (~150 слов)
│   ├── hsk2.json            # HSK 2 (~150 слов)
│   └── hsk3.json            # HSK 3 (~150 слов)
├── .env.example
├── requirements.txt
└── README.md
```

## Команды


| Команда       | Описание                          |
| ------------- | --------------------------------- |
| `/start`      | Начать работу с ботом             |
| `/help`       | Справка                           |
| `/topic`      | Выбрать тему диалога              |
| `/settings`   | Настройки                         |
| `/level`      | Изменить уровень HSK              |
| `/premium`    | Информация о подписке             |
| `/invite`     | Реферальная программа             |
| `/vocabulary` | Ваш словарь                       |
| `/admin`      | Админ-панель (только для админов) |


## Подписка

### Trial (3 дня)

- Полный доступ ко всем функциям

### Free

- 20 текстовых сообщений/день
- 5 голосовых сообщений/день
- 50 слов в словаре

### Premium (₽770/мес)

- Безлимитные сообщения
- Безлимитный словарь
- Приоритетная поддержка

## API стоимость

При 1000 сообщений/день:

- Whisper STT: ~$0.50/день
- GPT-4o-mini: ~$0.15/день
- TTS: ~$0.75/день
- **Итого: ~$1.40/день ≈ $42/мес**

## Технологии

- **aiogram 3.x** — Telegram Bot Framework
- **SQLite + aiosqlite** — База данных
- **OpenAI API** — Whisper, GPT-4o-mini, TTS
- **Pydantic** — Валидация настроек

## Deployment

### Railway (Production)

Бот развернут на [Railway](https://railway.app) в webhook режиме.

**Важные файлы:**

- `railway_start.py` — запуск в webhook режиме
- `Procfile` — конфигурация Railway
- `railway.json` — настройки деплоя (replicas=1)

**Env переменные в Railway:**

```
BOT_TOKEN=...
OPENAI_API_KEY=...
ADMIN_IDS=...
TRIBUTE_API_KEY=...
TRIBUTE_PRODUCT_ID=...
TRIBUTE_PAYMENT_LINK=...
```

**Deploy:**

```bash
git push origin main  # Railway автоматически деплоит
railway logs -f       # Смотреть логи
```

### Local Development

```bash
# Polling mode (для локальной разработки)
python -m bot.main

# Webhook + Payment server (для тестирования платежей)
python start_all.py
```

## Troubleshooting

### ❌ "Conflict: terminated by other getUpdates"

**Причина:** Несколько экземпляров бота запущено одновременно (на Railway: replicas > 1)

**Решение:**

1. Railway Dashboard → Settings → Deploy → **Replicas = 1**
2. Проверьте, что используется webhook mode (`railway_start.py`)
3. Подробная инструкция: **[RAILWAY_FIX.md](./RAILWAY_FIX.md)**

**Быстрый фикс:**

```bash
python delete_webhook.py  # Удалить webhook
python check_webhook.py   # Проверить статус
```

### Полезные скрипты

- `check_webhook.py` — проверить статус webhook
- `delete_webhook.py` — удалить webhook
- `railway_start.py` — запуск в webhook режиме (для Railway)
- `start_all.py` — запуск бот + webhook сервер локально

## Документация

- **[AGENTS.md](./AGENTS.md)** — руководство по разработке, архитектура, команды
- **[RAILWAY_FIX.md](./RAILWAY_FIX.md)** — решение проблем с Railway деплоем

## Лицензия

MIT